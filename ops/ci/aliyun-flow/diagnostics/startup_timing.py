#!/usr/bin/env python3
"""Read-only log arithmetic. No JVM attach, shell commands, network, or raw log output."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

TIMESTAMP = re.compile(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+(?:[+-]\d\d:?\d\d|Z))')
STARTED = re.compile(r'Started \S+ in ([\d.]+) seconds \(process running for ([\d.]+)\)')
MARKER = re.compile(r'CYF_DEPLOY_TIMING component=(installer|lifecycle) pid=(\d+) '
                    r'point=([a-z_]+)\.(begin|end|failed) monotonic_s=(\d+(?:\.\d+)?)\b')
# Labels are fixed: never echo bean arguments, credentials, SQL, or log bodies.
EVENTS = [
    ('starting', 'Starting JiaApplication', 'first'),
    ('repositories_begin', 'Bootstrapping Spring Data', 'first'),
    ('repositories_end', 'Finished Spring Data repository scanning', 'last'),
    ('mapper_duplicates_begin', 'Skipping MapperFactoryBean', 'first'),
    ('mapper_duplicates_end', 'Skipping MapperFactoryBean', 'last'),
    ('web_context', 'Root WebApplicationContext: initialization completed', 'first'),
    ('chat_mcp_config', 'MCP tool callbacks are disabled for ChatClient', 'first'),
    ('redisson_version', 'org.redisson.Version', 'first'),
    ('redisson_connections', 'connections initialized for', 'last'),
    ('hikari_begin', 'HikariPool-1 - Starting...', 'first'),
    ('hikari_end', 'HikariPool-1 - Start completed.', 'first'),
    ('mybatis_insert', 'CmsColumnMapper.insert] Has been loaded', 'first'),
    ('camunda_isolation', 'ENGINE-12020', 'first'),
    ('camunda_created', 'ENGINE-00001', 'first'),
    ('tomcat_started', 'Tomcat started on port', 'first'),
]


def timestamp(line):
    m = TIMESTAMP.search(line)
    if not m:
        return None
    value = m.group(1).replace('Z', '+0000')
    # Java Instant may print nanoseconds; legacy datetime arithmetic is microsecond precision.
    value = re.sub(r'(\.\d{6})\d+', r'\1', value)
    value = re.sub(r'([+-]\d\d):(\d\d)$', r'\1\2', value)
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')


def seconds(delta):
    return round(delta.total_seconds(), 6)


def spring_timing(text):
    lines = text.splitlines()
    endings = [(timestamp(line), STARTED.search(line)) for line in lines if STARTED.search(line)]
    endings = [(ts, m) for ts, m in endings if ts is not None]
    if len(endings) != 1:
        return {'status': 'unknown', 'reason': 'Expected exactly one timestamped Spring Started event',
                'startedEventCount': len(endings)}
    end, match = endings[0]
    duration, process_duration = map(float, match.groups())
    begin = end - timedelta(seconds=duration)
    process_begin = end - timedelta(seconds=process_duration)
    events = {'spring_timer_origin': begin, 'spring_started': end}
    duplicate_count = 0
    gc = []
    for line in lines:
        ts = timestamp(line)
        if ts is None or not process_begin <= ts <= end:
            continue
        pause = re.search(r'\[gc\s*\]\s+GC\(\d+\) Pause .*? ([\d.]+)ms\s*$', line)
        if pause:
            gc.append((ts, float(pause.group(1)) / 1000))
        if ts < begin:
            continue
        if 'Skipping MapperFactoryBean' in line:
            duplicate_count += 1
        for label, needle, selection in EVENTS:
            if needle in line and (selection == 'last' or label not in events):
                events[label] = ts
    ordered = sorted(events.items(), key=lambda item: item[1])
    intervals = []
    for (left, start), (right, finish) in zip(ordered, ordered[1:]):
        intervals.append({'from': left, 'to': right, 'start': start.isoformat(),
                          'end': finish.isoformat(), 'seconds': seconds(finish - start),
                          'exclusiveComponentTime': False})
    # Completion-window attribution: a pause crossing the boundary is included whole.
    spring_gc = [value for ts, value in gc if begin <= ts <= end]
    return {'status': 'measured', 'springSeconds': duration, 'processAtStartedSeconds': process_duration,
            'inferredProcessOrigin': process_begin.isoformat(), 'inferredSpringOrigin': begin.isoformat(),
            'springStartedAt': end.isoformat(), 'intervals': intervals,
            'intervalSumSeconds': round(sum(item['seconds'] for item in intervals), 6),
            'mapperDuplicateWarnings': duplicate_count,
            'gc': {'processWindowPauseCount': len(gc),
                   'processWindowPauseSeconds': round(sum(value for _, value in gc), 6),
                   'springWindowPauseCount': len(spring_gc),
                   'springWindowPauseSeconds': round(sum(spring_gc), 6),
                   'scope': 'Completed pause records only, already inside elapsed time; not additive'},
            'limits': ['Intervals are adjacent milestones, not exclusive bean/SQL times',
                       'Started is not readiness or ApplicationRunner completion',
                       'Timer origins are inferred from framework-reported durations',
                       'Missing milestones change interval boundaries; compare only identical pairs']}


def deploy_timing(text):
    pending, spans, incomplete = {}, [], []
    for line_no, line in enumerate(text.splitlines(), 1):
        m = MARKER.search(line)
        if not m:
            continue
        component, pid, point, kind, value = m.groups()
        key = (component, pid, point)
        base = dict(component=component, pid=int(pid), point=point)
        now = float(value)
        if kind == 'begin':
            if key in pending:
                incomplete.append(dict(base, reason='repeated_begin', line=pending[key][1]))
            pending[key] = (now, line_no)
        elif key not in pending:
            incomplete.append(dict(base, reason='missing_begin', line=line_no))
        else:
            start, start_line = pending.pop(key)
            if kind == 'failed' or now < start:
                incomplete.append(dict(base, reason='failed' if kind == 'failed' else 'clock_regression',
                                       startLine=start_line, endLine=line_no))
            else:
                spans.append(dict(base, seconds=round(now-start, 6), startLine=start_line,
                                  endLine=line_no, startMonotonicSeconds=start, endMonotonicSeconds=now))
    for (component, pid, point), (_, line_no) in pending.items():
        incomplete.append(dict(component=component, pid=int(pid), point=point,
                               reason='missing_end', line=line_no))
    return {'status': 'measured' if spans else 'no_complete_spans', 'spans': spans,
            'incomplete': incomplete,
            'limits': ['Nested spans and spans across processes must not be summed',
                       'Missing/failed intervals are unknown, never zero',
                       'Use logs from one machine and one run; do not concatenate different hosts/runs']}


TRACE = re.compile(r'CYF_STARTUP_STEP event=(BEGIN|TAG|END) id=(\d+) parent=(\d+) '
                   r'thread=(\d+) name=([A-Za-z0-9_.$@#:/-]+) wall=(\S+) '
                   r'monotonic_ns=(-?\d+)(?: (.*))?$')


def startup_steps(text):
    """Only explicit boundaries; never substitute adjacent application log timestamps."""
    entries, errors, summaries = {}, [], []
    for number, line in enumerate(text.splitlines(), 1):
        summary = re.search(r'CYF_STARTUP_SUMMARY steps=(\d+) open=(\d+) output_ns=(\d+) output_failures=(\d+)', line)
        if summary:
            summaries.append(dict(zip(('steps', 'open', 'outputNanos', 'outputFailures'), map(int, summary.groups()))))
        match = TRACE.search(line)
        if not match:
            continue
        event, identity, parent, thread, name, wall, tick, extra = match.groups()
        identity, parent, thread, tick = map(int, (identity, parent, thread, tick))
        row = entries.setdefault(identity, {'id': identity, 'parent': parent, 'thread': thread,
                                            'name': name, 'tags': {}, 'begin': None, 'end': None})
        if (row['parent'], row['thread'], row['name']) != (parent, thread, name):
            errors.append({'line': number, 'id': identity, 'reason': 'identity_changed'})
            row['invalid'] = True
            continue
        fields = dict(re.findall(r'([A-Za-z_]+)=([A-Za-z0-9_.$@#:/-]+)', extra or ''))
        if event == 'TAG':
            if fields.get('key') in ('beanName', 'beanType', 'postProcessor', 'listener', 'mainApplicationClass', 'outcome'):
                row['tags'][fields['key']] = fields.get('value', 'omitted')
        else:
            kind = event.lower()
            if row[kind] is not None:
                row['invalid'] = True
                errors.append({'line': number, 'id': identity, 'reason': 'duplicate_' + kind})
            row[kind] = {'monotonicNanos': tick, 'wall': wall, 'line': number}
            if event == 'END':
                row['reportedDurationNanos'] = int(fields.get('duration_ns', '-1'))
                row['outcome'] = fields.get('outcome', 'ended')
    for row in entries.values():
        start, end = row['begin'], row['end']
        row['selfWallSeconds'] = None
        if not start or not end or row.get('invalid'):
            row['status'] = 'incomplete'
            row['seconds'] = None
        else:
            duration = end['monotonicNanos'] - start['monotonicNanos']
            if duration < 0 or duration != row['reportedDurationNanos']:
                row['status'], row['seconds'] = 'invalid_duration', None
                errors.append({'id': row['id'], 'reason': 'duration_mismatch'})
            else:
                row['status'], row['seconds'] = 'measured', duration / 1e9
    complete = (len(summaries) == 1 and summaries[0]['steps'] == len(entries)
                and summaries[0]['open'] == 0 and summaries[0]['outputFailures'] == 0
                and not errors and all(row['status'] == 'measured' for row in entries.values()))
    # Validate real ancestry before subtracting nested wall intervals.
    children = {}
    for row in entries.values():
        if not row['parent']:
            continue
        parent = entries.get(row['parent'])
        if parent is None:
            complete = False
            errors.append({'id': row['id'], 'reason': 'missing_parent'})
        else:
            children.setdefault(parent['id'], []).append(row)
            if parent['status'] == row['status'] == 'measured':
                a, b = row['begin']['monotonicNanos'], row['end']['monotonicNanos']
                if (row['thread'] != parent['thread'] or row['parent'] >= row['id'] or
                        a < parent['begin']['monotonicNanos'] or b > parent['end']['monotonicNanos']):
                    complete = False
                    errors.append({'id': row['id'], 'reason': 'invalid_parent_interval'})
    if complete:
        for row in entries.values():
            intervals = sorted((child['begin']['monotonicNanos'], child['end']['monotonicNanos'])
                               for child in children.get(row['id'], []))
            covered, left, right = 0, None, None
            for a, b in intervals:
                if left is None:
                    left, right = a, b
                elif a <= right:
                    right = max(right, b)
                else:
                    covered += right - left
                    left, right = a, b
            if left is not None:
                covered += right - left
            row['recordedChildrenSeconds'] = covered / 1e9
            row['selfWallSeconds'] = (row['reportedDurationNanos'] - covered) / 1e9
    return {'status': 'measured' if entries else 'no_explicit_steps', 'traceComplete': complete,
            'steps': list(entries.values()), 'errors': errors, 'summaries': summaries,
            'limits': ['Times require matching actual BEGIN and END, not neighboring log messages',
                       'Native outcome=ended means scope closed, not success',
                       'Self wall time subtracts only recorded direct children, not CPU/SQL time',
                       'No self-time attribution without a complete trace; missing ends stay unknown',
                       'Parentage is same-thread only; asynchronous roots are not falsely nested']}


LIFECYCLE = re.compile(r"(Starting bean '([^']+)' of type|Successfully started bean '([^']+)')")


def lifecycle_steps(text):
    """Spring lifecycle starts are TRACE; completions are DEBUG, unlike bean creation spans."""
    pending, spans, incomplete = {}, [], []
    for number, line in enumerate(text.splitlines(), 1):
        # Only this logger's fixed messages; no arbitrary quoted payloads are returned.
        if 'DefaultLifecycleProcessor' not in line:
            continue
        match = LIFECYCLE.search(line)
        time = timestamp(line)
        if not match or time is None:
            continue
        name = match.group(2) or match.group(3)
        if not re.fullmatch(r'[A-Za-z0-9_.$@#:/-]+', name):
            continue
        if match.group(2):
            if name in pending:
                incomplete.append({'beanName': name, 'reason': 'repeated_begin'})
            pending[name] = (time, number)
        elif name in pending:
            start, start_line = pending.pop(name)
            elapsed = seconds(time - start)
            if elapsed < 0:
                incomplete.append({'beanName': name, 'reason': 'wall_clock_regression'})
            else:
                spans.append({'beanName': name, 'start': start.isoformat(), 'end': time.isoformat(),
                              'seconds': elapsed, 'startLine': start_line, 'endLine': number,
                              'clock': 'wall; not monotonic Java spans'})
        else:
            incomplete.append({'beanName': name, 'reason': 'missing_TRACE_begin'})
    for name, (start, number) in pending.items():
        incomplete.append({'beanName': name, 'start': start.isoformat(), 'startLine': number, 'reason': 'missing_end'})
    return {'spans': spans, 'incomplete': incomplete,
            'limits': ['Lifecycle start/finish only; repeated restart cycles and child contexts require separate logs',
                       'Start returns may precede asynchronous readiness; keep actual health checks']}


def snapshot(path):
    data = Path(path).read_bytes()
    return data.decode('utf-8', errors='replace'), {
        'path': str(Path(path).resolve()), 'bytes': len(data),
        'snapshotSha256': hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spring-log')
    parser.add_argument('--deploy-log')
    parser.add_argument('--run', type=int, required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--jar-sha256', required=True)
    args = parser.parse_args()
    if not (args.spring_log or args.deploy_log):
        parser.error('provide at least one log')
    if not re.fullmatch(r'[a-f0-9]{40}', args.source_sha) or not re.fullmatch(r'[a-f0-9]{64}', args.jar_sha256):
        parser.error('source and artifact must be full hex digests')
    out = {'pipeline': 5260799, 'run': args.run, 'sourceSha': args.source_sha,
           'jarSha256': args.jar_sha256, 'binding': 'Caller-supplied identity; verify against Flow receipt separately'}
    for label, path, analyze in [('spring', args.spring_log, spring_timing), ('deploy', args.deploy_log, deploy_timing)]:
        if path:
            text, evidence = snapshot(path)
            out[label] = dict(analyze(text), evidence=evidence)
            if label == 'spring':
                out['actualStartupSteps'] = startup_steps(text)
                out['lifecycleSteps'] = lifecycle_steps(text)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
