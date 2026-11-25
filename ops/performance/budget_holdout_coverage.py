"""Offline observation of the frozen quote-request population; never authorizes calibration."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


class Invalid(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Invalid(message)


def text(v):
    return isinstance(v, str) and bool(v.strip())


def sha(v):
    return isinstance(v, str) and bool(re.fullmatch('[0-9a-f]{64}', v))


def rows_by(rows, field):
    require(isinstance(rows, list), 'expected a row list')
    result = {}
    for row in rows:
        require(isinstance(row, dict), 'invalid observation row')
        key = row[field]
        require(text(key) and key not in result, 'missing or repeated observation identity')
        result[key] = row
    return result


def rate(n, d):
    return dict(numerator=n, denominator=d, value=n/d if d else None)


MISSING = {'NOT_EXECUTED', 'NOT_ACCEPTED', 'CANCELLED', 'USAGE_INCOMPLETE', 'REFERENCE_PRICE_MISSING', 'EVIDENCE_UNAVAILABLE'}


# Public TaskQuoteBatches.Reason values only; never aggregate private free-form text as a report key.
QUOTE_REASONS = {'NO_BASELINE', 'OUT_OF_DISTRIBUTION', 'USAGE_INCOMPLETE', 'BILLING_ROUTE_MISSING', 'PRICE_MISSING'}


def available(row):
    require(text(row['recommendationId']), 'missing batch identity')
    if row['state'] == 'UNAVAILABLE':
        require(row.get('amount') is None and row.get('quoteId') is None and text(row.get('unavailableReason')), 'invalid unavailable item')
        return False
    money = row.get('amount')
    require(row['state'] == 'AVAILABLE' and text(row.get('quoteId')) and row.get('unavailableReason') is None
            and isinstance(money, dict) and money.get('currency') == 'WEN', 'invalid available item')
    v = money.get('amountMinor')
    require(isinstance(v, str) and re.fullmatch('0|[1-9][0-9]{0,18}', v) and int(v) <= 2**63-1, 'invalid WEN amount')
    return True


def assess(roster, observations, truth, roster_sha, observations_sha):
    require(all(isinstance(x,dict) for x in (roster,observations,truth)), 'invalid study artifact')
    require(roster['format']=='budget-roster-v1' and observations['format']=='budget-forecast-observations-v1'
            and truth['format']=='budget-truth-inventory-v1', 'unknown coverage format')
    require(sha(roster_sha) and sha(observations_sha) and observations['rosterSha256']==roster_sha
            and truth['observationsSha256']==observations_sha, 'unbound study stage')
    require(sha(roster['configurationSha256']) and sha(roster['referenceSha256']), 'missing frozen configuration or reference')
    requests=rows_by(roster['requests'],'intentRef'); results=rows_by(observations['results'],'intentRef'); outcomes=rows_by(truth['outcomes'],'intentRef')
    require(requests and requests.keys()==results.keys()==outcomes.keys(), 'incomplete or surplus request observation')
    items=quoted=any_quote=full_quote=missing=paired=0
    states=Counter(); reasons=Counter(); unavailable=Counter(); no_result=Counter()
    for key, req in requests.items():
        ids=req['agentIds']; require(isinstance(ids,list) and ids and all(map(text,ids)) and len(ids)==len(set(ids)) and text(req['taskId']) and text(req['taskVersion']), 'invalid request scope')
        result=results[key]; status=result['httpStatus']; data=result.get('data'); present=set()
        require(sha(result['evidenceSha256']), 'missing observation evidence pin')
        if type(status) is int and status==200:
            require(isinstance(data,dict) and data['taskId']==req['taskId'] and data['taskVersion']==req['taskVersion'], 'result scope mismatch')
            rows=rows_by(data['quotes'],'agentId'); require(set(ids)==rows.keys(), 'partial or surplus quote result')
            present={agent for agent,row in rows.items() if available(row)}
            for agent in rows.keys()-present:
                reason=rows[agent]['unavailableReason']; unavailable[reason if reason in QUOTE_REASONS else 'OTHER']+=1
            require(len({r['recommendationId'] for r in rows.values()})==1, 'mixed quote batches')
            state='FULL' if len(present)==len(ids) else 'MIXED' if present else 'UNAVAILABLE'
        else:
            require(data is None and (status is None or type(status) is int and 400<=status<=599), 'invalid failed request observation')
            state='NO_RESPONSE' if status is None else 'HTTP_ERROR'
            no_result[state]+=len(ids)
        states[state]+=1; items+=len(ids); quoted+=len(present); any_quote+=bool(present); full_quote+=len(present)==len(ids)
        facts=rows_by(outcomes[key]['candidates'],'agentId'); require(facts.keys()==set(ids), 'partial or surplus truth inventory')
        for agent, fact in facts.items():
            reason=fact['reason']; require(sha(fact['evidenceSha256']), 'missing outcome evidence pin')
            if reason=='MEASURED':
                require(sha(fact.get('wholeTaskTruthSha256')), 'missing verified whole-task reference')
                paired+=agent in present
            else:
                require(reason in MISSING and fact.get('wholeTaskTruthSha256') is None, 'ambiguous missing truth'); missing+=1; reasons[reason]+=1
    return dict(format='budget-coverage-report-v1', requests=len(requests), candidateRequests=items, requestStates=dict(states),
                anyQuoteRequestCoverage=rate(any_quote,len(requests)), fullQuoteRequestCoverage=rate(full_quote,len(requests)),
                candidateQuoteCoverage=rate(quoted,items), unavailableCandidateReasons=dict(unavailable),
                noResultCandidateReasons=dict(no_result), missingTruthRate=rate(missing,items), missingTruthReasons=dict(reasons),
                quotedWithTruth=paired, quotedWithoutTruth=quoted-paired)


def parse_json(raw):
    def unique(pairs):
        obj=dict(pairs); require(len(obj)==len(pairs),'duplicate JSON field'); return obj
    def invalid_number(_):raise Invalid('non-finite JSON number')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=invalid_number)


def load(path, pin):
    raw=path.read_bytes(); require(sha(pin) and hashlib.sha256(raw).hexdigest()==pin,'external artifact pin mismatch')
    return parse_json(raw)


def bootstrap_plan(roster):
    # Optional descriptive intervals: the collection owner fixes seed and family assignments before sending.
    plan=roster.get('bootstrap')
    if plan is None:return None
    require(isinstance(plan,dict) and type(plan.get('seed')) is int and -(2**63)<=plan['seed']<2**63,'invalid frozen bootstrap seed')
    groups=plan.get('families');tasks={r['taskId'] for r in roster['requests']}
    require(isinstance(groups,dict) and groups.keys()==tasks and all(map(text,groups.values())),'incomplete or surplus frozen families')
    return dict(seed=plan['seed'],families=groups)


def freeze_observations(roster, capture, roster_sha, capture_sha):
    """One logical intent per denominator; only responses observed by the predeclared cutoff count."""
    from urllib.parse import quote
    require(roster['format']=='budget-roster-v1' and capture['format']=='budget-transport-export-v1'
            and sha(roster_sha) and sha(capture_sha) and capture['rosterSha256']==roster_sha, 'wrong capture or roster')
    bootstrap_plan(roster)
    cutoff=roster['cutoffAtMs']; end=capture['completeThroughMs']
    require(type(cutoff) is int and cutoff>=0 and type(end) is int and end>=cutoff, 'capture does not cover cutoff')
    intents=rows_by(roster['requests'],'intentRef'); logs=rows_by(capture['intents'],'intentRef'); output=[]; bindings=set()
    require(intents and intents.keys()==logs.keys(), 'missing or surplus intent log')
    for key,req in intents.items():
        ids=req['agentIds']; attempts=logs[key]['attempts']; rid=req['requestId']; idem=req['idempotencyKeySha256']
        require(text(req['taskId']) and text(req['taskVersion']) and isinstance(ids,list) and ids and all(map(text,ids)) and len(ids)==len(set(ids)), 'invalid roster request')
        require(text(rid) and sha(idem) and isinstance(attempts,list) and attempts, 'missing sent intent evidence')
        binding=(req['taskId'],idem)  # One private payer/scope per roster, as fixed by its capture owner.
        require(binding not in bindings,'duplicate logical quote intent'); bindings.add(binding)
        success=None; status=None; last_sent=-1; last_reply=-1
        for a in attempts:
            sent=a['sentAtMs']; seen=a['receivedAtMs']
            require(type(sent) is int and 0<=sent<=end and sent>=last_sent, 'invalid send order'); last_sent=sent
            require(a['method']=='POST' and a['path']=='/agent/tasks/'+quote(req['taskId'],safe='')+'/quotes'
                    and a['requestIdHeader']==rid and a['idempotencyKeySha256']==idem, 'wrong quote operation')
            body=parse_json(a['requestBody']); require(type(body['protocolVersion']) is int and body['protocolVersion']==1 and body['requestId']==rid, 'invalid request envelope')
            agents=body['data']['agentIds'];require(body['data']['expectedTaskVersion']==req['taskVersion'] and isinstance(agents,list) and set(agents)==set(ids),'wrong quote input')
            code=a['httpStatus']
            if seen is None:
                require(code is None and a['responseBody'] is None and a['responseIdHeader'] is None, 'contradictory absent response');continue
            require(type(seen) is int and sent<=seen<=end and type(code) is int, 'invalid response observation')
            if seen>cutoff:continue
            if code!=200:
                require(400<=code<=599 and a['responseIdHeader'] in (None,rid), 'invalid error response')
                if seen>=last_reply:status=code;last_reply=seen
                continue  # Errors can originate outside the application (e.g. gateway timeout).
            env=parse_json(a['responseBody']);require(type(env['protocolVersion']) is int and env['protocolVersion']==1 and env['code']=='E0'
                        and env['requestId']==rid==a['responseIdHeader'], 'uncorrelated quote response')
            data=env['data'];require(data['taskId']==req['taskId'] and data['taskVersion']==req['taskVersion'] and type(data['observedAt']) is int and data['observedAt']>=0,'wrong quote snapshot')
            rows=rows_by(data['quotes'],'agentId');require(rows.keys()==set(ids),'partial quote response')
            for row in rows.values():available(row)
            require(len({r['recommendationId'] for r in rows.values()})==1 and (success is None or success==data),'mixed or changed quote batch');success=data
        require(attempts[0]['sentAtMs']<=cutoff,'not sent by cutoff')
        output.append(dict(intentRef=key,httpStatus=200 if success is not None else status,data=success,evidenceSha256=capture_sha))
    return dict(format='budget-forecast-observations-v1',rosterSha256=roster_sha,results=output)


def reconcile_offers(roster, observations, manifest, roster_sha, observations_sha, get_object):
    """Match Economy's private frozen offers to every priced item; no inferred replies or outcomes."""
    require(roster['format']=='budget-roster-v1' and observations['format']=='budget-forecast-observations-v1'
            and manifest['format']=='budget-offer-manifest-v1' and sha(roster_sha) and sha(observations_sha)
            and observations['rosterSha256']==roster_sha and manifest['observationsSha256']==observations_sha, 'unbound offer inputs')
    scope=manifest['scope']; require(all(text(scope[k]) for k in ('tenantId','clientId','ownerJiacn')), 'missing private scope')
    candidates=rows_by(manifest['offers'],'quoteId'); reqs=rows_by(roster['requests'],'intentRef'); seen=rows_by(observations['results'],'intentRef')
    require(reqs and reqs.keys()==seen.keys() and sha(roster['referenceSha256']), 'incomplete observation population')
    output=[]; used={}
    for key,req in reqs.items():
        ids=req['agentIds'];require(isinstance(ids,list) and ids and all(map(text,ids)) and len(set(ids))==len(ids), 'invalid roster candidates')
        reply=seen[key]; status=reply['httpStatus']; data=reply['data']; bound={}
        if type(status) is int and status==200:
            require(data['taskId']==req['taskId'] and data['taskVersion']==req['taskVersion'],'wrong observed task')
            quotes=rows_by(data['quotes'],'agentId');require(quotes.keys()==set(ids),'incomplete observed candidates')
            for agent,q in quotes.items():
                if not available(q):continue
                qid=q['quoteId']; require(qid in candidates, 'missing published offer'); pin=candidates[qid]['offerSha256'];require(sha(pin),'invalid offer pin')
                if pin not in used:used[pin]=get_object(pin)
                o=used[pin]; original=o['original'];require(original==dict(taskId=req['taskId'],ownerJiacn=scope['ownerJiacn'],scope={k:scope[k] for k in ('tenantId','clientId')})
                        and o['agentId']==agent and o['quoteId']==qid and type(o['wen']) is int and str(o['wen'])==q['amount']['amountMinor']
                        and o['referenceSha']==roster['referenceSha256'] and sha(o['groupSha']) and sha(o['featureSha']), 'offer does not match forecast')
                bound[agent]=pin
        else:require(data is None and (status is None or type(status) is int and 400<=status<=599),'invalid absent forecast')
        output.append(dict(intentRef=key,candidates=[dict(agentId=i,offerSha256=bound.get(i)) for i in ids]))
    require(len(used)==len(candidates),'unobserved offer in manifest')
    return dict(format='budget-bound-forecasts-v1',observationsSha256=observations_sha,requests=output)


def evaluation_roster(roster,observations,manifest,truth,roster_sha,observations_sha,manifest_sha,truth_sha,get_object):
    """Assemble, never price, the complete offline input for Economy. Include unquoted and unmeasured items."""
    require(sha(manifest_sha) and sha(truth_sha),'missing study pins')
    assess(roster,observations,truth,roster_sha,observations_sha)
    bound=reconcile_offers(roster,observations,manifest,roster_sha,observations_sha,get_object)
    requests=rows_by(roster['requests'],'intentRef');outcomes=rows_by(truth['outcomes'],'intentRef');rows=[]
    for request in bound['requests']:
        key=request['intentRef'];facts=rows_by(outcomes[key]['candidates'],'agentId')
        for item in request['candidates']:
            fact=facts[item['agentId']];rows.append(dict(intentRef=key,taskId=requests[key]['taskId'],**item,
                reason=fact['reason'],wholeTaskTruthSha256=fact.get('wholeTaskTruthSha256')))
    return dict(format='budget-evaluation-roster-v1',observationsSha256=observations_sha,manifestSha256=manifest_sha,
                truthSha256=truth_sha,referenceSha256=roster['referenceSha256'],rows=rows,bootstrap=bootstrap_plan(roster))


def offers_main(argv):
    parser=argparse.ArgumentParser(description='Offline private offer join; input hashes must be independently retained.')
    for name in ('roster','observations','manifest'):
        parser.add_argument(name,type=Path);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--truth',type=Path);parser.add_argument('--truth-sha256')
    parser.add_argument('--objects',type=Path,required=True);args=parser.parse_args(argv)
    try:
        r,o,m=[load(getattr(args,k),getattr(args,k+'_sha256')) for k in ('roster','observations','manifest')]
        require((args.truth is None)==(args.truth_sha256 is None),'truth and pin required together')
        get_object=lambda pin:load(args.objects/pin,pin)
        if args.truth is None:
            result=reconcile_offers(r,o,m,args.roster_sha256,args.observations_sha256,get_object);result['manifestSha256']=args.manifest_sha256
        else:
            result=evaluation_roster(r,o,m,load(args.truth,args.truth_sha256),args.roster_sha256,args.observations_sha256,args.manifest_sha256,args.truth_sha256,get_object)
    except (KeyError,ValueError,TypeError,OSError) as e:
        parser.exit(2,'invalid offer inputs: '+(str(e) if isinstance(e,Invalid) else type(e).__name__)+'\n')
    print(json.dumps(result,sort_keys=True,allow_nan=False))


def freeze_main(argv):
    parser=argparse.ArgumentParser(description='Freeze private forecast observations before opening truth. No network access.')
    for name in ('roster','capture'):
        parser.add_argument(name,type=Path);parser.add_argument('--'+name+'-sha256',required=True)
    args=parser.parse_args(argv)
    try:
        r=load(args.roster,args.roster_sha256);c=load(args.capture,args.capture_sha256)
        result=freeze_observations(r,c,args.roster_sha256,args.capture_sha256)
    except (KeyError,ValueError,TypeError,OSError) as e:
        parser.exit(2,'invalid capture inputs: '+(str(e) if isinstance(e,Invalid) else type(e).__name__)+'\n')
    print(json.dumps(result,sort_keys=True,allow_nan=False))


def main():
    if sys.argv[1:2]==['offers']:
        return offers_main(sys.argv[2:])
    if sys.argv[1:2]==['freeze']:
        return freeze_main(sys.argv[2:])
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('roster','observations','truth'):
        parser.add_argument(key,type=Path); parser.add_argument('--'+key+'-sha256',required=True)
    args=parser.parse_args(); pins=[args.roster_sha256,args.observations_sha256,args.truth_sha256]
    try:
        data=[load(path,pin) for path,pin in zip((args.roster,args.observations,args.truth),pins)]
        report=assess(*data,*pins[:2]); report.update(rosterSha256=pins[0],observationsSha256=pins[1],truthSha256=pins[2],evaluatorSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    except (KeyError,ValueError,TypeError,OSError) as e:
        parser.exit(2,'invalid coverage inputs: '+(str(e) if isinstance(e,Invalid) else type(e).__name__)+'\n')
    print(json.dumps(report,sort_keys=True,allow_nan=False))


if __name__=='__main__':
    main()
