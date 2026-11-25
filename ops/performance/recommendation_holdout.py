"""Score pinned, independently labelled recommendation responses; no network or model calls."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import re


CASE_TAGS = ('SHORT_DESCRIPTION','MULTI_ATTACHMENT','NEGATED_OR_CONDITIONAL','PARAPHRASE','PARTIAL_CAPABILITY')


class Invalid(ValueError):
    pass


def require(value, message):
    if not value:
        raise Invalid(message)


def token(value):
    return isinstance(value, str) and bool(value.strip())


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)


def unique_keys(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON field')
        out[key] = value
    return out


def read(path):
    raw = path.read_bytes()
    return json.loads(raw, object_pairs_hook=unique_keys), sha256(raw).hexdigest()


class Rate:
    def __init__(self):
        self.success = self.total = 0
        self.family_weights = Counter()

    def add(self, family, successes, total):
        self.success += successes
        self.total += total
        self.family_weights[family] += total

    def report(self):
        rate = interval = None
        if self.total:
            rate = self.success / self.total
            # Conditional on evaluation denominators. Permit arbitrary within-family dependence.
            radius = math.sqrt(math.log(40) * sum(w*w for w in self.family_weights.values()) / 2) / self.total
            interval = [max(0., rate-radius), min(1., rate+radius)]
        # Count only families that contributed to this metric's denominator; expose no family IDs.
        return dict(numerator=self.success, denominator=self.total, value=rate, ci95=interval,
                    contributingFamilies=sum(n > 0 for n in self.family_weights.values()),
                    largestFamilyDenominatorShare=max(self.family_weights.values())/self.total if self.total else None)


class Group:
    def __init__(self):
        self.cases = self.candidates = self.insufficient = 0
        self.rates = {k: Rate() for k in ('highPrecision','mediumPrecision','positivePrecision','suitableRatedTaskCoverage','hitAt3','noMatchFalsePositive',
                                           'unknownCandidateRate','recommendedTaskRate','degradedTaskRate')}

    def add(self, family, labels, rows, mode):
        self.cases += 1
        self.candidates += len(rows)
        insufficient = 'INSUFFICIENT' in labels.values()
        self.insufficient += insufficient
        high = [person for person, level in rows if level == 'HIGH']
        acceptable = {person for person, label in labels.items() if label == 'ACCEPTABLE'}
        medium = [person for person, level in rows if level == 'MEDIUM']
        positive = high + medium
        correct = sum(p in acceptable for p in positive)
        recommended = bool(positive)
        def add(key, num, den):
            self.rates[key].add(family, num, den)
        add('highPrecision', sum(p in acceptable for p in high), len(high))
        add('mediumPrecision', sum(p in acceptable for p in medium), len(medium))
        add('positivePrecision', correct, len(positive))
        if acceptable:
            add('suitableRatedTaskCoverage', correct > 0, 1)
            add('hitAt3', any(p in acceptable for p, _ in rows[:3]), 1)
        elif not insufficient and rows:  # No candidates is reported separately, not a trivially correct rejection.
            add('noMatchFalsePositive', recommended, 1)
        add('unknownCandidateRate', sum(level == 'UNKNOWN' for _, level in rows), len(rows))
        add('recommendedTaskRate', recommended, 1)
        add('degradedTaskRate', mode in ('LEXICAL_ONLY','UNAVAILABLE'), 1)

    def report(self):
        return dict(tasks=self.cases, candidates=self.candidates, insufficientTasks=self.insufficient,
                    **{k:r.report() for k,r in self.rates.items()})


def evaluate(labels, run, labels_sha):
    require(labels['format'] == 'recommendation-labels-v1' and run['format'] == 'recommendation-run-v1', 'unknown format')
    require(run['labelsSha256'] == labels_sha and digest(labels_sha), 'label manifest digest mismatch')
    require(digest(run['configurationSha256']) and token(run['rankingVersion']), 'unbound ranking configuration')
    cases = {}; tasks = set(); partitions = {}
    for c in labels['cases']:
        key, family, part = c['caseId'], c['familyId'], c['partition']
        require(token(key) and token(family) and token(c['taskId']) and token(c['taskVersion']) and digest(c['factsSha256']), 'unbound case')
        require(key not in cases and c['taskId'] not in tasks, 'duplicate case or task')
        require(part in ('CALIBRATION','HOLDOUT') and partitions.setdefault(family,part) == part, 'family crosses partitions')
        tags = c['caseTags']
        require(isinstance(tags,list) and all(t in CASE_TAGS for t in tags) and len(set(tags))==len(tags), 'unrecognized or duplicate case tag')
        judgements = c['candidates']
        require(isinstance(judgements,dict) and all(token(k) and v in ('ACCEPTABLE','NOT_ACCEPTABLE','INSUFFICIENT') for k,v in judgements.items()), 'invalid candidate judgements')
        cases[key] = c; tasks.add(c['taskId'])
    holdout = {k for k,c in cases.items() if c['partition']=='HOLDOUT'}
    require(holdout, 'no holdout')
    total, groups, states, seen = Group(), defaultdict(Group), defaultdict(Group), set()
    tags = {tag:Group() for tag in CASE_TAGS}
    roster_sizes = {name:Group() for name in ('EMPTY','ONE_TO_THREE','FOUR_OR_MORE')}
    for entry in run['results']:
        key = entry['caseId']; require(key in holdout and key not in seen, 'unexpected or duplicate result'); seen.add(key)
        c, result = cases[key], entry['data']
        require(entry['factsSha256']==c['factsSha256'] and result['taskId']==c['taskId'] and result['taskVersion']==c['taskVersion'] and result['rankingVersion']==run['rankingVersion'], 'result identity mismatch')
        require(result['candidateSetComplete'] is True and isinstance(result['recommendations'],list), 'incomplete candidate set')
        rows = [(r['agent']['agentId'],r['recommendationLevel']) for r in result['recommendations']]
        require(len(rows)==len(c['candidates']) and {p for p,_ in rows}==set(c['candidates']), 'candidate set mismatch')
        require(all(level in ('HIGH','MEDIUM','LOW','UNKNOWN') for _,level in rows), 'unknown recommendation level')
        # Score only ratings the user can actually see. This checks disclosure, not
        # whether the cited capability is true or covers the task (blind labels decide that).
        for row in result['recommendations']:
            evidence = row.get('evidence')
            require(isinstance(evidence, list) and (evidence or row['recommendationLevel'] == 'UNKNOWN'),
                    'missing recommendation evidence')
            require(all(isinstance(e, dict) and e.get('available') is True
                        and all(token(e.get(k)) for k in ('id', 'kind', 'label', 'description')) for e in evidence),
                    'invalid recommendation evidence')
        mode = result['retrievalMode']; positive = any(level in ('HIGH','MEDIUM') for _,level in rows)
        expected = {'NOT_NEEDED':'NO_MATCH' if rows else 'NO_CANDIDATES','HYBRID':'READY' if positive else 'NO_MATCH',
                    'UNAVAILABLE':'DEGRADED','LEXICAL_ONLY':'DEGRADED'}
        require(mode in expected and (rows or mode=='NOT_NEEDED') and result['state']==expected[mode], 'inconsistent retrieval state')
        require(mode!='NOT_NEEDED' or all(r['recommendationLevel']=='UNKNOWN' and r.get('evidence')==[] for r in result['recommendations']), 'retrieval skipped with rated or cited evidence')
        require(mode!='UNAVAILABLE' or all(level=='UNKNOWN' for _,level in rows), 'unavailable retrieval cannot rate candidates')
        reasons = result.get('degradedReasons')
        require(isinstance(reasons,list) and all(token(r) for r in reasons)
                and bool(reasons)==(result['state']=='DEGRADED'), 'inconsistent degradation disclosure')
        size = 'EMPTY' if not rows else 'ONE_TO_THREE' if len(rows) <= 3 else 'FOUR_OR_MORE'
        for group in (total,roster_sizes[size],groups[mode],states[result['state']],*(tags[tag] for tag in c['caseTags'])):
            group.add(c['familyId'], c['candidates'], rows, mode)
    require(seen == holdout, 'missing holdout result; do not score a partial run')
    strata = {t:sum(t in cases[k]['caseTags'] for k in holdout) for t in CASE_TAGS}
    return dict(holdoutTagCounts=strata, missingHoldoutTags=[t for t,n in strata.items() if not n],
                format='recommendation-evaluation-v1', labelsSha256=labels_sha,
                configurationSha256=run['configurationSha256'],rankingVersion=run['rankingVersion'],
                ciMethod='two-sided Hoeffding; independent families, conditional fixed weights; marginal 95%',
                byRosterSize={k:g.report() for k,g in roster_sizes.items()},
                overall=total.report(), byResponseState={s:g.report() for s,g in sorted(states.items())}, byCaseTag={tag:g.report() for tag,g in tags.items()}, byRetrievalMode={m:g.report() for m,g in sorted(groups.items())})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('labels',type=Path); parser.add_argument('run',type=Path)
    parser.add_argument('--expected-labels-sha256',required=True)
    parser.add_argument('--expected-configuration-sha256',required=True)
    parser.add_argument('--expected-ranking-version',required=True)
    args = parser.parse_args()
    try:
        labels, pin = read(args.labels); run, run_sha = read(args.run)
        require(pin == args.expected_labels_sha256 and run['configurationSha256'] == args.expected_configuration_sha256, 'external pin mismatch')
        require(run['rankingVersion'] == args.expected_ranking_version, 'ranking version differs from frozen candidate')
        report = evaluate(labels,run,pin)
    except (KeyError, TypeError, ValueError, OSError) as error:
        parser.exit(2, 'invalid evaluation inputs: '+ (str(error) if isinstance(error,Invalid) else type(error).__name__)+'\n')
    report.update(runSha256=run_sha, evaluatorSha256=sha256(Path(__file__).read_bytes()).hexdigest())
    print(json.dumps(report,allow_nan=False,sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
