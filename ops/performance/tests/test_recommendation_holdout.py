import copy
import json
import subprocess
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from ops.performance import recommendation_holdout as evaluator


class HoldoutTest(unittest.TestCase):
    def setUp(self):
        self.labels={'format':'recommendation-labels-v1','cases':[]}
        self.run={'format':'recommendation-run-v1','configurationSha256':'f'*64,'rankingVersion':'rrf-v1','labelsSha256':'0'*64,'results':[]}

    def case(self,key,judgements,levels,mode,state,family=None):
        agents=['a'+str(i) for i in range(len(levels))]
        self.labels['cases'].append(dict(caseId=key,taskId=key,taskVersion='2',familyId=family or key,
            partition='HOLDOUT',caseTags=[],factsSha256='a'*64,candidates=dict(zip(agents,judgements))))
        self.run['results'].append(dict(caseId=key,factsSha256='a'*64,data=dict(taskId=key,taskVersion='2',rankingVersion='rrf-v1',state=state,
            retrievalMode=mode,degradedReasons=(["QUERY_VECTOR_UNAVAILABLE"] if state=="DEGRADED" else []),candidateSetComplete=True,recommendations=[dict(agent=dict(agentId=p),recommendationLevel=l,evidence=[] if l=='UNKNOWN' else [dict(id="ability:1",kind="DECLARED_ABILITY",label="fixture",description="fixture only",available=True)]) for p,l in zip(agents,levels)])))

    def score(self):return evaluator.evaluate(self.labels,self.run,'0'*64)

    def test_real_order_hit_at_three_not_recall_or_precision(self):
        self.case('t1',['NOT_ACCEPTABLE']*3+['ACCEPTABLE'],['HIGH','UNKNOWN','UNKNOWN','UNKNOWN'],'HYBRID','READY')
        self.case('t2',['ACCEPTABLE','ACCEPTABLE'],['HIGH','HIGH'],'LEXICAL_ONLY','DEGRADED')
        self.case('t3',['NOT_ACCEPTABLE'],['MEDIUM'],'HYBRID','READY')
        self.case('t4',['INSUFFICIENT'],['UNKNOWN'],'UNAVAILABLE','DEGRADED')
        self.case('t5',[],[],'NOT_NEEDED','NO_CANDIDATES')
        self.labels['cases'][1]['caseTags']=['PARAPHRASE','MULTI_ATTACHMENT']
        report=self.score(); overall=report['overall']
        self.assertEqual(1,report['holdoutTagCounts']['PARAPHRASE']);self.assertIn('PARTIAL_CAPABILITY',report['missingHoldoutTags'])
        self.assertEqual(2/3,overall['highPrecision']['value']);self.assertEqual(1/2,overall['hitAt3']['value'])
        self.assertEqual(1,overall['noMatchFalsePositive']['denominator']);self.assertEqual(1,overall['noMatchFalsePositive']['value'])
        self.assertEqual(2/5,overall['degradedTaskRate']['value']);self.assertEqual(4/8,overall['unknownCandidateRate']['value'])
        self.assertEqual(3/5,overall['recommendedTaskRate']['value']);self.assertEqual(1,overall['insufficientTasks'])
        self.assertIsNone(report['byRetrievalMode']['NOT_NEEDED']['highPrecision']['ci95'])

    def test_hit_at_three_separates_rosters_that_cannot_miss(self):
        self.case('empty',[],[],'NOT_NEEDED','NO_CANDIDATES')
        self.case('three',['NOT_ACCEPTABLE']*2+['ACCEPTABLE'],['UNKNOWN']*3,'HYBRID','NO_MATCH')
        self.case('four',['NOT_ACCEPTABLE']*3+['ACCEPTABLE'],['UNKNOWN']*4,'HYBRID','NO_MATCH')
        self.case('none',['NOT_ACCEPTABLE']*4,['UNKNOWN']*4,'HYBRID','NO_MATCH')
        report=self.score(); groups=report['byRosterSize']
        self.assertEqual(.5,report['overall']['hitAt3']['value'])
        for key,tasks,den,value in [('EMPTY',1,0,None),('ONE_TO_THREE',1,1,1),('FOUR_OR_MORE',2,1,0)]:
            self.assertEqual(tasks,groups[key]['tasks'])
            self.assertEqual(den,groups[key]['hitAt3']['denominator'])
            self.assertEqual(value,groups[key]['hitAt3']['value'])

    def test_no_high_is_not_success_and_insufficient_high_is_not_credited(self):
        self.case('t',['ACCEPTABLE'],['UNKNOWN'],'HYBRID','NO_MATCH');self.assertIsNone(self.score()['overall']['highPrecision']['value'])
        self.case('x',['INSUFFICIENT'],['HIGH'],'HYBRID','READY');self.assertEqual(0,self.score()['overall']['highPrecision']['value'])

    def test_one_template_cannot_narrow_interval_as_100_independent_observations(self):
        for i in range(100):self.case(str(i),['ACCEPTABLE'],['HIGH'],'HYBRID','READY','shared')
        shared=self.score()['overall']['highPrecision']['ci95']
        for c in self.labels['cases']:c['familyId']=c['caseId']
        self.assertLess(shared[0],self.score()['overall']['highPrecision']['ci95'][0])

    def test_family_support_follows_each_denominator_not_task_count(self):
        self.case('many',['ACCEPTABLE']*3,['HIGH']*3,'HYBRID','READY','A')
        self.case('one',['ACCEPTABLE'],['HIGH'],'HYBRID','READY','B')
        self.case('none',['ACCEPTABLE'],['UNKNOWN'],'HYBRID','NO_MATCH','C')
        rates=self.score()['overall']
        for metric, count, share in [('highPrecision',2,.75),('hitAt3',3,1/3),('mediumPrecision',0,None)]:
            self.assertEqual(count,rates[metric]['contributingFamilies'])
            self.assertEqual(share,rates[metric]['largestFamilyDenominatorShare'])

    def test_partial_and_conditional_rank_hits_do_not_hide_wrong_positive_ratings(self):
        self.case('partial',['INSUFFICIENT','ACCEPTABLE'],['MEDIUM','UNKNOWN'],'HYBRID','READY')
        self.labels['cases'][-1]['caseTags']=['NEGATED_OR_CONDITIONAL','PARTIAL_CAPABILITY']
        self.case('match',['ACCEPTABLE'],['HIGH'],'HYBRID','READY')
        report=self.score(); overall=report['overall']; partial=report['byCaseTag']['PARTIAL_CAPABILITY']
        self.assertEqual(1,overall['hitAt3']['value']);self.assertEqual(.5,overall['suitableRatedTaskCoverage']['value'])
        self.assertEqual(1,overall['highPrecision']['value']);self.assertEqual(.5,overall['positivePrecision']['value'])
        self.assertEqual(0,partial['mediumPrecision']['value']);self.assertEqual(0,partial['suitableRatedTaskCoverage']['value'])
        self.assertEqual(partial,report['byCaseTag']['NEGATED_OR_CONDITIONAL']);self.assertEqual(2,overall['tasks'])
        self.assertIsNone(report['byCaseTag']['PARAPHRASE']['positivePrecision']['value'])

    def test_no_match_is_not_conditioned_away_and_empty_roster_is_separate(self):
        self.case('ready',['ACCEPTABLE'],['HIGH'],'HYBRID','READY')
        self.case('miss',['ACCEPTABLE'],['UNKNOWN'],'HYBRID','NO_MATCH')
        self.case('empty',[],[],'NOT_NEEDED','NO_CANDIDATES')
        states=self.score()['byResponseState']
        self.assertEqual({'READY','NO_MATCH','NO_CANDIDATES'},set(states))
        self.assertEqual(0,states['NO_MATCH']['suitableRatedTaskCoverage']['value'])
        self.assertEqual(1,states['NO_MATCH']['hitAt3']['value'])
        self.assertIsNone(states['NO_CANDIDATES']['hitAt3']['value'])
        self.assertEqual(.5,self.score()['overall']['suitableRatedTaskCoverage']['value'])

    def test_cannot_score_a_response_that_hides_or_invents_degradation(self):
        self.case('degraded',['ACCEPTABLE'],['MEDIUM'],'LEXICAL_ONLY','DEGRADED')
        row=self.run['results'][0]['data']
        for wrong in (None,[],['  '],'failed'):
            row['degradedReasons']=wrong
            with self.assertRaisesRegex(evaluator.Invalid,'disclosure'):self.score()
        row.update(state='READY',retrievalMode='HYBRID',degradedReasons=['QUERY_VECTOR_UNAVAILABLE'])
        with self.assertRaisesRegex(evaluator.Invalid,'disclosure'):self.score()

    def test_empty_authorized_evidence_retains_candidates_in_holdout(self):
        self.case('manual',['ACCEPTABLE'],['UNKNOWN'],'NOT_NEEDED','NO_MATCH')
        row=self.run['results'][0]['data']['recommendations'][0];row['evidence']=[]
        self.assertEqual(1,self.score()['byResponseState']['NO_MATCH']['candidates'])
        self.assertEqual(0,self.score()['overall']['suitableRatedTaskCoverage']['value'])
        row['evidence']=['spurious']
        with self.assertRaises(evaluator.Invalid):self.score()

    def test_ratings_require_disclosed_evidence_before_scoring(self):
        self.case('t',['ACCEPTABLE'],['HIGH'],'HYBRID','READY')
        result=self.run['results'][0]['data']; row=result['recommendations'][0]
        citation=row['evidence'][0]
        for level in ('HIGH','MEDIUM','LOW','UNKNOWN'):
            row['recommendationLevel']=level
            result['state']='READY' if level in ('HIGH','MEDIUM') else 'NO_MATCH'
            invalid = [None, {}, [None], [dict(citation, available=1)], [dict(citation, available=False)]]
            invalid.extend([{**citation, k: ' '}] for k in ('id', 'kind', 'label', 'description'))
            for evidence in invalid:
                with self.subTest(level=level,evidence=evidence):
                    row['evidence']=evidence
                    with self.assertRaisesRegex(evaluator.Invalid,'evidence'):self.score()
            row['evidence']=[]
            if level=='UNKNOWN':self.score()
            else:
                with self.assertRaisesRegex(evaluator.Invalid,'evidence'):self.score()
            row['evidence']=[dict(citation,additionalField='ignored')]
            self.score()

    def test_split_contamination_rejected(self):
        self.case('a',[],[],'NOT_NEEDED','NO_CANDIDATES','family');self.case('b',[],[],'NOT_NEEDED','NO_CANDIDATES','family')
        self.labels['cases'][0]['partition']='CALIBRATION'
        with self.assertRaisesRegex(evaluator.Invalid,'partition'):self.score()

    def test_no_partial_duplicate_changed_scope_or_mixed_rank_generation(self):
        self.case('x',['ACCEPTABLE','NOT_ACCEPTABLE'],['MEDIUM','UNKNOWN'],'HYBRID','READY');original=copy.deepcopy(self.run)
        for edit in (lambda r:r['results'].clear(),lambda r:r['results'].extend(r['results'][:]),lambda r:r['results'][0].update(factsSha256='b'*64),
            lambda r:r['results'][0]['data'].update(rankingVersion='other'),lambda r:r['results'][0]['data'].update(candidateSetComplete=False),
            lambda r:r['results'][0]['data']['recommendations'][1]['agent'].update(agentId='a0'),lambda r:r['results'][0]['data'].update(retrievalMode='UNAVAILABLE')):
            self.run=copy.deepcopy(original);edit(self.run)
            with self.assertRaises(evaluator.Invalid):self.score()

    def test_cli_binds_inputs_script_and_hides_identifiers(self):
        self.case('sensitive-id',['NOT_ACCEPTABLE'],['UNKNOWN'],'HYBRID','NO_MATCH')
        with tempfile.TemporaryDirectory() as d:
            l,r=Path(d)/'labels',Path(d)/'run';l.write_text(json.dumps(self.labels));pin=sha256(l.read_bytes()).hexdigest()
            self.run['labelsSha256']=pin;r.write_text(json.dumps(self.run));cmd=[sys.executable,evaluator.__file__,str(l),str(r),'--expected-labels-sha256',pin,'--expected-ranking-version','rrf-v1','--expected-configuration-sha256','f'*64]
            output=subprocess.check_output(cmd);self.assertNotIn(b'sensitive-id',output);self.assertEqual(sha256(r.read_bytes()).hexdigest(),json.loads(output)['runSha256'])
            self.assertNotEqual(0,subprocess.run(cmd[:-1]+['b'*64],capture_output=True).returncode)
            # Even an unscored UNKNOWN row must not make a visibly invalid response scoreable.
            row=self.run['results'][0]['data']['recommendations'][0]
            row['evidence']=[dict(label='private-evidence-marker', available=False)]
            r.write_text(json.dumps(self.run)); rejected=subprocess.run(cmd,capture_output=True)
            self.assertEqual(2,rejected.returncode);self.assertFalse(rejected.stdout)
            self.assertNotIn(b'private-evidence-marker',rejected.stderr);row['evidence']=[]
            # A consistent run from a different policy must not be scored against this pin.
            self.run['rankingVersion']=self.run['results'][0]['data']['rankingVersion']='wrong-policy'
            r.write_text(json.dumps(self.run));rejected=subprocess.run(cmd,capture_output=True)
            self.assertEqual(2,rejected.returncode);self.assertFalse(rejected.stdout);self.assertIn(b'frozen candidate',rejected.stderr)
            l.write_text('{"x":1,"x":1}');self.assertNotEqual(0,subprocess.run(cmd,capture_output=True).returncode)

    def test_blind_cli_roundtrip_to_original_score(self):
        self.case('private-task',['ACCEPTABLE','INSUFFICIENT'],['HIGH','UNKNOWN'],'HYBRID','READY')
        c=self.labels['cases'][0]; facts=dict(format='recommendation-blind-facts-v1',cases=[dict(c,taskText='复核预算',candidates={'a1':[],'a0':['有完整预算复核能力']})]);
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'facts';ans=root/'returned';src.write_text(json.dumps(facts));pin=lambda p:sha256(p.read_bytes()).hexdigest()
            cmd=[sys.executable,evaluator.__file__,'blind',str(src),'--expected-facts-sha256',pin(src)];sheet=json.loads(subprocess.check_output(cmd))
            raw=json.dumps(sheet);self.assertFalse(any(k in raw for k in ('private-task','familyId','partition','a0"','a1"','rankingVersion','recommendationLevel')))
            for row in sheet['cases'][0]['candidates']:
                self.assertIsNone(row['judgement']);row['judgement']='ACCEPTABLE' if row['capabilityFacts'] else 'INSUFFICIENT'
            ans.write_text(json.dumps(sheet));imported=json.loads(subprocess.check_output(cmd+['--filled',str(ans),'--expected-filled-sha256',pin(ans)]));self.assertEqual(self.labels,imported)
            self.assertEqual(1,evaluator.evaluate(imported,self.run,'0'*64)['overall']['highPrecision']['numerator'])
            for changed in ('decision','text','missing','pin'):
                invalid=copy.deepcopy(sheet);row=invalid['cases'][0]['candidates'][0]
                if changed=='decision':row['judgement']=None
                if changed=='text':row['capabilityFacts']=['private-replacement']
                if changed=='missing':invalid['cases'][0]['candidates'].pop()
                if changed=='pin':invalid['sourceSha256']='0'*64
                ans.write_text(json.dumps(invalid));res=subprocess.run(cmd+['--filled',str(ans),'--expected-filled-sha256',pin(ans)],capture_output=True);self.assertEqual(2,res.returncode);self.assertFalse(res.stdout);self.assertNotIn(b'private-replacement',res.stderr)

    def test_blind_projection_does_not_inherit_rank_order_or_result_fields(self):
        self.case('first',[],[],'NOT_NEEDED','NO_CANDIDATES');self.case('second',[],[],'NOT_NEEDED','NO_CANDIDATES');cases=[dict(c,taskText='task',candidates={f'a{i}':[f'fact {i}'] for i in range(8)}) for c in self.labels['cases']];cases[0]['candidates']={}
        source=dict(format='recommendation-blind-facts-v1',cases=cases);sheet=evaluator.blind_material(source,'0'*64);cases.reverse();cases[0]['candidates']=dict(reversed(list(cases[0]['candidates'].items())));self.assertEqual(sheet,evaluator.blind_material(source,'0'*64))
        cases[0]['recommendations']=[]
        with self.assertRaises(evaluator.Invalid):evaluator.blind_material(source,'0'*64)
