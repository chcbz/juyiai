"""Offline observation of the frozen quote-request population; never authorizes calibration."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


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
    states=Counter(); reasons=Counter()
    for key, req in requests.items():
        ids=req['agentIds']; require(isinstance(ids,list) and ids and all(map(text,ids)) and len(ids)==len(set(ids)) and text(req['taskId']) and text(req['taskVersion']), 'invalid request scope')
        result=results[key]; status=result['httpStatus']; data=result.get('data'); present=set()
        require(sha(result['evidenceSha256']), 'missing observation evidence pin')
        if type(status) is int and status==200:
            require(isinstance(data,dict) and data['taskId']==req['taskId'] and data['taskVersion']==req['taskVersion'], 'result scope mismatch')
            rows=rows_by(data['quotes'],'agentId'); require(set(ids)==rows.keys(), 'partial or surplus quote result')
            present={agent for agent,row in rows.items() if available(row)}
            require(len({r['recommendationId'] for r in rows.values()})==1, 'mixed quote batches')
            state='FULL' if len(present)==len(ids) else 'MIXED' if present else 'UNAVAILABLE'
        else:
            require(data is None and (status is None or type(status) is int and 400<=status<=599), 'invalid failed request observation')
            state='NO_RESPONSE' if status is None else 'HTTP_ERROR'
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
                candidateQuoteCoverage=rate(quoted,items), missingTruthRate=rate(missing,items), missingTruthReasons=dict(reasons),
                quotedWithTruth=paired, quotedWithoutTruth=quoted-paired)


def load(path, pin):
    def unique(pairs):
        obj=dict(pairs); require(len(obj)==len(pairs),'duplicate JSON field'); return obj
    raw=path.read_bytes(); require(sha(pin) and hashlib.sha256(raw).hexdigest()==pin,'external artifact pin mismatch')
    return json.loads(raw,object_pairs_hook=unique)


def main():
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
