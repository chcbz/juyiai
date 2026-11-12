"""Offline-only adversarial tests for the exact E05 additive schema runner."""
import copy
import fcntl
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import time
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-e05-additive-schema'
loader = importlib.machinery.SourceFileLoader('cyf_e05_schema_runner_test_module', str(RUNNER))
e05 = loader.load_module()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def hx(value):
    return value.encode('utf-8').hex().upper()


def optional(value):
    return '-' if value is None else '+' + hx(str(value))


def expected_rows(table, collation):
    spec = e05.EXPECTED_TABLES[table]
    rows = {
        'TABLES': [[hx(table), hx('InnoDB'), hx(collation)]],
        'COLUMNS': [],
        'STATISTICS': [],
        'CONSTRAINTS': [],
        'CHECKS': [],
    }
    for ordinal, value in enumerate(spec['columns'], 1):
        name, sql_type, nullable, default, extra = value
        string_type = sql_type.startswith('varchar(') or sql_type.startswith('char(')
        rows['COLUMNS'].append([
            hx(table), str(ordinal), hx(name), hx(sql_type), hx(nullable),
            optional(default), hx(extra), optional('utf8mb4' if string_type else None),
            optional(collation if string_type else None),
        ])
    for name, non_unique, columns, index_type in sorted(spec['indexes'], key=lambda value: value[0]):
        for sequence, column_name in enumerate(columns, 1):
            rows['STATISTICS'].append([
                hx(table), hx(name), str(non_unique), str(sequence), hx(column_name), '-',
                hx(index_type), hx('A'), hx('YES'),
            ])
    constraints = {}
    for name in spec['unique_constraints']:
        constraints[name] = ('PRIMARY KEY' if name == 'PRIMARY' else 'UNIQUE', 'YES')
    for name in spec['checks']:
        constraints[name] = ('CHECK', 'YES')
    for name, (kind, enforced) in sorted(constraints.items()):
        rows['CONSTRAINTS'].append([hx(table), hx(name), hx(kind), hx(enforced)])
    for name, clause in sorted(spec['checks'].items()):
        # MySQL 8 returns quoted identifiers and may parenthesize arithmetic operands.
        # Quote complete identifiers in one pass. Sequential substring replace
        # corrupts previous_lease_until when lease_until is processed later;
        # the old global backtick deletion accidentally concealed that fixture bug.
        identifiers = (
            'request_sha256', 'lease_fence_sha256', 'expected_work_item_version',
            'result_work_item_version', 'task_version', 'previous_agent_id',
            'target_agent_id', 'previous_lease_until', 'lease_until',
            'attempt_count', 'max_attempts', 'create_time', 'update_time')
        mysql_clause = re.sub(r'\b(?:' + '|'.join(identifiers) + r')\b',
                              lambda match: '`' + match.group(0) + '`', clause)
        mysql_clause = mysql_clause.replace('`expected_work_item_version` + 1',
                                             '(`expected_work_item_version` + 1)')
        rows['CHECKS'].append([hx(table), hx(name), hx('(' + mysql_clause + ')')])
    return rows


# Synthetic E05 SHOW fixture, transcribed from the fixed CREATE contract in
# MySQL 8.0.21 SHOW spelling (including arithmetic parentheses). E05 has NOT
# been created/read in production. Unlike F06 Run49, this is NOT live evidence.
E05_SHOW_TEXT = """CREATE TABLE `agent_work_item_reassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reassignment_id` varchar(100) NOT NULL COMMENT 'Deterministic scope/task/work-item/idempotency receipt identity',
  `request_sha256` char(64) NOT NULL COMMENT 'Canonical exact request digest',
  `task_id` varchar(100) NOT NULL,
  `work_item_id` varchar(100) NOT NULL,
  `operator_subject` varchar(100) NOT NULL COMMENT 'Exact authenticated JWT sub',
  `coordinator_agent_id` varchar(100) NOT NULL COMMENT 'Exact active task coordinator',
  `previous_agent_id` varchar(100) NOT NULL,
  `target_agent_id` varchar(100) NOT NULL,
  `source_command_id` varchar(100) NOT NULL,
  `command_id` varchar(100) NOT NULL COMMENT 'New immutable WORK_ITEM_EXECUTE command',
  `message_id` varchar(100) NOT NULL,
  `outbox_event_id` varchar(100) NOT NULL,
  `expected_work_item_version` bigint NOT NULL,
  `result_work_item_version` bigint NOT NULL,
  `task_version` bigint NOT NULL,
  `lease_fence_sha256` char(64) NOT NULL COMMENT 'SHA-256 of fresh lease token; token is never stored here',
  `previous_lease_until` bigint NOT NULL,
  `lease_until` bigint NOT NULL,
  `attempt_count` int NOT NULL,
  `max_attempts` int NOT NULL,
  `tenant_id` varchar(50) NOT NULL,
  `client_id` varchar(50) NOT NULL,
  `create_time` bigint NOT NULL,
  `update_time` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_work_item_reassignment_id` (`tenant_id`,`client_id`,`reassignment_id`),
  UNIQUE KEY `uk_work_item_reassignment_command` (`tenant_id`,`client_id`,`command_id`),
  KEY `idx_work_item_reassignment_latest` (`tenant_id`,`client_id`,`task_id`,`work_item_id`,`id`),
  CONSTRAINT `chk_work_item_reassignment_agents` CHECK ((`previous_agent_id` <> `target_agent_id`)),
  CONSTRAINT `chk_work_item_reassignment_digest` CHECK (((char_length(`request_sha256`) = 64) and (char_length(`lease_fence_sha256`) = 64))),
  CONSTRAINT `chk_work_item_reassignment_immutable_clock` CHECK (((`create_time` > 0) and (`update_time` = `create_time`))),
  CONSTRAINT `chk_work_item_reassignment_lease` CHECK (((`previous_lease_until` > 0) and (`lease_until` > `previous_lease_until`) and (`attempt_count` > 0) and (`attempt_count` < `max_attempts`))),
  CONSTRAINT `chk_work_item_reassignment_versions` CHECK (((`expected_work_item_version` >= 0) and (`result_work_item_version` = (`expected_work_item_version` + 1)) and (`task_version` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Immutable E05 explicit-target expired-lease reassignment receipts'
"""
E05_SHOW_ROWS = [['agent_work_item_reassignment', E05_SHOW_TEXT.splitlines()[0]]] + [
    [line] for line in E05_SHOW_TEXT.splitlines()[1:]]
# E05_SHOW_ROWS above is the frozen historical ownerless negative. The current
# synthetic SHOW below matches the new owner-complete CREATE, not the old bare
# CREATE. These offline fixtures are not live MySQL or production evidence.
CURRENT_OWNER_E05_SHOW_TEXT = E05_SHOW_TEXT.replace(
    '  PRIMARY KEY (`id`),', "  `owner_jiacn` varchar(50) NOT NULL COMMENT 'Authenticated task owner',\n  PRIMARY KEY (`id`),").replace(
    '  CONSTRAINT `chk_work_item_reassignment_agents`',
    '  KEY `idx_agent_work_item_reassignment_owner_scope` '
    '(`tenant_id`,`client_id`,`owner_jiacn`,`task_id`,`work_item_id`),\n'
    '  CONSTRAINT `chk_work_item_reassignment_agents`')
CURRENT_OWNER_E05_SHOW_ROWS = [
    ['agent_work_item_reassignment', CURRENT_OWNER_E05_SHOW_TEXT.splitlines()[0]]
] + [[line] for line in CURRENT_OWNER_E05_SHOW_TEXT.splitlines()[1:]]


# Frozen historical ownerless negative input, raw bytes/SHA from 7245df;
# never used as the new same-batch CREATE or a successful migration proof.
LEGACY_OWNERLESS_SQL_BYTES = b"-- M4-E05 bounded additive migration candidate.\n-- DDL only: no backfill, no lease mutation, and no transport/history rewrite.\nCREATE TABLE IF NOT EXISTS agent_work_item_reassignment (\n    id                          BIGINT NOT NULL AUTO_INCREMENT,\n    reassignment_id             VARCHAR(100) NOT NULL COMMENT 'Deterministic scope/task/work-item/idempotency receipt identity',\n    request_sha256              CHAR(64) NOT NULL COMMENT 'Canonical exact request digest',\n    task_id                     VARCHAR(100) NOT NULL,\n    work_item_id                VARCHAR(100) NOT NULL,\n    operator_subject            VARCHAR(100) NOT NULL COMMENT 'Exact authenticated JWT sub',\n    coordinator_agent_id        VARCHAR(100) NOT NULL COMMENT 'Exact active task coordinator',\n    previous_agent_id           VARCHAR(100) NOT NULL,\n    target_agent_id             VARCHAR(100) NOT NULL,\n    source_command_id           VARCHAR(100) NOT NULL,\n    command_id                  VARCHAR(100) NOT NULL COMMENT 'New immutable WORK_ITEM_EXECUTE command',\n    message_id                  VARCHAR(100) NOT NULL,\n    outbox_event_id             VARCHAR(100) NOT NULL,\n    expected_work_item_version  BIGINT NOT NULL,\n    result_work_item_version    BIGINT NOT NULL,\n    task_version                BIGINT NOT NULL,\n    lease_fence_sha256          CHAR(64) NOT NULL COMMENT 'SHA-256 of fresh lease token; token is never stored here',\n    previous_lease_until        BIGINT NOT NULL,\n    lease_until                 BIGINT NOT NULL,\n    attempt_count               INT NOT NULL,\n    max_attempts                INT NOT NULL,\n    tenant_id                   VARCHAR(50) NOT NULL,\n    client_id                   VARCHAR(50) NOT NULL,\n    create_time                 BIGINT NOT NULL,\n    update_time                 BIGINT NOT NULL,\n    PRIMARY KEY (id),\n    UNIQUE KEY uk_work_item_reassignment_id\n        (tenant_id, client_id, reassignment_id),\n    UNIQUE KEY uk_work_item_reassignment_command\n        (tenant_id, client_id, command_id),\n    KEY idx_work_item_reassignment_latest\n        (tenant_id, client_id, task_id, work_item_id, id),\n    CONSTRAINT chk_work_item_reassignment_digest\n        CHECK (CHAR_LENGTH(request_sha256)=64 AND CHAR_LENGTH(lease_fence_sha256)=64),\n    CONSTRAINT chk_work_item_reassignment_versions\n        CHECK (expected_work_item_version >= 0\n               AND result_work_item_version = expected_work_item_version + 1\n               AND task_version >= 0),\n    CONSTRAINT chk_work_item_reassignment_agents\n        CHECK (previous_agent_id <> target_agent_id),\n    CONSTRAINT chk_work_item_reassignment_lease\n        CHECK (previous_lease_until > 0 AND lease_until > previous_lease_until\n               AND attempt_count > 0 AND attempt_count < max_attempts),\n    CONSTRAINT chk_work_item_reassignment_immutable_clock\n        CHECK (create_time > 0 AND update_time = create_time)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4\n  COMMENT='Immutable E05 explicit-target expired-lease reassignment receipts';\n"
LEGACY_OWNERLESS_SQL_SHA256 = 'da1ceedd4bfad55f141613d9acdfccb7ee604127360f65f59e5bb053009dcda1'


E05_CREATE_GRANTS = [
    'GRANT USAGE ON *.* TO `cyf_e05_schema_runner`@`localhost`',
    'GRANT CREATE ON `jia`.`agent_work_item_reassignment` TO `cyf_e05_schema_runner`@`localhost`',
]


FAKE_MYSQL = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
import re
import re
import sys

root = Path(__file__).resolve().parents[1]
state_path = root / 'fake-state.json'
args_path = root / 'mysql-args.json'
args_path.write_text(json.dumps(sys.argv[1:], sort_keys=True))

def load():
    return json.loads(state_path.read_text())

def save(value):
    state_path.write_text(json.dumps(value, sort_keys=True))

def emit(rows):
    for row in rows:
        print('\t'.join(row), flush=True)

for raw in sys.stdin:
    statement = raw.strip()
    marker = re.match(r"SELECT '(_CYF_E05_[0-9]{4}_END_)';$", statement)
    if marker:
        print(marker.group(1), flush=True)
        continue
    state = load()
    state.setdefault('commands', []).append(statement)
    save(state)
    if 'GET_LOCK(' in statement:
        print(str(state.get('db_lock_result', 1)), flush=True)
        continue
    if 'RELEASE_LOCK(' in statement:
        print('1', flush=True)
        continue
    tag_match = re.search(r'/\*CYF_E05:([A-Z]+)\*/', statement)
    if tag_match:
        tag = tag_match.group(1)
        if state.get('metadata_error_tag') == tag:
            print('fixture metadata failure', file=sys.stderr, flush=True)
            continue
        if tag == 'GRANTS':
            emit([[value] for value in state['grants']])
            continue
        if tag == 'DEFAULTS':
            emit(state['default_rows'])
            continue
        if tag == 'SHOWFIRST':
            emit(state['show_rows'])
            continue
        if tag == 'SCHEMA':
            emit(state['schema_rows'])
            continue
        rows = []
        for table in sorted(state['tables']):
            table_state = state['tables'][table]
            if table_state == 'absent':
                continue
            table_rows = [list(row) for row in state['expected'][table][tag]]
            if table_state == 'column_drift' and tag == 'COLUMNS':
                table_rows[0][3] = state['hex_int']
            if table_state == 'nullable_drift' and tag == 'COLUMNS':
                table_rows[1][4] = state['hex_yes']
            if table_state == 'default_drift' and tag == 'COLUMNS':
                table_rows[1][5] = '+31'
            if table_state == 'check_drift' and tag == 'CHECKS':
                target = state.get('check_drift_hex_name')
                for row in table_rows:
                    if target is None or row[1] == target:
                        row[2] = state['hex_bad_check']
                        break
            if table_state == 'charset_drift' and tag == 'COLUMNS':
                table_rows[1][7] = state['hex_latin1_optional']
            if table_state == 'column_collation_drift' and tag == 'COLUMNS':
                table_rows[1][8] = state['hex_other_collation_optional']
            if table_state == 'index_attributes_drift' and tag == 'STATISTICS':
                table_rows[0][8] = state['hex_no']
            if table_state == 'engine_drift' and tag == 'TABLES':
                table_rows[0][1] = state['hex_myisam']
            if table_state == 'collation_drift' and tag == 'TABLES':
                table_rows[0][2] = state['hex_other_collation']
            if table_state == 'index_drift' and tag == 'STATISTICS':
                table_rows = table_rows[:-1]
            if table_state == 'constraint_drift' and tag == 'CONSTRAINTS':
                table_rows[0][3] = state['hex_no']
            rows.extend(table_rows)
        emit(rows)
        continue
    create = re.match(r'CREATE TABLE IF NOT EXISTS ([a-z0-9_]+) ', statement, re.I)
    if create:
        table = create.group(1).lower()
        state['creates'].append(table)
        if state.get('create_fail_on') == table:
            print('fixture create failure', file=sys.stderr, flush=True)
        else:
            state['tables'][table] = ('column_drift' if state.get('create_drift_on') == table
                                      else 'equivalent')
        save(state)
        continue
    print('unexpected fixture SQL', file=sys.stderr, flush=True)
'''


class ApiE05AdditiveSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-e05-schema-', dir='/tmp')
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        for name in ('service', 'state/incoming', 'bin'):
            (self.root / name).mkdir(parents=True, mode=0o700)
        self.mysql = self.root / 'bin/mysql'
        self.mysql.write_text(FAKE_MYSQL)
        self.mysql.chmod(0o700)
        self.collation = 'utf8mb4_0900_ai_ci'
        expected = {table: expected_rows(table, self.collation) for table in e05.TABLE_ORDER}
        self.state = {
            'schema_rows': [[hx('utf8'), hx('utf8_general_ci')]],
            'default_rows': [[hx(self.collation)]],
            'grants': list(E05_CREATE_GRANTS),
            'show_rows': copy.deepcopy(CURRENT_OWNER_E05_SHOW_ROWS),
            'expected': expected,
            'tables': {table: 'absent' for table in e05.TABLE_ORDER},
            'creates': [],
            'hex_int': hx('int'),
            'hex_yes': hx('YES'),
            'hex_no': hx('NO'),
            'hex_myisam': hx('MyISAM'),
            'hex_other_collation': hx('utf8mb4_bin'),
            'hex_latin1_optional': '+' + hx('latin1'),
            'hex_other_collation_optional': '+' + hx('utf8mb4_bin'),
            'hex_bad_check': hx('1 = 1'),
        }
        self.write_state()
        self.commit = 'a' * 40
        self.tree = 'b' * 40
        self.run_id = '44'
        self.resource = e05.E05_SQL_BYTES
        self.rebuild_release()
        self.secret = 'offline-only-secret-value'
        self.env = dict(os.environ)
        self.env.update(
            CYF_E05_SCHEMA_OFFLINE_TEST='YES',
            CYF_E05_SCHEMA_TEST_ROOT=str(self.root),
            CYF_E05_MYSQL_PASSWORD=self.secret,
            # These must not influence the fixed target catalog.
            CYF_E05_DATABASE='attacker_database',
            CYF_E05_SCHEMA='attacker_schema',
            MYSQL_PWD='inherited-wrong-secret',
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_state(self):
        path = self.root / 'fake-state.json'
        path.write_text(json.dumps(self.state, sort_keys=True))
        path.chmod(0o600)

    def read_state(self):
        return json.loads((self.root / 'fake-state.json').read_text())

    def build_jar(self, resource=None, nested_name=None, resource_name=None):
        resource = self.resource if resource is None else resource
        nested_name = e05.NESTED_MAPPER_JAR if nested_name is None else nested_name
        resource_name = e05.RESOURCE_PATH if resource_name is None else resource_name
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(resource_name, resource)
        boot = io.BytesIO()
        with zipfile.ZipFile(boot, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('META-INF/MANIFEST.MF', 'Start-Class: fixture.Main\n')
            archive.writestr(nested_name, nested.getvalue())
        return boot.getvalue()

    def rebuild_release(self, resource=None, nested_name=None, resource_name=None,
                        record_overrides=None, receipt_overrides=None, root_entries=(), source_branch="develop"):
        jar = self.build_jar(resource, nested_name, resource_name)
        canonical = self.root / 'service/cyf-api-kit.jar'
        canonical.write_bytes(jar)
        canonical.chmod(0o600)
        provenance = encoded({'fixture': True})
        flow = {
            'organization_id': e05.EXPECTED_ORG,
            'pipeline_id': e05.EXPECTED_PIPELINE,
            'job_id': e05.EXPECTED_JOB,
            'run_id': self.run_id,
            'source_tip_sha': self.commit,
        }
        source = {
            'branch': source_branch, 'commit_sha': self.commit, 'tree_sha': self.tree,
            'clean_before': True, 'clean_after': True,
        }
        identity = digest(encoded({'flow': flow, 'source': source}))
        records = [
            {'kind': 'application_jar', 'path': 'application.jar',
             'sha256': digest(jar), 'size': len(jar)},
            {'kind': 'dependency_provenance', 'path': 'dependency.provenance.json',
             'sha256': digest(provenance), 'size': len(provenance)},
        ]
        receipt = {
            'schema_version': 1, 'status': 'success', 'gradle_exit_code': 0,
            'bridge_exit_code': 0, 'ticket_sha256': identity,
            'flow': flow, 'source': source, 'files': records,
        }
        if receipt_overrides:
            receipt.update(receipt_overrides)
        receipt_bytes = encoded(receipt)
        metadata = encoded({'fixture': 'metadata'})
        sidecar = encoded({'fixture': 'sidecar'})
        members = {
            'application.jar': jar,
            'application.metadata.json': metadata,
            'application.sidecar.json': sidecar,
            'dependency.provenance.json': provenance,
            'receipt.json': receipt_bytes,
        }
        package = self.root / 'state/incoming/package.tgz'
        with tarfile.open(str(package), 'w:gz') as archive:
            for name, kind, size in root_entries:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.size = size
                archive.addfile(info, io.BytesIO(b'x' * size) if size else None)
            for name, value in members.items():
                info = tarfile.TarInfo(name)
                info.size = len(value)
                archive.addfile(info, io.BytesIO(value))
        package.chmod(0o600)
        record = {
            'schema_version': 2, 'status': 'installed', 'phase': 'installed',
            'recovery': 'not_required', 'ticket_sha256': identity,
            'source_commit_sha': self.commit, 'source_tree_sha': self.tree,
            'run_id': self.run_id, 'receipt_sha256': digest(receipt_bytes),
            'candidate_sha256': digest(jar), 'previous_sha256': 'c' * 64,
            'backup': '/home/isp/state/cyf-api-flow/backups/fixture.jar',
            'candidate_stop_rc': 0, 'timestamp': '20260913T000000Z',
        }
        if record_overrides:
            record.update(record_overrides)
        record_path = self.root / 'state/record.json'
        record_path.write_bytes(encoded(record))
        record_path.chmod(0o600)

    def execute(self, *args):
        result = subprocess.run(
            [str(RUNNER)] + list(args), env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=20,
        )
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(result.stdout)

    def assert_no_secret_disclosure(self, result, payload):
        combined = result.stdout + result.stderr + json.dumps(payload)
        self.assertNotIn(self.secret, combined)
        args_path = self.root / 'mysql-args.json'
        if args_path.exists():
            args_text = args_path.read_text()
            self.assertNotIn(self.secret, args_text)
            args = json.loads(args_text)
            self.assertIn('--database=jia', args)
            self.assertIn('--user=cyf_e05_schema_runner', args)
            self.assertNotIn('--database=attacker_database', args)
            self.assertFalse(any('password' in value.lower() for value in args))
        self.assertNotIn(self.secret, (self.root / 'fake-state.json').read_text())

    def test_create_resource_has_no_business_checks(self):
        self.assertNotIn(b'CHECK (', e05.E05_SQL_BYTES)
        for table in e05.TABLE_ORDER:
            self.assertEqual(e05.EXPECTED_TABLES[table]['checks'], {})

    def test_default_plan_is_read_only_and_binds_exact_nested_resource(self):
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(payload['operation'], 'plan')
        self.assertEqual(payload['candidate']['resource_outer'], e05.NESTED_MAPPER_JAR)
        self.assertEqual(payload['candidate']['resource_inner'], e05.RESOURCE_PATH)
        self.assertEqual(payload['candidate']['sql_sha256'], e05.RESOURCE_SHA256)
        self.assertEqual(payload['binding']['run'], self.run_id)
        self.assertNotIn('source', payload)
        self.assertNotIn('activation', json.dumps(payload).lower())
        self.assertEqual(self.read_state()['creates'], [])
        self.assertTrue(all(value['status'] == 'planned_create'
                            for value in payload['tables'].values()))
        self.assert_no_secret_disclosure(result, payload)

    def test_flow_empty_root_directory_is_allowed_without_weakening_payload_allowlist(self):
        self.rebuild_release(root_entries=(('.', tarfile.DIRTYPE, 0),))
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(self.read_state()['creates'], [])

    def test_archive_root_is_not_a_link_duplicate_or_extra_directory(self):
        cases = [
            (('.', tarfile.SYMTYPE, 0),),
            (('.', tarfile.DIRTYPE, 0), ('./', tarfile.DIRTYPE, 0)),
            (('unexpected', tarfile.DIRTYPE, 0),),
            (('unexpected-link', tarfile.SYMTYPE, 0),),
            (('.', tarfile.DIRTYPE, 1),),
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                self.rebuild_release(root_entries=entries)
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'package_member_invalid')
                self.assertEqual(self.read_state()['creates'], [])

    def test_apply_creates_only_the_exact_e05_table_and_verifies_equivalence(self):
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(payload['transaction_model'],
                         'mysql_ddl_autocommit_per_create_no_rollback_or_drop')
        self.assertEqual(payload['lock_order'],
                         ['e05_runner_file_lock', 'e05_mysql_named_lock'])
        self.assertEqual(self.read_state()['creates'], ['agent_work_item_reassignment'])
        self.assertEqual(payload['tables']['agent_work_item_reassignment']['status'],
                         'created_equivalent')
        self.assert_no_secret_disclosure(result, payload)

    def test_fixed_feature_branch_is_accepted_without_recreating_tables(self):
        self.rebuild_release(source_branch='codex/juyiting-event-api-20261102')
        self.state['tables'] = {table: 'equivalent' for table in e05.TABLE_ORDER}
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(self.read_state()['creates'], [])

    def test_branch_provenance_change_without_identity_rebinding_is_rejected(self):
        self.rebuild_release(receipt_overrides={'source': {
            'branch': 'codex/unbound-branch', 'commit_sha': self.commit,
            'tree_sha': self.tree, 'clean_before': True, 'clean_after': True}})
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'release_identity_digest_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_equivalent_existing_table_is_not_blindly_repeated(self):
        table = e05.TABLE_ORDER[0]
        self.state['tables'][table] = 'equivalent'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_state()['creates'], [])
        self.assertEqual(payload['tables'][table]['status'], 'existing_equivalent')

    def test_all_requested_schema_facets_are_fail_closed_before_create(self):
        cases = {
            'column_drift': 'columns',
            'nullable_drift': 'columns',
            'default_drift': 'columns',
            'engine_drift': 'engine',
            'collation_drift': 'table_collation',
            'charset_drift': 'column_charset',
            'column_collation_drift': 'column_collation',
            'index_drift': 'indexes',
            'index_attributes_drift': 'index_attributes',
            'constraint_drift': 'constraints',
        }
        table = e05.TABLE_ORDER[0]
        for state_name, mismatch in cases.items():
            with self.subTest(state=state_name):
                self.state['tables'][table] = state_name
                self.state['creates'] = []
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertIn(mismatch, payload['tables'][table]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])

    def test_explicit_utf8mb4_is_independent_of_schema_charset_but_not_session_collation(self):
        table = e05.TABLE_ORDER[0]
        self.state['schema_rows'] = [[hx('latin1'), hx('latin1_swedish_ci')]]
        self.state['tables'][table] = 'equivalent'
        self.write_state()
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, payload)
        for collation in ('utf8mb4_general_ci', 'utf8mb4_bin'):
            with self.subTest(collation=collation):
                self.state['expected'][table] = expected_rows(table, collation)
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('table_collation', payload['tables'][table]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])
        self.state['default_rows'] = [[hx('utf8mb4_general_ci')]]
        self.state['expected'][table] = expected_rows(table, 'utf8mb4_general_ci')
        self.write_state()
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, payload)

    def test_create_only_zero_columns_use_complete_synthetic_show_after_single_create(self):
        table = e05.TABLE_ORDER[0]
        self.state['expected'][table]['COLUMNS'] = []
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload['tables'][table]['status'], 'created_equivalent')
        self.assertEqual(self.read_state()['creates'], [table])
        self.assertEqual(self.read_state()['grants'], E05_CREATE_GRANTS)
        self.assert_no_secret_disclosure(result, payload)

    def test_existing_zero_columns_use_show_without_recreate_but_partial_columns_fail(self):
        table = e05.TABLE_ORDER[0]
        self.state['show_rows'] = copy.deepcopy(CURRENT_OWNER_E05_SHOW_ROWS)
        full = copy.deepcopy(self.state['expected'][table]['COLUMNS'])
        self.state['tables'][table] = 'equivalent'
        self.state['expected'][table]['COLUMNS'] = []
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload['tables'][table]['status'], 'existing_equivalent')
        self.assertEqual(self.read_state()['creates'], [])
        for columns in (full[:1], full[:-1]):
            with self.subTest(columns=len(columns)):
                self.state['expected'][table]['COLUMNS'] = columns
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertIn('columns', payload['tables'][table]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])

    def test_missing_or_inaccessible_show_blocks_existing_table_before_ddl(self):
        table = e05.TABLE_ORDER[0]
        self.state['tables'][table] = 'equivalent'
        self.state['expected'][table]['COLUMNS'] = []
        for rows in ([], E05_SHOW_ROWS[:-1], E05_SHOW_ROWS[:1] + E05_SHOW_ROWS[2:]):
            with self.subTest(rows=len(rows)):
                self.state['show_rows'] = rows
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(payload['error'], ('show_create_metadata_invalid', 'show_create_schema_drift'))
                self.assertEqual(self.read_state()['creates'], [])
        self.state['metadata_error_tag'] = 'SHOWFIRST'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'metadata_visibility_show_create_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_zero_columns_without_show_after_create_is_durable_failure_not_pass_or_drop(self):
        table = e05.TABLE_ORDER[0]
        self.state['expected'][table]['COLUMNS'] = []
        self.state['show_rows'] = []
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'created_table_not_equivalent')
        self.assertEqual(payload['tables'][table]['status'], 'create_result_unknown')
        self.assertEqual(self.read_state()['creates'], [table])
        self.assertEqual(self.read_state()['tables'][table], 'equivalent')

    def test_show_preserves_e05_columns_indexes_and_nullability(self):
        table = e05.TABLE_ORDER[0]
        columns = e05.parse_show_create(CURRENT_OWNER_E05_SHOW_ROWS, table, self.collation)
        self.assertEqual(len(columns), 26)
        self.assertEqual(tuple(col[1:6] for col in columns), e05.EXPECTED_TABLES[table]['columns'])
        changes = [
            ('`id` bigint', '`id` int'), ('varchar(100) NOT NULL', 'varchar(100) DEFAULT NULL'),
            ('NOT NULL AUTO_INCREMENT', 'NOT NULL'),
            ('varchar(100) NOT NULL', "varchar(100) NOT NULL DEFAULT 'evil'"),
            ('varchar(100) NOT NULL', 'varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL'),
            ('char(64) NOT NULL', 'char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL'),
            ('UNIQUE KEY `uk_', 'KEY `uk_'), ('`tenant_id`,`client_id`', '`task_id`,`client_id`'),
            ('ENGINE=InnoDB', 'ENGINE=MyISAM'), ('CHARSET=utf8mb4', 'CHARSET=utf8'),
            ('COLLATE=utf8mb4_0900_ai_ci', 'COLLATE=utf8mb4_bin'),
            ('(`id`)', '(`id`(1))'),
            ('NOT NULL AUTO_INCREMENT', 'NOT NULL AUTO_INCREMENT INVISIBLE'),
            ('NOT NULL AUTO_INCREMENT', 'NOT NULL AUTO_INCREMENT ON UPDATE 1'),
        ]
        for before, after in changes:
            with self.subTest(change=(before, after)):
                rows = [[value.replace(before, after) for value in row] for row in CURRENT_OWNER_E05_SHOW_ROWS]
                self.assertNotEqual(rows, CURRENT_OWNER_E05_SHOW_ROWS)
                with self.assertRaises(e05.SchemaError):
                    e05.parse_show_create(rows, table, self.collation)
        reordered = copy.deepcopy(CURRENT_OWNER_E05_SHOW_ROWS)
        reordered[1], reordered[2] = reordered[2], reordered[1]
        for rows in (reordered, CURRENT_OWNER_E05_SHOW_ROWS + [['trailing SQL']]):
            with self.assertRaises(e05.SchemaError):
                e05.parse_show_create(rows, table, self.collation)
        with self.assertRaises(e05.SchemaError):
            e05.parse_show_create(CURRENT_OWNER_E05_SHOW_ROWS, 'agent_task_artifact_outcome', self.collation)
        self.assertEqual(set(e05.SHOW_SQL), set(e05.TABLE_ORDER))

    def test_good_show_cannot_mask_information_schema_drift(self):
        table = e05.TABLE_ORDER[0]
        self.state['show_rows'] = copy.deepcopy(CURRENT_OWNER_E05_SHOW_ROWS)
        self.state['expected'][table]['COLUMNS'] = []
        for drift in ('index_drift', 'index_attributes_drift', 'constraint_drift', 'collation_drift'):
            with self.subTest(drift=drift):
                self.state['tables'][table] = drift
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertEqual(self.read_state()['creates'], [])

    def test_no_new_grants_required_but_wrong_scope_missing_create_and_query_failure_stop(self):
        for grants, error in [
                (E05_CREATE_GRANTS[:1], 'exact_table_create_privilege_required'),
                ([grant.replace('GRANT CREATE ', 'GRANT REFERENCES ') for grant in E05_CREATE_GRANTS],
                 'exact_table_create_privilege_required'),
                ([grant.replace('`jia`.`agent_work_item_reassignment`', '`jia`.*') for grant in E05_CREATE_GRANTS],
                 'metadata_privilege_scope_invalid'),
                ([grant.replace('cyf_e05_schema_runner', 'cyf_f06_schema_runner') for grant in E05_CREATE_GRANTS],
                 'metadata_privilege_scope_invalid')]:
            with self.subTest(grants=grants):
                self.state['grants'] = grants
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], error)
                self.assertEqual(self.read_state()['creates'], [])
        self.state['grants'] = list(E05_CREATE_GRANTS)
        self.state['metadata_error_tag'] = 'GRANTS'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'metadata_privilege_query_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_runner_file_lock_waits_without_backend_or_schema_mutation(self):
        lock_path = self.root / 'e05-runner.lock'
        lock_path.touch(mode=0o600)
        with lock_path.open('r+') as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            process = subprocess.Popen(
                [str(RUNNER)], env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            try:
                time.sleep(0.25)
                self.assertIsNone(process.poll())
                self.assertFalse((self.root / 'mysql-args.json').exists())
                self.assertEqual(self.read_state()['creates'], [])
            finally:
                fcntl.flock(held, fcntl.LOCK_UN)
            out, err = process.communicate(timeout=20)
        self.assertEqual(process.returncode, 0, out + err)
        self.assertEqual(json.loads(out)['status'], 'pass')

    def test_database_named_lock_denial_stops_before_metadata_or_ddl(self):
        self.state['db_lock_result'] = 0
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'database_lock_acquire_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_source_and_statement_catalog_are_closed_to_activation_and_other_sql(self):
        source = RUNNER.read_text()
        self.assertNotIn('/usr/local/sbin/cyf-api-kit', source)
        self.assertNotIn('/tmp/cyf-release-api.lock', source)
        self.assertNotIn('activation', source.lower())
        # Reading/parsing SHOW GRANTS is allowed, executing GRANT/REVOKE is not.
        for sql in list(e05.QUERY_SQL.values()) + list(e05.SHOW_SQL.values()):
            statement = re.sub(r'^/\*[^*]*\*/\s*', '', sql).upper()
            self.assertRegex(statement, r'^(SELECT|SHOW) ')
            self.assertNotIn(';', statement)
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, payload)
        for sql in self.read_state()['commands']:
            statement = re.sub(r'^/\*[^*]*\*/\s*', '', sql).upper()
            self.assertRegex(statement, r'^(SELECT |SHOW |CREATE TABLE IF NOT EXISTS AGENT_WORK_ITEM_REASSIGNMENT )')
            self.assertNotRegex(statement, r'^(GRANT|REVOKE|DROP|ALTER|INSERT|UPDATE|DELETE) ')

        statements = e05.split_exact_statements(e05.E05_SQL_BYTES)
        self.assertEqual(set(statements), {'agent_work_item_reassignment'})
        statement = statements['agent_work_item_reassignment']
        self.assertRegex(statement, r'^CREATE TABLE IF NOT EXISTS agent_work_item_reassignment ')
        for forbidden in (' ALTER ', ' DROP ', ' INSERT ', ' UPDATE ', ' DELETE ',
                          ' REPLACE ', ' GRANT ', ' TRUNCATE '):
            self.assertNotIn(forbidden, ' ' + statement.upper() + ' ')
        self.assertEqual(digest(e05.E05_SQL_BYTES),
                         '3c287315e1d6126c652b219e6b4f14ebf02546ee7458c5d6abc3bf46e46b048c')

    def test_create_backend_failure_is_reported_preserved_and_retryable(self):
        table = e05.TABLE_ORDER[0]
        self.state['create_fail_on'] = table
        self.write_state()
        first_result, first_payload = self.execute('--apply')
        self.assertNotEqual(first_result.returncode, 0)
        self.assertEqual(first_payload['error'], 'create_statement_failed')
        self.assertEqual(first_payload['failed_table'], table)
        self.assertEqual(first_payload['tables'][table]['status'],
                         'create_backend_error_absent')
        after_first = self.read_state()
        self.assertEqual(after_first['tables'][table], 'absent')
        self.assertEqual(after_first['creates'], [table])

        del after_first['create_fail_on']
        after_first['creates'] = []
        self.state = after_first
        self.write_state()
        second_result, second_payload = self.execute('--apply')
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        self.assertEqual(self.read_state()['creates'], [table])
        self.assertEqual(second_payload['tables'][table]['status'], 'created_equivalent')

    def test_post_create_drift_is_preserved_and_never_dropped(self):
        table = e05.TABLE_ORDER[0]
        self.state['create_drift_on'] = table
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'created_table_not_equivalent')
        self.assertEqual(payload['failed_table'], table)
        state = self.read_state()
        self.assertEqual(state['tables'][table], 'column_drift')
        self.assertEqual(state['creates'], [table])
        self.assertNotIn('DROP TABLE', RUNNER.read_text().upper())

    def test_metadata_query_error_stops_before_ddl(self):
        self.state['metadata_error_tag'] = 'COLUMNS'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'metadata_query_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_resource_with_extra_drop_is_rejected_even_when_receipt_matches_jar(self):
        self.rebuild_release(resource=self.resource + b'\nDROP TABLE forbidden;\n')
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'e05_resource_digest_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())
        self.assertEqual(self.read_state()['creates'], [])

    def test_wrong_nested_module_or_resource_location_is_rejected(self):
        cases = [
            ({'nested_name': 'BOOT-INF/lib/not-the-mapper.jar'},
             'mapper_jar_location_invalid'),
            ({'resource_name': 'db/not-e05.sql'}, 'e05_resource_location_invalid'),
        ]
        for kwargs, error in cases:
            with self.subTest(error=error):
                self.rebuild_release(**kwargs)
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], error)
                self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_installed_record_receipt_source_tree_and_canonical_jar_are_bound(self):
        cases = [
            ({'record_overrides': {'run_id': '45'}}, 'receipt_release_identity_mismatch'),
            ({'record_overrides': {'source_tree_sha': 'c' * 40}},
             'receipt_release_identity_mismatch'),
            ({'record_overrides': {'status': 'activation'}},
             'record_not_installed_exact_release'),
            ({'receipt_overrides': {'status': 'activation'}},
             'receipt_release_identity_mismatch'),
        ]
        for kwargs, error in cases:
            with self.subTest(error=error):
                self.rebuild_release(**kwargs)
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], error)
                self.assertFalse((self.root / 'mysql-args.json').exists())
        self.rebuild_release()
        canonical = self.root / 'service/cyf-api-kit.jar'
        canonical.write_bytes(self.build_jar() + b'changed')
        canonical.chmod(0o600)
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'canonical_release_binding_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_artifact_archive_has_exact_five_files_plus_optional_empty_root_only(self):
        self.rebuild_release(root_entries=(('.', tarfile.DIRTYPE, 0),
                                           ('extra', tarfile.REGTYPE, 1)))
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'package_member_set_invalid')
        self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_arbitrary_cli_payload_is_rejected_without_touching_backend(self):
        for args in (('--apply', '--database=evil'), ('--source=activation',), ('--plan',)):
            with self.subTest(args=args):
                result, payload = self.execute(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(payload['error'], 'arguments_rejected')
                self.assertFalse((self.root / 'mysql-args.json').exists())
                self.assertEqual(self.read_state()['creates'], [])

    def test_missing_or_multiline_password_fails_without_starting_mysql(self):
        for value in (None, '', 'line1\nline2', 'line1\rline2'):
            with self.subTest(value=value):
                if value is None:
                    self.env.pop('CYF_E05_MYSQL_PASSWORD', None)
                else:
                    self.env['CYF_E05_MYSQL_PASSWORD'] = value
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'mysql_password_environment_missing')
                self.assertFalse((self.root / 'mysql-args.json').exists())


    def test_preservation_e05_fixed_create_bytes_and_owner_extension_are_both_required(self):
        self.assertEqual(e05.RESOURCE_SHA256,
                         '3c287315e1d6126c652b219e6b4f14ebf02546ee7458c5d6abc3bf46e46b048c')
        self.assertEqual(digest(e05.E05_SQL_BYTES), e05.RESOURCE_SHA256)
        self.assertIn(b"owner_jiacn                  VARCHAR(50) NOT NULL COMMENT 'Authenticated task owner'", e05.E05_SQL_BYTES)
        spec = e05.EXPECTED_TABLES[e05.TABLE_ORDER[0]]
        self.assertIn(('owner_jiacn', 'varchar(50)', 'NO', None, ''), spec['columns'])
        self.assertIn(e05.index('idx_agent_work_item_reassignment_owner_scope', False,
                      ('tenant_id', 'client_id', 'owner_jiacn', 'task_id', 'work_item_id')),
                      spec['indexes'])

    def test_preservation_ownerless_historical_create_show_cannot_be_current_success(self):
        with self.assertRaises(e05.SchemaError):
            e05.parse_show_create(E05_SHOW_ROWS, e05.TABLE_ORDER[0], self.collation)

    def test_preservation_complete_current_owner_show_is_synthetic_only_and_exact(self):
        text = E05_SHOW_TEXT.replace('  PRIMARY KEY (`id`),',
                                    "  `owner_jiacn` varchar(50) NOT NULL COMMENT 'Authenticated task owner',\n  PRIMARY KEY (`id`),")
        needle = '  CONSTRAINT `chk_work_item_reassignment_agents`'
        text = text.replace(needle,
            '  KEY `idx_agent_work_item_reassignment_owner_scope` '
            '(`tenant_id`,`client_id`,`owner_jiacn`,`task_id`,`work_item_id`),\n' + needle)
        rows = [[e05.TABLE_ORDER[0], text.splitlines()[0]]] + [[line] for line in text.splitlines()[1:]]
        parsed = e05.parse_show_create(rows, e05.TABLE_ORDER[0], self.collation)
        self.assertEqual(len(parsed), 26)
        self.assertEqual(tuple(col[1:6] for col in parsed),
                         e05.EXPECTED_TABLES[e05.TABLE_ORDER[0]]['columns'])
        no_owner_index = [row for row in rows if not row[0].startswith('  KEY `idx_agent_work_item_reassignment_owner_scope`')]
        with self.assertRaises(e05.SchemaError):
            e05.parse_show_create(no_owner_index, e05.TABLE_ORDER[0], self.collation)

    def test_preservation_missing_mandatory_owner_index_stops_before_create(self):
        table = e05.TABLE_ORDER[0]
        self.state['tables'][table] = 'equivalent'
        rows = self.state['expected'][table]['STATISTICS']
        rows[:] = [row for row in rows if row[1] != hx('idx_agent_work_item_reassignment_owner_scope')]
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'existing_schema_drift')
        self.assertEqual(self.read_state()['creates'], [])


    def test_oracle_sync_bare_create_cannot_satisfy_current_owner_guard(self):
        # Frozen ownerless historical input still cannot satisfy the current
        # contract. The new CREATE is owner-complete; an ownerless readback
        # remains a durable unknown-result failure, never repaired or inferred.
        table = e05.TABLE_ORDER[0]
        self.assertEqual(digest(LEGACY_OWNERLESS_SQL_BYTES),
                         LEGACY_OWNERLESS_SQL_SHA256)
        self.assertNotIn(b'owner_jiacn', LEGACY_OWNERLESS_SQL_BYTES)
        self.assertIn(('owner_jiacn', 'varchar(50)', 'NO', None, ''),
                      e05.EXPECTED_TABLES[table]['columns'])
        self.state['expected'][table]['COLUMNS'] = []
        self.state['show_rows'] = copy.deepcopy(E05_SHOW_ROWS)
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'created_table_not_equivalent')
        self.assertEqual(payload['tables'][table]['status'], 'create_result_unknown')
        self.assertEqual(self.read_state()['creates'], [table])
        for statement in self.read_state()['commands']:
            self.assertNotRegex(statement.upper(), r'^(ALTER|DROP|UPDATE|INSERT|DELETE) ')
        self.assert_no_secret_disclosure(result, payload)

    def test_same_batch_owner_create_show_and_historical_input_are_distinct(self):
        self.assertEqual(digest(LEGACY_OWNERLESS_SQL_BYTES), LEGACY_OWNERLESS_SQL_SHA256)
        self.assertNotEqual(LEGACY_OWNERLESS_SQL_BYTES, e05.E05_SQL_BYTES)
        self.assertNotIn(b'owner_jiacn', LEGACY_OWNERLESS_SQL_BYTES)
        statements = e05.split_exact_statements(e05.E05_SQL_BYTES)
        self.assertEqual(tuple(statements), e05.TABLE_ORDER)
        self.assertIn('owner_jiacn VARCHAR(50) NOT NULL', statements[e05.TABLE_ORDER[0]])
        self.assertIn('idx_agent_work_item_reassignment_owner_scope', statements[e05.TABLE_ORDER[0]])
        metadata = e05.parse_show_create(CURRENT_OWNER_E05_SHOW_ROWS, e05.TABLE_ORDER[0], self.collation)
        self.assertIn('owner_jiacn', [value[1] for value in metadata])
        with self.assertRaises(e05.SchemaError):
            e05.parse_show_create(E05_SHOW_ROWS, e05.TABLE_ORDER[0], self.collation)

    def test_frozen_old_ownerless_artifact_rejected_before_mysql(self):
        self.rebuild_release(resource=LEGACY_OWNERLESS_SQL_BYTES)
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'e05_resource_digest_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())
        self.assertEqual(self.read_state()['creates'], [])
        self.assert_no_secret_disclosure(result, payload)



class LocalSchemaInstalledBindingSourceTest(unittest.TestCase):
    """LOCAL grammar with actual installed-fixture bytes, not live DB acceptance."""
    def setUp(self):
        from test_api_gate_policy import ApiLocalSharedInstallerSourceTest
        from unittest.mock import patch
        self.fixture = ApiLocalSharedInstallerSourceTest(); self.fixture.setUp()
        self.deploy = self.fixture.deploy
        self.inputs = self.fixture.inputs
        for entry in self.inputs.schema['entries']:
            from test_api_additive_schema import f06
            from test_api_e05_additive_schema import e05
            source = f06 if entry['feature'] == 'F06' else e05
            entry['expectedCatalogSha256'] = digest(self.deploy.local_canonical(source.EXPECTED_TABLES))
        self.inputs.seal(); self.fixture.stage()
        result = self.fixture.install(); self.assertEqual(result.returncode, 0, result.stderr)
        self.paths = {'record': self.fixture.fixture.root / 'state/record.json',
                      'package': self.fixture.fixture.root / 'state/incoming/package.tgz',
                      'jar': self.fixture.fixture.target}
        self.modes = {'record': 0o600, 'package': 0o600, 'jar': 0o640}
        self.patch = patch.object(e05, 'local_coordinator_validator', return_value=self.deploy.__dict__)
        self.patch.start()

    def tearDown(self):
        self.patch.stop(); self.fixture.tearDown()

    def verify(self):
        return e05.verify_release_binding(self.paths, os.geteuid(), self.modes)

    def test_v3_consumed_installed_record_has_typed_source_no_fake_flow_identity(self):
        binding = self.verify()
        self.assertEqual(binding['source'], self.inputs.decision['source'])
        self.assertEqual(binding['binding_sha256'], self.deploy.local_binding_sha(self.fixture.binding))
        self.assertEqual(binding['expected_catalog_sha256'], digest(self.deploy.local_canonical(e05.EXPECTED_TABLES)))
        self.assertNotIn('run', binding)
        e05.assert_binding_paths_unchanged(self.paths, os.geteuid(), self.modes, binding, full_digest=True)

    def test_v3_installed_record_cannot_substitute_different_package(self):
        self.paths['package'].write_bytes(b'wrong incoming after installation')
        with self.assertRaises(e05.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_package_invalid')

    def test_v3_unconsumed_approval_cannot_authorize_schema(self):
        path = self.paths['record'].parent / 'approval.json'
        approval = json.loads(path.read_text()); approval.update(consumed=False, consumed_at=None)
        path.write_bytes(self.deploy.local_canonical(approval))
        with self.assertRaises(e05.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_recovery_binding_mismatch')

    def test_v3_noninstalled_phase_cannot_authorize_schema(self):
        record = json.loads(self.paths['record'].read_text()); record.update(status='active_pending', phase='commit')
        self.paths['record'].write_bytes(self.deploy.local_canonical(record))
        with self.assertRaises(e05.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_durable_record_incomplete')

    def test_v3_immutable_inputs_are_rechecked_before_original_ddl_boundary(self):
        binding = self.verify()
        Path(self.inputs.decision['precondition']['schemaInventory']['path']).write_bytes(b'changed schema observation')
        with self.assertRaises(e05.SchemaError) as error:
            e05.assert_binding_paths_unchanged(self.paths, os.geteuid(), self.modes, binding)
        self.assertEqual(error.exception.code, 'local_immutable_input_changed')

if __name__ == '__main__':
    unittest.main()
