#!/usr/bin/env python3
"""One-shot, read-only notifier for selected Alibaba Flow runs.

This program deliberately has no scheduler, deployment, or process-control path.
Its state is a small notification/observation cache, not a task ledger.
"""
from __future__ import print_function

import errno
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile

FLOW_ORG = '5fb7d76ee6f9d07f148529c7'
EXPECTED_REPOS = {
    '5260799': 'https://github.com/chcbz/juyiai-api.git',
    '5263690': 'https://github.com/chcbz/juyiai-api.git',
    '4403172': 'https://github.com/chcbz/juyiai-web.git',
    '5263692': 'https://github.com/chcbz/juyiai-web.git',
}
ALLOWED_PIPELINES = frozenset(EXPECTED_REPOS)
FLOW_COMMAND = '/root/.codex/skills/aliyun-pipeline/scripts/flow.cjs'
CREDENTIALS_FILE = '/root/.codex/auth.json'
MAIL_COMMAND = '/root/.local/bin/cyf-task-email'
FLOW_TIMEOUT_SECONDS = 30
MAIL_TIMEOUT_SECONDS = 30
EXIT_OK = 0
EXIT_MAIN_CONTROLLER_REQUIRED = 2
TASK_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')
SHA_RE = re.compile(r'^[0-9a-fA-F]{40}$')
NUMERIC_RE = re.compile(r'^[0-9]+$')
TERMINAL = frozenset(('FAIL', 'CANCELED', 'SUCCESS'))
APPROVAL_WAIT = frozenset(('WAIT', 'WAITING', 'WAIT_FOR_APPROVAL', 'WAITING_FOR_APPROVAL'))


class ConfigurationError(Exception):
    pass


class ObservationError(Exception):
    def __init__(self, error_class):
        Exception.__init__(self, error_class)
        self.error_class = error_class


def _safe_text(value):
    """Keep notification fields bounded and free of control characters."""
    return ''.join(ch for ch in str(value) if ch.isalnum() or ch in '._:-').strip()[:128]


def _target_key(target):
    return '%s|%s|%s' % (target['task_id'], target['pipeline'], target['run'])


def _validate_config(value):
    if not isinstance(value, dict):
        raise ConfigurationError('config_object_required')
    allowed = set(('targets', 'state', 'org', 'mail_enabled'))
    if set(value) - allowed:
        raise ConfigurationError('unknown_config_field')
    if value.get('org', FLOW_ORG) != FLOW_ORG:
        raise ConfigurationError('fixed_org_required')
    mail_enabled = value.get('mail_enabled', True)
    if not isinstance(mail_enabled, bool):
        raise ConfigurationError('mail_enabled_invalid')
    state = value.get('state')
    if not isinstance(state, str) or not state or '\x00' in state:
        raise ConfigurationError('state_path_required')
    targets = value.get('targets')
    if not isinstance(targets, list) or not targets:
        raise ConfigurationError('targets_required')
    normalized = []
    seen = set()
    for raw in targets:
        if not isinstance(raw, dict) or set(raw) != set(('task_id', 'pipeline', 'run', 'expected_commit')):
            raise ConfigurationError('target_schema_invalid')
        target = {}
        for field in ('task_id', 'pipeline', 'run', 'expected_commit'):
            if not isinstance(raw.get(field), str):
                raise ConfigurationError('target_value_invalid')
            target[field] = raw[field]
        if not TASK_ID_RE.match(target['task_id']):
            raise ConfigurationError('task_id_invalid')
        if target['pipeline'] not in ALLOWED_PIPELINES:
            raise ConfigurationError('pipeline_not_allowed')
        if not NUMERIC_RE.match(target['run']):
            raise ConfigurationError('run_invalid')
        if not SHA_RE.match(target['expected_commit']):
            raise ConfigurationError('expected_commit_invalid')
        target['expected_commit'] = target['expected_commit'].lower()
        key = _target_key(target)
        if key in seen:
            raise ConfigurationError('duplicate_target')
        seen.add(key)
        normalized.append(target)
    return state, normalized, mail_enabled


def _read_state(path):
    try:
        with open(path, 'r') as handle:
            value = json.load(handle)
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            return {'version': 1, 'targets': {}}
        raise ObservationError('state_read_error')
    except (ValueError, TypeError):
        raise ObservationError('state_invalid')
    if not isinstance(value, dict) or value.get('version') != 1 or not isinstance(value.get('targets'), dict):
        raise ObservationError('state_invalid')
    return value


def _atomic_write(path, value):
    parent = os.path.dirname(os.path.abspath(path)) or '.'
    if not os.path.isdir(parent):
        os.makedirs(parent, 0o700)
    fd, temporary = tempfile.mkstemp(prefix='.%s.' % os.path.basename(path), dir=parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as handle:
            fd = None
            json.dump(value, handle, sort_keys=True, separators=(',', ':'))
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary)
        except OSError:
            pass


def _flow_status(target):
    argv = [
        'node', FLOW_COMMAND, 'status', '--org', FLOW_ORG,
        '--pipeline', target['pipeline'], '--run', target['run'],
        '--credentials-file', CREDENTIALS_FILE,
    ]
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, _stderr = process.communicate(timeout=FLOW_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise ObservationError('flow_timeout')
    except ObservationError:
        raise
    except OSError:
        raise ObservationError('flow_spawn_error')
    if process.returncode != 0:
        raise ObservationError('flow_command_error')
    try:
        decoded = stdout.decode('utf-8')
        result = json.loads(decoded)
    except (UnicodeDecodeError, ValueError, TypeError):
        raise ObservationError('flow_output_invalid')
    if not isinstance(result, dict):
        raise ObservationError('flow_output_invalid')
    if result.get('org') != FLOW_ORG or str(result.get('pipeline')) != target['pipeline'] or str(result.get('run')) != target['run']:
        raise ObservationError('flow_identity_mismatch')
    status = result.get('status')
    if not isinstance(status, str):
        raise ObservationError('flow_status_invalid')
    # A history entry is not checkout identity. Require exactly one source
    # from the fixed component repository and branch before trusting its HEAD.
    sources = result.get('sources')
    if not isinstance(sources, list) or len(sources) != 1:
        raise ObservationError('flow_sources_invalid')
    source = sources[0]
    if not isinstance(source, dict):
        raise ObservationError('flow_sources_invalid')
    if (source.get('repo') != EXPECTED_REPOS[target['pipeline']]
            or source.get('branch') != 'develop'):
        raise ObservationError('flow_source_identity_mismatch')
    commits = source.get('commits')
    if commits is None:
        commits = []
    if not isinstance(commits, list) or any(
            not isinstance(commit, str) or not SHA_RE.fullmatch(commit)
            for commit in commits):
        # Do not filter an invalid first item and promote history to HEAD.
        raise ObservationError('flow_sources_invalid')
    # Match flow-control sourceSummary: the first commit is HEAD. Preserve
    # ordering and duplicates; never sort or search history for expected SHA.
    return status.upper(), [commit.lower() for commit in commits]


def _send_email(subject, body):
    try:
        process = subprocess.Popen([MAIL_COMMAND, subject, body], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            process.communicate(timeout=MAIL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            return False
        return process.returncode == 0
    except OSError:
        return False


def _notice(target, state_target, event, subject, body, mail_enabled=True):
    """Attempt a mail at most three times; a success is only helper acceptance."""
    if not mail_enabled:
        return False
    notices = state_target.setdefault('notices', {})
    record = notices.setdefault(event, {'attempts': 0, 'accepted': False})
    if record.get('accepted'):
        return False
    attempts = record.get('attempts', 0)
    if not isinstance(attempts, int) or attempts < 0:
        attempts = 0
    if attempts >= 3:
        record['attempts'] = 3
        record['accepted'] = False
        return True
    record['attempts'] = attempts + 1
    accepted = _send_email(subject, body)
    record['accepted'] = bool(accepted)
    if accepted:
        record['receipt'] = {'accepted_by_mail_helper': True, 'inbox_delivery': 'unknown'}
        return False
    record['receipt'] = {'accepted_by_mail_helper': False, 'inbox_delivery': 'unknown'}
    return True


def _terminal_notice(target, status, commits):
    title = 'Flow %s %s %s' % (target['pipeline'], target['run'], status)
    base = '任务 %s；流水线 %s；运行 %s；状态 %s。' % (
        target['task_id'], target['pipeline'], target['run'], status)
    if status == 'SUCCESS':
        success_text = 'Flow成功，线上版本/业务验收仍需主控核验。'
        if commits and commits[0] == target['expected_commit']:
            return ('success_expected_commit', title,
                    base + '提交 %s 已匹配。%s' % (target['expected_commit'], success_text))
        actual = commits[0] if commits else 'missing'
        return ('success_sha_mismatch', title + ' SHA不匹配',
                base + '期望提交 %s；观察HEAD %s。源码未匹配，不视为发布成功；需主控核验。' %
                (target['expected_commit'], actual))
    if status == 'WAIT' or status in APPROVAL_WAIT:
        return ('approval_wait', title + ' 等待审批', base + '等待审批；需主控处理。')
    return ('terminal_' + status.lower(), title, base + '需主控核验。')


def _observe_target(target, state_target, mail_enabled=True):
    """Return whether this observation requires a main-controller exit status."""
    try:
        status, commits = _flow_status(target)
    except ObservationError as exc:
        error_class = _safe_text(exc.error_class) or 'flow_observation_error'
        previous = state_target.get('last_observation', {})
        if previous.get('kind') == 'error' and previous.get('class') == error_class:
            streak = state_target.get('error_streak', 0) + 1
        else:
            streak = 1
        state_target['last_observation'] = {'kind': 'error', 'class': error_class}
        state_target['error_streak'] = streak
        if streak >= 3:
            mail_failed = _notice(
                target, state_target, 'observation_error_' + error_class,
                'Flow %s %s 观察异常' % (target['pipeline'], target['run']),
                '任务 %s；流水线 %s；运行 %s；观察阶段 %s 连续%d次异常。需主控核验。' %
                (target['task_id'], target['pipeline'], target['run'], error_class, streak),
                mail_enabled=mail_enabled)
            if mail_failed:
                return True
        return error_class in ('flow_identity_mismatch', 'flow_sources_invalid',
                               'flow_source_identity_mismatch')

    state_target['error_streak'] = 0
    observation = {'kind': 'status', 'status': status, 'commits': commits}
    previous = state_target.get('last_observation')
    state_target['last_observation'] = observation
    if status in TERMINAL or status in APPROVAL_WAIT:
        notice = _terminal_notice(target, status, commits)
        if notice is not None:
            event, subject, body = notice
            task_failed = status in ('FAIL', 'CANCELED') or event == 'success_sha_mismatch'
            # A stable Flow state is not re-notified after acceptance.  An SMTP
            # failure is the sole exception: retry its same pending notice up
            # to the fixed three-attempt cap.
            if previous == observation:
                record = state_target.get('notices', {}).get(event, {})
                if record.get('accepted'):
                    return task_failed
                if record.get('attempts', 0) >= 3:
                    return True
            mail_failed = _notice(target, state_target, event, subject, body,
                                  mail_enabled=mail_enabled)
            return task_failed or mail_failed
    if previous == observation:
        return False
    return False


def check(config):
    state_path, targets, mail_enabled = _validate_config(config)
    lock_path = state_path + '.lock'
    parent = os.path.dirname(os.path.abspath(lock_path)) or '.'
    if not os.path.isdir(parent):
        os.makedirs(parent, 0o700)
    try:
        lock = open(lock_path, 'a+')
    except IOError:
        return EXIT_MAIN_CONTROLLER_REQUIRED
    try:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                return EXIT_OK
            return EXIT_MAIN_CONTROLLER_REQUIRED
        state = _read_state(state_path)
        # Keep one explicit pause marker while observations continue.  The
        # marker is configuration state only; notices and receipts stay
        # untouched until an operator re-enables mail.
        if mail_enabled:
            state.pop('mail_paused', None)
        else:
            state['mail_paused'] = {'reason': 'mail_disabled'}
        requires_controller = False
        for target in targets:
            target_state = state['targets'].setdefault(_target_key(target), {})
            if _observe_target(target, target_state, mail_enabled=mail_enabled):
                requires_controller = True
        _atomic_write(state_path, state)
        return EXIT_MAIN_CONTROLLER_REQUIRED if requires_controller else EXIT_OK
    except ObservationError:
        return EXIT_MAIN_CONTROLLER_REQUIRED
    finally:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except IOError:
            pass
        lock.close()


def main(argv=None):
    # Keep this one-shot interface deliberately exact and silent: a scheduler
    # can use only the exit code without receiving Flow output or error text.
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 3 or argv[0] != '--check' or argv[1] != '--config':
        return EXIT_MAIN_CONTROLLER_REQUIRED
    try:
        config = json.loads(argv[2])
        return check(config)
    except (ValueError, TypeError, ConfigurationError):
        return EXIT_MAIN_CONTROLLER_REQUIRED


if __name__ == '__main__':
    sys.exit(main())
