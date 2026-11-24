import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from ops.performance import budget_holdout_coverage as tool


class BudgetCoverageTest(unittest.TestCase):
    def setUp(self):
        self.h='a'*64
        self.roster={'format':'budget-roster-v1','configurationSha256':self.h,'referenceSha256':self.h,'requests':[]}
        self.run={'format':'budget-forecast-observations-v1','rosterSha256':self.h,'results':[]}
        self.truth={'format':'budget-truth-inventory-v1','observationsSha256':self.h,'outcomes':[]}

    def case(self,key,amounts,reasons,status=200):
        ids=[str(i) for i in range(len(amounts))];self.roster['requests'].append(dict(intentRef=key,taskId=key,taskVersion='1',agentIds=ids))
        rows=[dict(agentId=i,state='AVAILABLE' if v is not None else 'UNAVAILABLE',quoteId='q'+i if v is not None else None,recommendationId='batch',amount=None if v is None else dict(currency='WEN',amountMinor=v),unavailableReason='NO_BASELINE' if v is None else None) for i,v in zip(ids,amounts)]
        self.run['results'].append(dict(intentRef=key,httpStatus=status,evidenceSha256=self.h,data=dict(taskId=key,taskVersion='1',quotes=rows) if status==200 else None))
        self.truth['outcomes'].append(dict(intentRef=key,candidates=[dict(agentId=i,reason=r,evidenceSha256=self.h,wholeTaskTruthSha256=self.h if r=='MEASURED' else None) for i,r in zip(ids,reasons)]))

    def score(self):return tool.assess(self.roster,self.run,self.truth,self.h,self.h)

    def test_all_requests_not_only_measured_or_available(self):
        self.case('mixed',['0',None],['NOT_EXECUTED','NOT_ACCEPTED']);self.case('full',['100'],['MEASURED']);self.case('unavailable',[None],['MEASURED']);self.case('failed',[None],['CANCELLED'],503);self.case('no-response',[None],['EVIDENCE_UNAVAILABLE'],None)
        r=self.score();self.assertEqual(2/5,r['anyQuoteRequestCoverage']['value']);self.assertEqual(1/5,r['fullQuoteRequestCoverage']['value']);self.assertEqual(2/6,r['candidateQuoteCoverage']['value']);self.assertEqual((1,1),(r['quotedWithTruth'],r['quotedWithoutTruth']));self.assertEqual(4/6,r['missingTruthRate']['value']);self.assertEqual({s:1 for s in ('FULL','MIXED','UNAVAILABLE','HTTP_ERROR','NO_RESPONSE')},r['requestStates'])

    def test_no_omission_no_replay_as_extra_intent_no_foreign_task(self):
        self.case('k',['1',None],['MEASURED','USAGE_INCOMPLETE']);a,b,c=copy.deepcopy((self.roster,self.run,self.truth))
        for alter in (lambda:self.run['results'].clear(),lambda:self.truth['outcomes'][0]['candidates'].pop(),lambda:self.run['results'].append(b['results'][0]),lambda:self.roster['requests'].append(a['requests'][0]),lambda:self.run['results'][0]['data'].update(taskId='foreign'),lambda:self.run['results'][0]['data']['quotes'][1].update(recommendationId='other'),lambda:self.truth.update(observationsSha256='b'*64)):
            self.roster,self.run,self.truth=copy.deepcopy((a,b,c));alter()
            with self.assertRaises(tool.Invalid):self.score()

    def test_no_fabricated_money_or_whole_task_truth(self):
        self.case('key',['1'],['MEASURED']);row=self.run['results'][0]['data']['quotes'][0];fact=self.truth['outcomes'][0]['candidates'][0]
        for invalid in ('-1','01',1,'1.1',str(2**63)):
            row['amount']['amountMinor']=invalid
            with self.assertRaises(tool.Invalid):self.score()
        row['amount']['amountMinor']='1';fact['reason']='USAGE_INCOMPLETE'
        with self.assertRaises(tool.Invalid):self.score()
        fact.update(reason='MEASURED',wholeTaskTruthSha256=None)
        with self.assertRaises(tool.Invalid):self.score()

    def test_cli_chain_and_no_private_identifiers(self):
        self.case('sensitive-case',['1'],['MEASURED'])
        with tempfile.TemporaryDirectory() as tmp:
            cmd=[sys.executable,tool.__file__];pins=[]
            for name,obj in [('roster',self.roster),('observations',self.run),('truth',self.truth)]:
                if pins:obj['rosterSha256' if name=='observations' else 'observationsSha256']=pins[-1]
                p=Path(tmp)/name;p.write_text(json.dumps(obj));pins.append(hashlib.sha256(p.read_bytes()).hexdigest());cmd += [str(p),'--'+name+'-sha256',pins[-1]]
            output=subprocess.check_output(cmd);self.assertNotIn(b'sensitive-case',output);self.assertEqual(pins[-1],json.loads(output)['truthSha256']);(Path(tmp)/'truth').write_text('{}');r=subprocess.run(cmd,capture_output=True);self.assertEqual(2,r.returncode);self.assertFalse(r.stdout)
    def test_bind_published_offer_not_another_scope_price_or_missing_response(self):
        self.case('observed',['65',None],['NOT_ACCEPTED','NOT_EXECUTED']);self.case('absent',[None],['EVIDENCE_UNAVAILABLE'],None)
        scope=dict(tenantId='t',clientId='c',ownerJiacn='o'); manifest=dict(format='budget-offer-manifest-v1',observationsSha256=self.h,scope=scope,offers=[dict(quoteId='q0',offerSha256=self.h)])
        offer=dict(original=dict(taskId='observed',ownerJiacn='o',scope=dict(tenantId='t',clientId='c')),agentId='0',quoteId='q0',wen=65,referenceSha=self.h,featureSha=self.h,groupSha=self.h)
        join=lambda x:tool.reconcile_offers(self.roster,self.run,manifest,self.h,self.h,lambda pin:x)
        rows=join(offer)['requests'];self.assertEqual([[self.h,None],[None]],[[c['offerSha256'] for c in r['candidates']] for r in rows]);
        evaluation=tool.evaluation_roster(self.roster,self.run,manifest,self.truth,self.h,self.h,self.h,self.h,lambda pin:offer)
        self.assertEqual([(r['taskId'],r['offerSha256'],r['reason']) for r in evaluation['rows']],
                         [('observed',self.h,'NOT_ACCEPTED'),('observed',None,'NOT_EXECUTED'),('absent',None,'EVIDENCE_UNAVAILABLE')])
        for patch in (dict(wen=66),dict(referenceSha='b'*64),dict(agentId='1'),dict(original={**offer['original'],'ownerJiacn':'other'})):
            with self.assertRaises(tool.Invalid):join(dict(offer,**patch))
        manifest['offers'].append(dict(quoteId='extra',offerSha256='b'*64))
        with self.assertRaises(tool.Invalid):join(offer)

    def wire(self):
        self.case('k',['0'],['MEASURED']);req=self.roster['requests'][0];req.update(requestId='request',idempotencyKeySha256=self.h);self.roster['cutoffAtMs']=30
        data=self.run['results'][0]['data'];data['observedAt']=15
        a=dict(method='POST',path='/agent/tasks/k/quotes',sentAtMs=10,receivedAtMs=20,idempotencyKeySha256=self.h,requestIdHeader='request',responseIdHeader='request',httpStatus=200,
               requestBody=json.dumps(dict(protocolVersion=1,requestId='request',data=dict(expectedTaskVersion='1',agentIds=['0']))),
               responseBody=json.dumps(dict(protocolVersion=1,requestId='request',code='E0',msg='ok',data=data)))
        log=dict(format='budget-transport-export-v1',rosterSha256=self.h,completeThroughMs=100,intents=[dict(intentRef='k',attempts=[a])]);return a,log

    def test_bootstrap_uses_predeclared_whole_task_families_and_signed_long_seed(self):
        _,log=self.wire();freeze=lambda:tool.freeze_observations(self.roster,log,self.h,self.h)
        self.assertIsNone(tool.bootstrap_plan(self.roster));self.roster['bootstrap']={'seed':-3,'families':{'k':'family'}};freeze()
        for bad in ({'seed':True,'families':{'k':'family'}},{'seed':2**63,'families':{'k':'family'}},
                    {'seed':3,'families':{}},{'seed':3,'families':{'k':'family','extra':'family'}},{'seed':3,'families':{'k':' '}}):
            self.roster['bootstrap']=bad
            with self.assertRaises(tool.Invalid):freeze()

    def test_freeze_uses_observed_responses_not_late_success_or_last_retry(self):
        a,log=self.wire();attempts=log['intents'][0]['attempts'];score=lambda:tool.freeze_observations(self.roster,log,self.h,self.h)['results'][0]
        retry=dict(a,sentAtMs=22,receivedAtMs=23,httpStatus=503,responseIdHeader=None,responseBody='gateway error');attempts.append(retry)
        self.assertEqual('0',score()['data']['quotes'][0]['amount']['amountMinor']);a['receivedAtMs']=35;self.assertEqual(503,score()['httpStatus']);self.assertIsNone(score()['data']);retry['receivedAtMs']=36;self.assertIsNone(score()['httpStatus']);self.assertIsNone(score()['data'])

    def test_freeze_refuses_cross_intent_replay_or_changed_winner(self):
        a,log=self.wire();base=copy.deepcopy(a);attempts=log['intents'][0]['attempts'];attempts.append(a.copy())
        for change in (dict(method='GET'),dict(path='/agent/tasks/foreign/quotes'),dict(idempotencyKeySha256='b'*64),dict(responseIdHeader='other'),dict(responseBody=base['responseBody'].replace('"amountMinor": "0"','"amountMinor": "1"')),dict(requestBody=base['requestBody'].replace('"1"','"9"'))):
            attempts[-1]={**base,**change}
            with self.assertRaises(tool.Invalid):tool.freeze_observations(self.roster,log,self.h,self.h)
        attempts[-1]=base;self.roster['requests'].append(dict(self.roster['requests'][0],intentRef='alias'));log['intents'].append(dict(log['intents'][0],intentRef='alias'))
        with self.assertRaisesRegex(tool.Invalid,'duplicate logical'):tool.freeze_observations(self.roster,log,self.h,self.h)

    def test_freeze_cli_requires_complete_capture_before_opening_truth(self):
        _,log=self.wire()
        with tempfile.TemporaryDirectory() as td:
            r,c=(Path(td)/k for k in ('r','c'));r.write_text(json.dumps(self.roster));pin=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();log['rosterSha256']=pin(r)
            def run():
                c.write_text(json.dumps(log));return subprocess.run([sys.executable,tool.__file__,'freeze',str(r),str(c),'--roster-sha256',pin(r),'--capture-sha256',pin(c)],capture_output=True)
            result=run();self.assertEqual(0,result.returncode);out=json.loads(result.stdout);self.assertEqual(pin(c),out['results'][0]['evidenceSha256']);self.assertNotIn(b'idempotencyKey',result.stdout)
            self.truth['observationsSha256']=hashlib.sha256(result.stdout).hexdigest();report=tool.assess(self.roster,out,self.truth,pin(r),self.truth['observationsSha256']);self.assertEqual(1,report['quotedWithTruth'])
            log['completeThroughMs']=29;fail=run();self.assertEqual(2,fail.returncode);self.assertFalse(fail.stdout)
