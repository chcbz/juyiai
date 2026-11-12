#!/usr/bin/env python3
"""Start the two existing CYF Flow release pipelines in their fixed night slots.

The controller is intentionally a narrow control-plane client: it never builds,
deploys, cancels runs, or edits pipeline YAML. A backend release is authorized at
00:00, and a pending frontend release is authorized at 00:30 (Asia/Shanghai).
The exact Flow run ID is written only after a successful StartPipelineRun response
so a push-triggered run cannot consume a night-release intent.
"""
from __future__ import print_function

import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path('/home/isp/state/cyf-flow-release-schedule')
INTENTS = ROOT / 'intents'
LOCK = ROOT / 'controller.lock'
ALLOWLIST = ROOT / 'allowlist.json'
CREDENTIALS = '/root/.codex/auth.json'
FLOW_CONTROL = '/usr/local/lib/cyf-flow-release-schedule/flow-control.cjs'
ORG = '5fb7d76ee6f9d07f148529c7'
BRANCH = 'develop'
SHA = re.compile(r'^[0-9a-f]{40}$')
RUN = re.compile(r'^[1-9][0-9]*$')
TERMINAL = frozenset(('SUCCESS', 'FAIL', 'FAILED', 'CANCELED', 'CANCELLED'))
TARGETS = {
    'backend-nightly': {
        'pipeline': '5260799', 'name': 'cyf-api-release',
        'repo': 'https://github.com/chcbz/juyiai-api.git',
        'record': Path('/home/isp/state/cyf-api-flow/approval.json'),
        'record_commit': 'source_commit_sha', 'intent_kind': 'backend-nightly',
    },
    'frontend-major-nightly': {
        'pipeline': '4403172', 'name': 'cyf-web-release',
        'repo': 'https://github.com/chcbz/juyiai-web.git',
        'record': Path('/home/isp/state/cyf-web-flow/record.json'),
        'record_commit': 'commit', 'intent_kind': 'frontend-major-nightly',
    },
}


class ScheduleError(RuntimeError):
    pass


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def secure_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not path.is_dir() or info.st_uid != 0 or (info.st_mode & 0o077):
        raise ScheduleError('unsafe scheduler directory: ' + str(path))


def atomic_write(path, data, mode=0o600):
    secure_directory(path.parent)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as handle:
            fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, str(path))
        directory = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary)
        except OSError:
            pass


def command(args, accepted=(0,)):
    completed = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
    if completed.returncode not in accepted:
        detail = (completed.stderr or completed.stdout or 'command failed').strip()[-500:]
        raise ScheduleError(detail)
    return completed


def flow(operation, target, extra=(), accepted=(0,)):
    command_line = ['node', FLOW_CONTROL, operation, '--org', ORG,
                    '--pipeline', target['pipeline'], '--allowlist', str(ALLOWLIST),
                    '--credentials-file', CREDENTIALS] + list(extra)
    completed = command(command_line, accepted=accepted)
    try:
        value = json.loads(completed.stdout)
    except (TypeError, ValueError):
        raise ScheduleError('invalid Flow control response')
    if not isinstance(value, dict) or value.get('pipeline') != target['pipeline'] or value.get('org') != ORG:
        raise ScheduleError('Flow control identity mismatch')
    return value, completed.returncode


def remote_develop(repo):
    completed = command(['git', 'ls-remote', '--refs', repo, 'refs/heads/' + BRANCH])
    fields = completed.stdout.strip().split()
    if len(fields) != 2 or fields[1] != 'refs/heads/' + BRANCH or not SHA.fullmatch(fields[0]):
        raise ScheduleError('remote develop resolution was not a single full commit')
    return fields[0]


def installed_commit(target):
    path = target['record']
    try:
        info = path.lstat()
        if not path.is_file() or info.st_uid != 0 or (info.st_mode & 0o077):
            return None
        value = json.loads(path.read_text(encoding='utf-8'))
        commit = value.get(target['record_commit']) if isinstance(value, dict) else None
        return commit if isinstance(commit, str) and SHA.fullmatch(commit) else None
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def active_runs(value):
    runs = value.get('runs')
    if not isinstance(runs, list):
        raise ScheduleError('Flow run list invalid')
    if value.get('nextToken') is not None:
        raise ScheduleError('Flow run history requires pagination reconciliation')
    return [run for run in runs if isinstance(run, dict) and str(run.get('status', '')).upper() not in TERMINAL]


def wait_for_no_active_run(target):
    while True:
        value, _ = flow('list', target)
        active = active_runs(value)
        if not active:
            return value
        print(json.dumps({'status': 'waiting_for_active_run', 'pipeline': target['pipeline'],
                          'run_ids': [item.get('id') for item in active]}, sort_keys=True), flush=True)
        time.sleep(60)


def write_intent(target, run_id, commit):
    if not RUN.fullmatch(run_id) or not SHA.fullmatch(commit):
        raise ScheduleError('invalid Flow run identity for intent')
    value = {
        'schema_version': 1,
        'kind': target['intent_kind'],
        'pipeline_id': target['pipeline'],
        'run_id': run_id,
        'commit': commit,
        'issued_at': datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
    }
    path = INTENTS / (target['pipeline'] + '-' + run_id + '.json')
    atomic_write(path, canonical_json(value))
    return path


def start_once(action):
    target = TARGETS[action]
    secure_directory(ROOT)
    secure_directory(INTENTS)
    if not ALLOWLIST.is_file():
        raise ScheduleError('scheduler allowlist is missing')
    remote = remote_develop(target['repo'])
    installed = installed_commit(target)
    if installed == remote:
        print(json.dumps({'status': 'skipped_no_pending_commit', 'pipeline': target['pipeline'],
                          'commit': remote}, sort_keys=True), flush=True)
        return 0
    runs = wait_for_no_active_run(target)
    config, _ = flow('config', target)
    configuration = config.get('configuration')
    if not isinstance(configuration, dict) or configuration.get('name') != target['name']:
        raise ScheduleError('pipeline config identity mismatch')
    canonical = configuration.get('canonicalConfigSha256')
    if not isinstance(canonical, str) or not re.fullmatch(r'[0-9a-f]{64}', canonical):
        raise ScheduleError('pipeline config digest unavailable')
    existing = [str(item.get('id')) for item in runs.get('runs', []) if RUN.fullmatch(str(item.get('id', '')))]
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    context = {
        'schemaVersion': 1,
        'kind': 'cyf.flow.start-context.v1',
        'org': ORG,
        'pipeline': target['pipeline'],
        'pipelineName': target['name'],
        'canonicalConfigSha256': canonical,
        'existingRunIds': existing,
        'requestStartedAt': now,
        'params': {},
        'expectedSources': [{'repo': target['repo'], 'branch': BRANCH, 'commit': remote}],
    }
    context_path = ROOT / ('start-' + target['pipeline'] + '-' + hashlib.sha256(canonical_json(context)).hexdigest() + '.json')
    atomic_write(context_path, canonical_json(context))
    digest = hashlib.sha256(context_path.read_bytes()).hexdigest()
    result, return_code = flow('start', target, ('--context', str(context_path), '--context-sha256', digest), accepted=(0, 3))
    if return_code != 0 or result.get('state') != 'APPLIED':
        print(json.dumps({'status': 'start_unresolved', 'pipeline': target['pipeline'],
                          'flow_result': result.get('state')}, sort_keys=True), flush=True)
        return 2
    run = result.get('run')
    run_id = str(run.get('id')) if isinstance(run, dict) else ''
    if not RUN.fullmatch(run_id):
        raise ScheduleError('successful start response omitted a run id')
    intent = write_intent(target, run_id, remote)
    print(json.dumps({'status': 'scheduled', 'pipeline': target['pipeline'], 'run_id': run_id,
                      'commit': remote, 'intent': str(intent)}, sort_keys=True), flush=True)
    return 0


def main(argv):
    if len(argv) != 2 or argv[1] not in TARGETS:
        raise SystemExit('usage: cyf-flow-release-schedule {backend-nightly|frontend-major-nightly}')
    secure_directory(ROOT)
    lock_fd = os.open(str(LOCK), os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return start_once(argv[1])
    finally:
        os.close(lock_fd)


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv))
    except ScheduleError as error:
        print('cyf-flow-release-schedule: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
