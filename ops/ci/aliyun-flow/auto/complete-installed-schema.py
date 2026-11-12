#!/usr/bin/python3
"""Complete the fixed API49 additive schemas without touching application lifecycle.

The only production forms are::

    complete-installed-schema.py verify <private-bundle-root>
    complete-installed-schema.py complete <private-bundle-root>

Both forms install only the two manifest-bound canonical runner corrections and plan
F06 then E05.  ``complete`` additionally applies F06 then E05 once for the Ops Flow
run.  There are no caller-selected SQL, runner, database, artifact, or result paths.
"""
from __future__ import print_function

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


OPS_PIPELINE = '5264702'
API_BINDING = {
    'pipelineId': '5260799',
    'runId': '49',
    'sourceCommitSha': '4be112cdde8397590760292eb04eb823ad88299d',
    'sourceTreeSha': '534c185dce7d07f90333b242120da5284d324ff5',
    'jarSha256': 'dcab9c7105d5b9d30a8c3f37642dbb06259eb1b2a16a9b9f00ab574399cc3933',
    'receiptSha256': '780b4bc59ac2481dbae3ab719ddbc3b5ad1772bdebcb8b295c2f271550746060',
}
RUNNERS = {
    'f06': {
        'name': 'cyf-api-additive-schema',
        'candidateSha256': 'b1a972c4174bbc36a585cec51f815eab5676cd4ec3c3985d0c74ca4c2798beb6',
        'passwordEnv': 'CYF_F06_MYSQL_PASSWORD',
        'passwordFile': 'f06-schema-password',
        'sqlSha256': '77ed9db141c9eedce5e357ebd562c02e060a6cdc238825ade1f60bc5c9dbe9cc',
        'resourceInner': 'db/agent-task-artifact-outcome-f06.sql',
        'tables': ['agent_task_artifact_outcome',
                   'agent_task_artifact_outcome_decision'],
        'lockOrder': ['f06_runner_file_lock', 'f06_mysql_named_lock'],
    },
    'e05': {
        'name': 'cyf-api-e05-additive-schema',
        'candidateSha256': '265d36774768577335fd4bfd5f342010a9c2bd5d4a5a6d4be100e28b827b5cb6',
        'passwordEnv': 'CYF_E05_MYSQL_PASSWORD',
        'passwordFile': 'e05-schema-password',
        'sqlSha256': 'da1ceedd4bfad55f141613d9acdfccb7ee604127360f65f59e5bb053009dcda1',
        'resourceInner': 'db/agent-work-item-reassignment-e05.sql',
        'tables': ['agent_work_item_reassignment'],
        'lockOrder': ['e05_runner_file_lock', 'e05_mysql_named_lock'],
    },
}
RUNNER_ORDER = ('f06', 'e05')
MANIFEST_NAME = 'schema-completion-manifest.json'
SHA_RE = re.compile(r'^[0-9a-f]{64}$')
RUN_RE = re.compile(r'^[1-9][0-9]*$')
STAMP_RE = re.compile(r'^[0-9]{8}T[0-9]{6}Z$')
TRANSACTION_MODEL = 'mysql_ddl_autocommit_per_create_no_rollback_or_drop'
WRAPPER_LOCK_ORDER = ['flow_coordinator_lock', 'api_release_lock']


class CompletionError(Exception):
    def __init__(self, code, detail=None):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size,
            getattr(info, 'st_mtime_ns', int(info.st_mtime * 1000000000)))


def safe_directory(path, uid, mode=None):
    try:
        info = os.lstat(str(path))
    except OSError:
        raise CompletionError('required_directory_missing', str(path))
    if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or info.st_uid != uid or info.st_mode & 0o022):
        raise CompletionError('required_directory_unsafe', str(path))
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise CompletionError('required_directory_mode_invalid', str(path))
    return info


def ensure_private_directory(path, uid, gid):
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = safe_directory(path, uid, 0o700)
    if info.st_gid != gid:
        raise CompletionError('private_directory_group_invalid', str(path))


def read_stable(path, uid, mode=None, allow_group_write=False):
    try:
        before = os.lstat(str(path))
    except OSError:
        raise CompletionError('required_file_missing', str(path))
    unsafe_write = before.st_mode & (0o002 if allow_group_write else 0o022)
    if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)
            or before.st_uid != uid or before.st_nlink != 1 or unsafe_write):
        raise CompletionError('required_file_unsafe', str(path))
    if mode is not None and stat.S_IMODE(before.st_mode) != mode:
        raise CompletionError('required_file_mode_invalid', str(path))
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags)
    except OSError:
        raise CompletionError('required_file_open_failed', str(path))
    try:
        opened = os.fstat(fd)
        if signature(opened) != signature(before):
            raise CompletionError('required_file_changed', str(path))
        chunks = []
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    try:
        current = os.lstat(str(path))
    except OSError:
        raise CompletionError('required_file_changed', str(path))
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise CompletionError('required_file_changed', str(path))
    return b''.join(chunks), signature(current), current


def digest_stable(path, uid, mode=None):
    """Hash a large regular file without retaining its payload in memory."""
    try:
        before = os.lstat(str(path))
    except OSError:
        raise CompletionError('required_file_missing', str(path))
    if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)
            or before.st_uid != uid or before.st_nlink != 1 or before.st_mode & 0o022):
        raise CompletionError('required_file_unsafe', str(path))
    if mode is not None and stat.S_IMODE(before.st_mode) != mode:
        raise CompletionError('required_file_mode_invalid', str(path))
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags)
    except OSError:
        raise CompletionError('required_file_open_failed', str(path))
    value = hashlib.sha256()
    try:
        opened = os.fstat(fd)
        if signature(opened) != signature(before):
            raise CompletionError('required_file_changed', str(path))
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            value.update(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    try:
        current = os.lstat(str(path))
    except OSError:
        raise CompletionError('required_file_changed', str(path))
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise CompletionError('required_file_changed', str(path))
    return value.hexdigest(), signature(current)


def fsync_directory(path):
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
    fd = os.open(str(path), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def create_exclusive(path, data, uid, gid, mode=0o600):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags, mode)
    except FileExistsError:
        raise CompletionError('operation_already_recorded', str(path))
    except OSError:
        raise CompletionError('exclusive_record_create_failed', str(path))
    try:
        os.fchmod(fd, mode)
        os.fchown(fd, uid, gid)
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    fsync_directory(path.parent)


def atomic_install(path, data, uid, gid, mode):
    fd, temporary = tempfile.mkstemp(prefix='.schema-completion-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as target:
            os.fchmod(target.fileno(), mode)
            os.fchown(target.fileno(), uid, gid)
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, str(path))
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Journal(object):
    """Append-only, non-overwriting report retained even after interruption."""
    def __init__(self, path, uid, gid, start):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        try:
            self.fd = os.open(str(path), flags, 0o600)
        except FileExistsError:
            raise CompletionError('operation_report_exists', str(path))
        except OSError:
            raise CompletionError('operation_report_create_failed', str(path))
        self.path = path
        os.fchmod(self.fd, 0o600)
        os.fchown(self.fd, uid, gid)
        self.append(start)
        fsync_directory(path.parent)

    def append(self, value):
        data = json_bytes(value)
        offset = 0
        while offset < len(data):
            offset += os.write(self.fd, data[offset:])
        os.fsync(self.fd)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class Runtime(object):
    """Closed production paths; tests inject an equivalent temporary fixture."""
    def __init__(self, root_uid=0, root_gid=0):
        self.uid = root_uid
        self.gid = root_gid
        self.destination = Path('/usr/local/sbin')
        self.state_root = Path('/home/isp/state/cyf-api-flow')
        self.record = self.state_root / 'record.json'
        self.jar = Path('/home/isp/hosts/cyf/api/cyf-api-kit.jar')
        self.coordination_lock = Path('/tmp/cyf-api-flow-auto-approval-v2.lock')
        self.release_lock = Path('/tmp/cyf-release-api.lock')
        self.curl = Path('/usr/bin/curl')
        self.health_url = 'http://127.0.0.1:10018/actuator/health'
        self.bundle_uid = 0
        self.runner_gid = 0
        self.jar_mode = 0o640
        self.record_mode = 0o600
        self.password_mode = 0o600
        self.runner_mode = 0o755
        self.state_mode = 0o700
        self.production = True
        self.protected_directories = (
            Path('/usr'), Path('/usr/local'), Path('/usr/local/sbin'),
            Path('/home/isp/state'), Path('/home/isp/state/cyf-api-flow'),
            Path('/home'), Path('/home/isp'), Path('/home/isp/hosts'), Path('/home/isp/hosts/cyf'),
            Path('/home/isp/hosts/cyf/api'),
        )


def load_manifest(bundle, action, env, runtime):
    if not bundle.is_absolute():
        raise CompletionError('bundle_path_not_absolute')
    try:
        resolved_bundle = bundle.resolve(strict=True)
    except OSError:
        raise CompletionError('bundle_path_invalid')
    if resolved_bundle != bundle:
        raise CompletionError('bundle_path_invalid')
    safe_directory(bundle, runtime.bundle_uid)
    manifest_bytes, ignored, ignored_info = read_stable(
        bundle / MANIFEST_NAME, runtime.bundle_uid, 0o600)
    try:
        manifest = json.loads(manifest_bytes.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        raise CompletionError('manifest_json_invalid')
    expected_keys = {'schemaVersion', 'action', 'opsFlow', 'installedApi', 'runners'}
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        raise CompletionError('manifest_shape_invalid')
    if manifest['schemaVersion'] != 1 or manifest['action'] != action:
        raise CompletionError('manifest_action_invalid')
    ops = manifest['opsFlow']
    if (not isinstance(ops, dict) or set(ops) != {'pipelineId', 'runId'}
            or ops.get('pipelineId') != OPS_PIPELINE
            or not isinstance(ops.get('runId'), str) or not RUN_RE.fullmatch(ops['runId'])):
        raise CompletionError('manifest_ops_binding_invalid')
    if env.get('PIPELINE_ID') != OPS_PIPELINE or env.get('BUILD_NUMBER') != ops['runId']:
        raise CompletionError('flow_environment_binding_invalid')
    if manifest['installedApi'] != API_BINDING:
        raise CompletionError('manifest_installed_api_binding_invalid')
    runners = manifest['runners']
    if not isinstance(runners, dict) or set(runners) != set(RUNNER_ORDER):
        raise CompletionError('manifest_runner_set_invalid')
    candidate_root = bundle / 'ops/ci/aliyun-flow/host'
    safe_directory(bundle / 'ops', runtime.bundle_uid)
    safe_directory(bundle / 'ops/ci', runtime.bundle_uid)
    safe_directory(bundle / 'ops/ci/aliyun-flow', runtime.bundle_uid)
    safe_directory(candidate_root, runtime.bundle_uid)
    candidates = {}
    for key in RUNNER_ORDER:
        value = runners[key]
        if (not isinstance(value, dict)
                or set(value) != {'beforeSha256', 'candidateSha256'}
                or not isinstance(value['beforeSha256'], str)
                or not SHA_RE.fullmatch(value['beforeSha256'])
                or value['candidateSha256'] != RUNNERS[key]['candidateSha256']
                or value['beforeSha256'] == value['candidateSha256']):
            raise CompletionError('manifest_runner_binding_invalid', key)
        source = candidate_root / RUNNERS[key]['name']
        data, ignored_sig, ignored_stat = read_stable(
            source, runtime.bundle_uid, runtime.runner_mode)
        if sha256_bytes(data) != value['candidateSha256']:
            raise CompletionError('candidate_digest_mismatch', key)
        candidates[key] = data
    return manifest, manifest_bytes, candidates


def acquire_lock(path, uid):
    data, before_signature, info = read_stable(path, uid, allow_group_write=True)
    if data not in (b'',):
        # Lock content is not an API; only reject unsafe metadata, not benign bytes.
        pass
    flags = os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags)
    except OSError:
        raise CompletionError('lock_open_failed', str(path))
    try:
        opened = os.fstat(fd)
        current = os.lstat(str(path))
        if (signature(opened) != before_signature
                or signature(current) != before_signature
                or not stat.S_ISREG(opened.st_mode) or opened.st_uid != uid
                or opened.st_nlink != 1 or opened.st_mode & 0o002):
            raise CompletionError('lock_inode_changed', str(path))
        fcntl.flock(fd, fcntl.LOCK_EX)
        current = os.lstat(str(path))
        if signature(os.fstat(fd)) != signature(current):
            raise CompletionError('lock_inode_changed', str(path))
        return fd
    except BaseException:
        os.close(fd)
        raise


def validate_record_and_jar(runtime):
    record_bytes, record_signature, ignored = read_stable(
        runtime.record, runtime.uid, runtime.record_mode)
    try:
        record = json.loads(record_bytes.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        raise CompletionError('installed_record_json_invalid')
    keys = {
        'schema_version', 'status', 'phase', 'recovery', 'ticket_sha256',
        'source_commit_sha', 'source_tree_sha', 'run_id', 'receipt_sha256',
        'candidate_sha256', 'previous_sha256', 'backup', 'candidate_stop_rc', 'timestamp',
    }
    backup = record.get('backup')
    backup_path = Path(backup) if isinstance(backup, str) else Path('.')
    if (not isinstance(record, dict) or set(record) != keys
            or record.get('schema_version') != 2 or record.get('status') != 'installed'
            or record.get('phase') != 'installed' or record.get('recovery') != 'not_required'
            or not isinstance(record.get('ticket_sha256'), str)
            or not SHA_RE.fullmatch(record['ticket_sha256'])
            or not isinstance(record.get('previous_sha256'), str)
            or not SHA_RE.fullmatch(record['previous_sha256'])
            or not isinstance(record.get('candidate_stop_rc'), int)
            or isinstance(record.get('candidate_stop_rc'), bool)
            or record.get('candidate_stop_rc') != 0
            or not isinstance(record.get('timestamp'), str)
            or not STAMP_RE.fullmatch(record['timestamp'])
            or not backup_path.is_absolute()
            or backup_path.parent != runtime.state_root / 'backups'
            or not re.fullmatch(
                r'[0-9]{8}T[0-9]{6}Z-[0-9a-f]{64}-[0-9]+\.jar', backup_path.name)
            or record.get('run_id') != API_BINDING['runId']
            or record.get('source_commit_sha') != API_BINDING['sourceCommitSha']
            or record.get('source_tree_sha') != API_BINDING['sourceTreeSha']
            or record.get('candidate_sha256') != API_BINDING['jarSha256']
            or record.get('receipt_sha256') != API_BINDING['receiptSha256']):
        raise CompletionError('installed_record_binding_mismatch')
    jar_sha256, jar_signature = digest_stable(
        runtime.jar, runtime.uid, runtime.jar_mode)
    if jar_sha256 != API_BINDING['jarSha256']:
        raise CompletionError('installed_jar_digest_mismatch')
    return {
        'recordSha256': sha256_bytes(record_bytes),
        'recordSignature': record_signature,
        'jarSignature': jar_signature,
    }


def validate_health(runtime):
    read_stable(runtime.curl, runtime.uid, 0o755)
    child_env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'}
    try:
        result = subprocess.run(
            [str(runtime.curl), '--fail', '--silent', '--show-error', runtime.health_url],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=child_env, close_fds=True)
    except OSError:
        raise CompletionError('local_health_request_failed')
    if result.returncode != 0:
        raise CompletionError('local_health_request_failed')
    try:
        value = json.loads(result.stdout.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        raise CompletionError('local_health_json_invalid')
    if (not isinstance(value, dict) or value.get('apiVersion') != 'V3'
            or not isinstance(value.get('status'), dict)
            or value['status'].get('code') != 'UP'):
        raise CompletionError('local_health_not_up')
    return sha256_bytes(result.stdout)


def validate_runtime_paths(runtime, manifest):
    for path in runtime.protected_directories:
        safe_directory(path, runtime.uid)
    safe_directory(runtime.destination, runtime.uid)
    safe_directory(runtime.state_root, runtime.uid, runtime.state_mode)
    current = {}
    passwords = {}
    for key in RUNNER_ORDER:
        spec = RUNNERS[key]
        installed, ignored, info = read_stable(
            runtime.destination / spec['name'], runtime.uid, runtime.runner_mode)
        actual = sha256_bytes(installed)
        allowed = (manifest['runners'][key]['beforeSha256'],
                   manifest['runners'][key]['candidateSha256'])
        if actual not in allowed:
            raise CompletionError('installed_runner_digest_drift', key)
        current[key] = {'bytes': installed, 'sha256': actual}
        password, ignored, ignored_info = read_stable(
            runtime.state_root / spec['passwordFile'], runtime.uid, runtime.password_mode)
        if not password or b'\x00' in password or b'\n' in password or b'\r' in password:
            raise CompletionError('schema_password_file_invalid', key)
        try:
            passwords[key] = password.decode('utf-8')
        except UnicodeDecodeError:
            raise CompletionError('schema_password_file_invalid', key)
    artifact = validate_record_and_jar(runtime)
    health_sha = validate_health(runtime)
    return current, passwords, artifact, health_sha


def prepare_persistence(runtime, manifest, manifest_bytes, action):
    base = runtime.state_root / 'schema-completion'
    reports = base / 'operations-reports'
    attempts = base / 'attempt-markers'
    backups = base / 'tooling-backups'
    ensure_private_directory(base, runtime.uid, runtime.gid)
    ensure_private_directory(reports, runtime.uid, runtime.gid)
    ensure_private_directory(attempts, runtime.uid, runtime.gid)
    ensure_private_directory(backups, runtime.uid, runtime.gid)
    run_id = manifest['opsFlow']['runId']
    report_path = reports / ('ops-run-%s-%s.jsonl' % (run_id, action))
    start = {
        'schemaVersion': 1, 'event': 'started', 'action': action,
        'opsFlow': manifest['opsFlow'], 'installedApi': API_BINDING,
        'manifestSha256': sha256_bytes(manifest_bytes),
        'lockOrder': WRAPPER_LOCK_ORDER,
        'applicationLifecycle': False, 'featureFlagsChanged': False,
        'businessCompletionClaimed': False,
    }
    journal = Journal(report_path, runtime.uid, runtime.gid, start)
    if action == 'complete':
        marker = attempts / ('ops-run-%s.json' % run_id)
        marker_value = dict(start)
        marker_value['event'] = 'complete_attempt_claimed'
        try:
            create_exclusive(marker, json_bytes(marker_value), runtime.uid, runtime.gid)
        except BaseException:
            journal.append({'schemaVersion': 1, 'event': 'terminal', 'status': 'failed',
                            'error': 'complete_attempt_already_exists'})
            journal.close()
            raise CompletionError('complete_attempt_already_exists')
    # Action and Ops run differ between plan and completion, but the immutable
    # original-runner backup identity is solely the exact before/candidate catalog.
    identity = sha256_bytes(json_bytes(manifest['runners']))
    backup = backups / identity
    ensure_private_directory(backup, runtime.uid, runtime.gid)
    return journal, backup, report_path


def install_candidates(runtime, manifest, candidates, current, backup, journal):
    installed = {}
    for key in RUNNER_ORDER:
        spec = RUNNERS[key]
        binding = manifest['runners'][key]
        destination = runtime.destination / spec['name']
        if current[key]['sha256'] == binding['beforeSha256']:
            backup_path = backup / (spec['name'] + '.before')
            if backup_path.exists() or backup_path.is_symlink():
                old, ignored, ignored_info = read_stable(
                    backup_path, runtime.uid, 0o600)
                if sha256_bytes(old) != binding['beforeSha256']:
                    raise CompletionError('runner_backup_digest_mismatch', key)
            else:
                create_exclusive(backup_path, current[key]['bytes'],
                                 runtime.uid, runtime.gid, 0o600)
            atomic_install(destination, candidates[key], runtime.uid,
                           runtime.runner_gid, runtime.runner_mode)
            disposition = 'installed_candidate'
        else:
            backup_path = backup / (spec['name'] + '.before')
            old, ignored, ignored_info = read_stable(
                backup_path, runtime.uid, 0o600)
            if sha256_bytes(old) != binding['beforeSha256']:
                raise CompletionError('runner_backup_digest_mismatch', key)
            disposition = 'candidate_already_installed'
        readback, ignored, readback_info = read_stable(
            destination, runtime.uid, runtime.runner_mode)
        actual = sha256_bytes(readback)
        if actual != binding['candidateSha256']:
            raise CompletionError('installed_runner_readback_mismatch', key)
        installed[key] = actual
        journal.append({'schemaVersion': 1, 'event': 'runner_installed',
                        'runner': key, 'disposition': disposition,
                        'beforeSha256': binding['beforeSha256'],
                        'candidateSha256': actual})
    return installed


def expected_binding():
    return {
        'organization': '5fb7d76ee6f9d07f148529c7',
        'pipeline': API_BINDING['pipelineId'],
        'run': API_BINDING['runId'],
        'source_commit': API_BINDING['sourceCommitSha'],
        'source_tree': API_BINDING['sourceTreeSha'],
        'jar_sha256': API_BINDING['jarSha256'],
        'receipt_sha256': API_BINDING['receiptSha256'],
    }


def validate_runner_report(key, operation, report, return_code):
    spec = RUNNERS[key]
    mandatory = {'schema_version', 'operation', 'status', 'transaction_model',
                 'lock_order', 'tables', 'binding', 'candidate'}
    allowed_report_keys = mandatory | {'error', 'failed_table'}
    if (not isinstance(report, dict) or not mandatory.issubset(set(report))
            or not set(report).issubset(allowed_report_keys)
            or report.get('status') not in ('pass', 'failed')):
        raise CompletionError('runner_report_shape_invalid', key)
    if (report.get('schema_version') != 1 or report.get('operation') != operation
            or report.get('transaction_model') != TRANSACTION_MODEL
            or report.get('lock_order') != spec['lockOrder']
            or report.get('binding') != expected_binding()):
        raise CompletionError('runner_report_binding_invalid', key)
    candidate = report.get('candidate')
    expected_candidate = {
        'resource_outer': 'BOOT-INF/lib/jia-agent-mapper-1.1.2-SNAPSHOT.jar',
        'resource_inner': spec['resourceInner'],
        'sql_sha256': spec['sqlSha256'],
        'tables': spec['tables'],
        'statement_policy': 'exact_create_table_if_not_exists_only',
    }
    if candidate != expected_candidate:
        raise CompletionError('runner_report_candidate_invalid', key)
    tables = report.get('tables')
    if not isinstance(tables, dict) or set(tables) != set(spec['tables']):
        raise CompletionError('runner_report_table_set_invalid', key)
    for table in spec['tables']:
        table_report = tables[table]
        if (not isinstance(table_report, dict)
                or not set(table_report).issubset({'status', 'mismatches'})
                or not isinstance(table_report.get('status'), str)
                or ('mismatches' in table_report
                    and (not isinstance(table_report['mismatches'], list)
                         or not all(isinstance(value, str)
                                    for value in table_report['mismatches'])))):
            raise CompletionError('runner_report_table_status_invalid', key)
    if (return_code == 0) != (report.get('status') == 'pass'):
        raise CompletionError('runner_exit_status_disagrees_with_report', key)
    if return_code != 0:
        raise CompletionError('%s_%s_failed' % (key, operation))
    allowed = ({'existing_equivalent', 'planned_create'} if operation == 'plan'
               else {'existing_equivalent', 'created_equivalent'})
    if any(tables[table]['status'] not in allowed for table in spec['tables']):
        raise CompletionError('runner_pass_table_status_invalid', key)


def invoke_runner(runtime, key, operation, password, journal):
    spec = RUNNERS[key]
    runner_path = runtime.destination / spec['name']
    runner_sha256, ignored_signature = digest_stable(
        runner_path, runtime.uid, runtime.runner_mode)
    if runner_sha256 != spec['candidateSha256']:
        raise CompletionError('installed_runner_changed_before_invocation', key)
    argv = [str(runner_path)]
    if operation == 'apply':
        argv.append('--apply')
    child_env = {
        'PATH': '/usr/sbin:/usr/bin:/sbin:/bin',
        'LC_ALL': 'C',
        spec['passwordEnv']: password,
    }
    try:
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=child_env, close_fds=True)
    except OSError:
        journal.append({'schemaVersion': 1, 'event': 'runner_finished',
                        'runner': key, 'operation': operation,
                        'reportRetained': False, 'error': 'runner_start_failed'})
        raise CompletionError('runner_start_failed', key)
    secret = password.encode('utf-8')
    summary = {
        'schemaVersion': 1, 'event': 'runner_finished', 'runner': key,
        'operation': operation, 'exitCode': result.returncode,
        'stdoutSha256': sha256_bytes(result.stdout),
        'stderrSha256': sha256_bytes(result.stderr),
    }
    if secret in result.stdout or secret in result.stderr:
        summary['reportRetained'] = False
        journal.append(summary)
        raise CompletionError('runner_output_contains_secret', key)
    try:
        lines = result.stdout.decode('utf-8', errors='strict').splitlines()
    except UnicodeDecodeError:
        summary['reportRetained'] = False
        journal.append(summary)
        raise CompletionError('runner_stdout_contract_invalid', key)
    if len(lines) != 1:
        summary['reportRetained'] = False
        journal.append(summary)
        raise CompletionError('runner_stdout_contract_invalid', key)
    try:
        report = json.loads(lines[0])
    except ValueError:
        summary['reportRetained'] = False
        journal.append(summary)
        raise CompletionError('runner_report_json_invalid', key)
    summary['reportRetained'] = True
    summary['runnerReport'] = report
    journal.append(summary)
    validate_runner_report(key, operation, report, result.returncode)
    return report


def execute(action, bundle, env, runtime=None):
    if action not in ('verify', 'complete'):
        raise CompletionError('action_rejected')
    runtime = Runtime() if runtime is None else runtime
    if runtime.production and os.geteuid() != 0:
        raise CompletionError('root_required')
    manifest, manifest_bytes, candidates = load_manifest(bundle, action, env, runtime)
    handles = []
    journal = None
    report_path = None
    try:
        handles.append(acquire_lock(runtime.coordination_lock, runtime.uid))
        handles.append(acquire_lock(runtime.release_lock, runtime.uid))
        current, passwords, artifact, health_sha = validate_runtime_paths(runtime, manifest)
        journal, backup, report_path = prepare_persistence(
            runtime, manifest, manifest_bytes, action)
        journal.append({'schemaVersion': 1, 'event': 'preflight_passed',
                        'artifact': artifact, 'healthResponseSha256': health_sha})
        installed = install_candidates(
            runtime, manifest, candidates, current, backup, journal)
        artifact_after = validate_record_and_jar(runtime)
        health_after = validate_health(runtime)
        plans = {}
        for key in RUNNER_ORDER:
            plans[key] = invoke_runner(runtime, key, 'plan', passwords[key], journal)
        applies = {}
        if action == 'complete':
            # Re-check the fixed installed artifact and local health immediately
            # before the first DDL. Runners independently re-bind package/record/JAR.
            validate_record_and_jar(runtime)
            validate_health(runtime)
            for key in RUNNER_ORDER:
                applies[key] = invoke_runner(
                    runtime, key, 'apply', passwords[key], journal)
        result = {
            'schemaVersion': 1, 'status': 'pass', 'action': action,
            'opsFlow': manifest['opsFlow'], 'installedApi': API_BINDING,
            'runnerSha256': installed,
            'plans': plans, 'applies': applies,
            'transactionModel': TRANSACTION_MODEL,
            'lockOrder': WRAPPER_LOCK_ORDER,
            'applicationRestarted': False, 'applicationLifecycleInvoked': False,
            'applicationArtifactOrInstalledRecordChanged': False,
            'featureFlagsChanged': False, 'businessCompletionClaimed': False,
            'operationsReport': str(report_path),
            'artifactAfter': artifact_after, 'healthResponseSha256': health_after,
        }
        journal.append({'schemaVersion': 1, 'event': 'terminal', 'status': 'pass',
                        'result': result})
        return result
    except CompletionError as exc:
        if journal is not None:
            journal.append({'schemaVersion': 1, 'event': 'terminal', 'status': 'failed',
                            'error': exc.code, 'detail': exc.detail,
                            'applicationLifecycleInvoked': False,
                            'featureFlagsChanged': False,
                            'businessCompletionClaimed': False})
        raise
    except Exception:
        if journal is not None:
            journal.append({'schemaVersion': 1, 'event': 'terminal', 'status': 'failed',
                            'error': 'internal_operation_error',
                            'applicationLifecycleInvoked': False,
                            'featureFlagsChanged': False,
                            'businessCompletionClaimed': False})
        raise CompletionError('internal_operation_error')
    finally:
        if journal is not None:
            journal.close()
        for fd in reversed(handles):
            os.close(fd)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in ('verify', 'complete'):
        result = {'schemaVersion': 1, 'status': 'failed', 'error': 'arguments_rejected'}
        print('CYF_SCHEMA_COMPLETION=' + json.dumps(result, sort_keys=True, separators=(',', ':')))
        return 2
    try:
        bundle = Path(argv[1])
        if not bundle.is_absolute() or bundle.is_symlink():
            raise CompletionError('bundle_path_invalid')
        result = execute(argv[0], bundle, dict(os.environ))
    except CompletionError as exc:
        result = {'schemaVersion': 1, 'status': 'failed', 'error': exc.code,
                  'applicationLifecycleInvoked': False,
                  'featureFlagsChanged': False, 'businessCompletionClaimed': False}
        print('CYF_SCHEMA_COMPLETION=' + json.dumps(result, sort_keys=True, separators=(',', ':')))
        return 1
    print('CYF_SCHEMA_COMPLETION=' + json.dumps(result, sort_keys=True, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
