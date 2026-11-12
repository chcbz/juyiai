"""Offline-only adversarial tests for the exact F06 additive schema runner."""
import copy
import fcntl
import hashlib
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-additive-schema'
loader = importlib.machinery.SourceFileLoader('cyf_f06_schema_runner_test_module', str(RUNNER))
f06 = loader.load_module()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def hx(value):
    return value.encode('utf-8').hex().upper()


def optional(value):
    return '-' if value is None else '+' + hx(str(value))


def expected_rows(table, collation):
    spec = f06.EXPECTED_TABLES[table]
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
        # Exercise the parser against normal MySQL quoting/charset decoration.
        mysql_clause = clause.replace('outcome_state', '`outcome_state`')
        mysql_clause = mysql_clause.replace("'accepted'", "_utf8mb4'accepted'")
        mysql_clause = mysql_clause.replace("'superseded'", "_utf8mb4'superseded'")
        rows['CHECKS'].append([hx(table), hx(name), hx(mysql_clause)])
    return rows


def synthetic_show_rows(table, collation):
    """Offline ONLY: model SHOW for the uncreated table; not live evidence."""
    spec = f06.EXPECTED_TABLES[table]
    lines = []
    for name, sql_type, nullable, default, extra in spec['columns']:
        assert default is None
        lines.append('  `%s` %s %s%s' % (
            name, sql_type, 'NOT NULL' if nullable == 'NO' else 'DEFAULT NULL',
            ' AUTO_INCREMENT' if extra == 'auto_increment' else ''))
    for name, non_unique, columns, kind in spec['indexes']:
        prefix = ('PRIMARY KEY' if name == 'PRIMARY' else
                  ('KEY' if non_unique else 'UNIQUE KEY') + ' `%s`' % name)
        lines.append('  %s (%s)' % (prefix, ','.join('`%s`' % col for col in columns)))
    for name, clause in sorted(spec['checks'].items()):
        lines.append('  CONSTRAINT `%s` CHECK (%s)' % (name, ' '.join(clause.split())))
    return ([[table, 'CREATE TABLE `%s` (' % table]] +
            [[line + (',' if at < len(lines) - 1 else '')] for at, line in enumerate(lines)] +
            [[') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=' + collation]])


# Literal read-only Run49 observation, MySQL 8.0.21; no observed columns.
# /var/tmp/cyf-f06-run49-metadata-diagnostic/metadata.json SHA256:
# f8846b038a27a2ecbb40b2fb74f8314ded59f74d18963f26cf24cc405d2f9f81
RUN49_METADATA = {'checks': {'agent_task_artifact_outcome': {'chk_artifact_outcome_digest': '(char_length(`decision_digest`) = 64)',
                                            'chk_artifact_outcome_state': '(`outcome_state` in '
                                                                          "(_utf8mb4\\'accepted\\',_utf8mb4\\'superseded\\'))",
                                            'chk_artifact_outcome_supersession': "(((`outcome_state` = _utf8mb4\\'accepted\\') and "
                                                                                 '(`superseded_by_artifact_id` is null) and '
                                                                                 '(`superseded_by_artifact_version` is null)) or '
                                                                                 "((`outcome_state` = _utf8mb4\\'superseded\\') and "
                                                                                 '(`superseded_by_artifact_id` is not null) and '
                                                                                 '(`superseded_by_artifact_version` >= 1) and '
                                                                                 '((`artifact_id` <> `superseded_by_artifact_id`) or '
                                                                                 '(`artifact_version` <> '
                                                                                 '`superseded_by_artifact_version`))))',
                                            'chk_artifact_outcome_versions': '((`artifact_version` >= 1) and (`version` >= 1) and '
                                                                             '(`decided_at` > 0))'},
            'agent_task_artifact_outcome_decision': {}},
 'columns': {'agent_task_artifact_outcome': [], 'agent_task_artifact_outcome_decision': []},
 'constraints': {'agent_task_artifact_outcome': {'PRIMARY': ['PRIMARY KEY', 'YES'],
                                                 'chk_artifact_outcome_digest': ['CHECK', 'YES'],
                                                 'chk_artifact_outcome_state': ['CHECK', 'YES'],
                                                 'chk_artifact_outcome_supersession': ['CHECK', 'YES'],
                                                 'chk_artifact_outcome_versions': ['CHECK', 'YES'],
                                                 'uk_artifact_outcome_version': ['UNIQUE', 'YES']},
                 'agent_task_artifact_outcome_decision': {}},
 'indexes': {'agent_task_artifact_outcome': {'PRIMARY': [[0, 1, 'id', None, 'BTREE', 'A', 'YES']],
                                             'idx_artifact_outcome_decision': [[1, 1, 'tenant_id', None, 'BTREE', 'A', 'YES'],
                                                                               [1, 2, 'client_id', None, 'BTREE', 'A', 'YES'],
                                                                               [1, 3, 'task_id', None, 'BTREE', 'A', 'YES'],
                                                                               [1, 4, 'decision_id', None, 'BTREE', 'A', 'YES'],
                                                                               [1, 5, 'id', None, 'BTREE', 'A', 'YES']],
                                             'idx_artifact_outcome_superseded_by': [[1, 1, 'tenant_id', None, 'BTREE', 'A', 'YES'],
                                                                                    [1, 2, 'client_id', None, 'BTREE', 'A', 'YES'],
                                                                                    [1, 3, 'task_id', None, 'BTREE', 'A', 'YES'],
                                                                                    [1, 4, 'superseded_by_artifact_id', None, 'BTREE', 'A',
                                                                                     'YES'],
                                                                                    [1, 5, 'superseded_by_artifact_version', None, 'BTREE',
                                                                                     'A', 'YES']],
                                             'idx_artifact_outcome_task_state': [[1, 1, 'tenant_id', None, 'BTREE', 'A', 'YES'],
                                                                                 [1, 2, 'client_id', None, 'BTREE', 'A', 'YES'],
                                                                                 [1, 3, 'task_id', None, 'BTREE', 'A', 'YES'],
                                                                                 [1, 4, 'outcome_state', None, 'BTREE', 'A', 'YES'],
                                                                                 [1, 5, 'decided_at', None, 'BTREE', 'A', 'YES'],
                                                                                 [1, 6, 'id', None, 'BTREE', 'A', 'YES']],
                                             'uk_artifact_outcome_version': [[0, 1, 'tenant_id', None, 'BTREE', 'A', 'YES'],
                                                                             [0, 2, 'client_id', None, 'BTREE', 'A', 'YES'],
                                                                             [0, 3, 'artifact_id', None, 'BTREE', 'A', 'YES'],
                                                                             [0, 4, 'artifact_version', None, 'BTREE', 'A', 'YES']]},
             'agent_task_artifact_outcome_decision': {}},
 'schema_charset': 'utf8',
 'schema_collation': 'utf8_general_ci',
 'tables': {'agent_task_artifact_outcome': ['innodb', 'utf8mb4_0900_ai_ci']}}
RUN49_GRANTS = ['GRANT USAGE ON *.* TO `cyf_f06_schema_runner`@`localhost`',
 'GRANT CREATE ON `jia`.`agent_task_artifact_outcome_decision` TO `cyf_f06_schema_runner`@`localhost`',
 'GRANT CREATE ON `jia`.`agent_task_artifact_outcome` TO `cyf_f06_schema_runner`@`localhost`']


# Actual CREATE-only SHOW readback; SHA256 of shared show-create.json:
# 08aab10b81368ab50f8f03002ea89b758110cbba6e725588420a7c56d11bf6c3
RUN49_SHOW_ROWS = [['agent_task_artifact_outcome', 'CREATE TABLE `agent_task_artifact_outcome` ('],
 ["  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Primary key',"],
 ["  `task_id` varchar(100) NOT NULL COMMENT 'Task ID copied for exact scope fencing',"],
 ["  `artifact_id` varchar(100) NOT NULL COMMENT 'Stable logical artifact ID',"],
 ["  `artifact_version` int NOT NULL COMMENT 'Exact immutable artifact version',"],
 ["  `outcome_state` varchar(20) NOT NULL COMMENT 'accepted/superseded',"],
 ["  `superseded_by_artifact_id` varchar(100) DEFAULT NULL COMMENT 'Accepted replacement artifact ID',"],
 ["  `superseded_by_artifact_version` int DEFAULT NULL COMMENT 'Accepted replacement artifact version',"],
 ["  `decision_id` varchar(100) NOT NULL COMMENT 'Caller supplied scoped idempotency identity',"],
 ["  `decision_digest` char(64) NOT NULL COMMENT 'Canonical SHA-256 of exact decision input',"],
 ["  `decided_by_agent_id` varchar(100) NOT NULL COMMENT 'Authorized coordinator/reviewer agent ID',"],
 ["  `decided_at` bigint NOT NULL COMMENT 'Decision time',"],
 ["  `version` bigint NOT NULL COMMENT 'Outcome optimistic lock version; implicit draft is zero',"],
 ["  `tenant_id` varchar(50) NOT NULL COMMENT 'Owner jiacn scope',"],
 ["  `client_id` varchar(50) NOT NULL COMMENT 'OAuth/API client scope',"],
 ["  `create_time` bigint DEFAULT NULL COMMENT 'Create time',"],
 ["  `update_time` bigint DEFAULT NULL COMMENT 'Last modified time',"], ['  PRIMARY KEY (`id`),'],
 ['  UNIQUE KEY `uk_artifact_outcome_version` (`tenant_id`,`client_id`,`artifact_id`,`artifact_version`),'],
 ['  KEY `idx_artifact_outcome_task_state` '
  '(`tenant_id`,`client_id`,`task_id`,`outcome_state`,`decided_at`,`id`),'],
 ['  KEY `idx_artifact_outcome_decision` (`tenant_id`,`client_id`,`task_id`,`decision_id`,`id`),'],
 ['  KEY `idx_artifact_outcome_superseded_by` '
  '(`tenant_id`,`client_id`,`task_id`,`superseded_by_artifact_id`,`superseded_by_artifact_version`),'],
 ['  CONSTRAINT `chk_artifact_outcome_digest` CHECK ((char_length(`decision_digest`) = 64)),'],
 ['  CONSTRAINT `chk_artifact_outcome_state` CHECK ((`outcome_state` in '
  "(_utf8mb4'accepted',_utf8mb4'superseded'))),"],
 ["  CONSTRAINT `chk_artifact_outcome_supersession` CHECK ((((`outcome_state` = _utf8mb4'accepted') and "
  '(`superseded_by_artifact_id` is null) and (`superseded_by_artifact_version` is null)) or '
  "((`outcome_state` = _utf8mb4'superseded') and (`superseded_by_artifact_id` is not null) and "
  '(`superseded_by_artifact_version` >= 1) and ((`artifact_id` <> `superseded_by_artifact_id`) or '
  '(`artifact_version` <> `superseded_by_artifact_version`))))),'],
 ['  CONSTRAINT `chk_artifact_outcome_versions` CHECK (((`artifact_version` >= 1) and (`version` >= 1) and '
  '(`decided_at` > 0)))'],
 [") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Scoped current "
  "accepted/superseded state for immutable task artifact versions'"]]


# Synthetic current-owner projection of historical SHOW spelling. The literal
# Run49 observation above remains unchanged and still proves ownerless rejection.
# Owner column/index scope is the fixed current F06 SQL and installed contract;
# this projection is NOT a new production SHOW readback.
def current_owner_show_rows():
    rows = copy.deepcopy(RUN49_SHOW_ROWS)
    primary = next(i for i, row in enumerate(rows) if row[0].startswith('  PRIMARY KEY'))
    rows.insert(primary, ["  `owner_jiacn` varchar(50) NOT NULL COMMENT 'Authenticated user owner scope',"])
    for row in rows:
        if row[0].startswith(('  UNIQUE KEY', '  KEY')):
            row[0] = row[0].replace('`tenant_id`,`client_id`',
                                    '`tenant_id`,`client_id`,`owner_jiacn`')
    return rows


CURRENT_OWNER_SHOW_ROWS = current_owner_show_rows()


FAKE_MYSQL = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
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
    marker = re.match(r"SELECT '(_CYF_F06_[0-9]{4}_END_)';$", statement)
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
    tag_match = re.search(r'/\*CYF_F06:([A-Z]+)\*/', statement)
    if tag_match:
        tag = tag_match.group(1)
        if state.get('metadata_error_tag') == tag:
            print('fixture metadata failure', file=sys.stderr, flush=True)
            continue
        if tag in ('SHOWFIRST', 'SHOWSECOND'):
            table = sorted(state['tables'])[0 if tag == 'SHOWFIRST' else 1]
            emit(state['show_rows'].get(table, []))
            continue
        if tag == 'GRANTS':
            emit([[value] for value in state['grants']])
            continue
        if tag == 'DEFAULTS':
            emit(state['default_rows'])
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
                table_rows[0][2] = state['hex_bad_check']
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


class ApiAdditiveSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-f06-schema-', dir='/tmp')
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        for name in ('service', 'state/incoming', 'bin'):
            (self.root / name).mkdir(parents=True, mode=0o700)
        self.mysql = self.root / 'bin/mysql'
        self.mysql.write_text(FAKE_MYSQL)
        self.mysql.chmod(0o700)
        self.collation = 'utf8mb4_0900_ai_ci'
        expected = {table: expected_rows(table, self.collation) for table in f06.TABLE_ORDER}
        self.state = {
            'schema_rows': [[hx('utf8'), hx('utf8_general_ci')]],
            'default_rows': [[hx(self.collation)]],
            'grants': list(RUN49_GRANTS),
            'show_rows': {},
            'expected': expected,
            'tables': {table: 'absent' for table in f06.TABLE_ORDER},
            'creates': [],
            'hex_int': hx('int'),
            'hex_yes': hx('YES'),
            'hex_no': hx('NO'),
            'hex_myisam': hx('MyISAM'),
            'hex_other_collation': hx('utf8mb4_bin'),
            'hex_bad_check': hx('1 = 1'),
        }
        self.write_state()
        self.commit = 'a' * 40
        self.tree = 'b' * 40
        self.run_id = '39'
        self.resource = f06.F06_SQL_BYTES
        self.rebuild_release()
        self.secret = 'offline-only-secret-value'
        self.env = dict(os.environ)
        self.env.update(
            CYF_F06_SCHEMA_OFFLINE_TEST='YES',
            CYF_F06_SCHEMA_TEST_ROOT=str(self.root),
            CYF_F06_MYSQL_PASSWORD=self.secret,
            # These must not influence the fixed target catalog.
            CYF_F06_DATABASE='attacker_database',
            CYF_F06_SCHEMA='attacker_schema',
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
        nested_name = f06.NESTED_MAPPER_JAR if nested_name is None else nested_name
        resource_name = f06.RESOURCE_PATH if resource_name is None else resource_name
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
            'organization_id': f06.EXPECTED_ORG,
            'pipeline_id': f06.EXPECTED_PIPELINE,
            'job_id': f06.EXPECTED_JOB,
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
            self.assertIn('--user=cyf_f06_schema_runner', args)
            self.assertNotIn('--database=attacker_database', args)
            self.assertFalse(any('password' in value.lower() for value in args))
        self.assertNotIn(self.secret, (self.root / 'fake-state.json').read_text())

    def test_create_resource_has_no_business_checks(self):
        self.assertNotIn(b'CHECK (', f06.F06_SQL_BYTES)
        for table in f06.TABLE_ORDER:
            self.assertEqual(f06.EXPECTED_TABLES[table]['checks'], {})

    def test_default_plan_is_read_only_and_binds_exact_nested_resource(self):
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(payload['operation'], 'plan')
        self.assertEqual(payload['candidate']['resource_outer'], f06.NESTED_MAPPER_JAR)
        self.assertEqual(payload['candidate']['resource_inner'], f06.RESOURCE_PATH)
        self.assertEqual(payload['candidate']['sql_sha256'], f06.RESOURCE_SHA256)
        self.assertEqual(payload['binding']['run'], self.run_id)
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
            (('.', tarfile.DIRTYPE, 1),),
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                self.rebuild_release(root_entries=entries)
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'package_member_invalid')
                self.assertEqual(self.read_state()['creates'], [])

    def test_apply_creates_only_the_two_exact_tables_and_verifies_equivalence(self):
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload['status'], 'pass')
        self.assertEqual(self.read_state()['creates'], list(f06.TABLE_ORDER))
        self.assertTrue(all(value['status'] == 'created_equivalent'
                            for value in payload['tables'].values()))
        self.assert_no_secret_disclosure(result, payload)

    def test_fixed_feature_branch_is_accepted_without_recreating_tables(self):
        self.rebuild_release(source_branch='codex/juyiting-event-api-20261102')
        self.state['tables'] = {table: 'equivalent' for table in f06.TABLE_ORDER}
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

    def test_equivalent_existing_tables_are_not_blindly_repeated(self):
        self.state['tables'] = {table: 'equivalent' for table in f06.TABLE_ORDER}
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_state()['creates'], [])
        self.assertTrue(all(value['status'] == 'existing_equivalent'
                            for value in payload['tables'].values()))


    def test_all_requested_schema_facets_are_fail_closed(self):
        cases = {
            'nullable_drift': 'columns',
            'default_drift': 'columns',
            'engine_drift': 'engine',
            'collation_drift': 'table_collation',
            'index_drift': 'indexes',
            'constraint_drift': 'constraints',
        }
        for state_name, mismatch in cases.items():
            with self.subTest(state=state_name):
                self.state['tables'] = {table: 'absent' for table in f06.TABLE_ORDER}
                self.state['tables'][f06.TABLE_ORDER[0]] = state_name
                self.state['creates'] = []
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertIn(mismatch, payload['tables'][f06.TABLE_ORDER[0]]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])

    def use_run49_metadata(self, complete_synthetic_columns=False):
        # All visible metadata below is the real snapshot. Only the opt-in
        # positive case adds synthetic contract columns, NOT production evidence.
        metadata = copy.deepcopy(RUN49_METADATA)
        self.state['schema_rows'] = [[hx(metadata['schema_charset']), hx(metadata['schema_collation'])]]
        first = f06.TABLE_ORDER[0]
        self.state['tables'][first] = 'equivalent'
        self.state['show_rows'][first] = copy.deepcopy(RUN49_SHOW_ROWS)
        for table in f06.TABLE_ORDER:
            if table not in metadata['tables']:
                continue
            rows = self.state['expected'][table]
            rows['TABLES'] = []
            if table in metadata['tables']:
                engine, collation = metadata['tables'][table]
                rows['TABLES'] = [[hx(table), hx(engine), hx(collation)]]
            if not complete_synthetic_columns:
                rows['COLUMNS'] = []
            rows['CHECKS'] = [[hx(table), hx(name), hx(clause)]
                              for name, clause in sorted(metadata['checks'][table].items())]
            rows['CONSTRAINTS'] = [[hx(table), hx(name), hx(kind), hx(enforced)]
                                   for name, (kind, enforced) in
                                   sorted(metadata['constraints'][table].items())]
            rows['STATISTICS'] = []
            for name, entries in sorted(metadata['indexes'][table].items()):
                for non_unique, seq, col, sub, kind, direction, visible in entries:
                    rows['STATISTICS'].append([
                        hx(table), hx(name), str(non_unique), str(seq), hx(col),
                        '-' if sub is None else '+' + str(sub), hx(kind), hx(direction), hx(visible)])
        self.write_state()

    def use_current_owner_metadata(self, complete_synthetic_columns=False):
        # Retain the raw Run49 fixture in its original helper; this explicitly
        # synthetic current projection adds only mandatory owner index scope.
        self.use_run49_metadata(complete_synthetic_columns)
        first = f06.TABLE_ORDER[0]
        self.state['show_rows'][first] = copy.deepcopy(CURRENT_OWNER_SHOW_ROWS)
        indexes = copy.deepcopy(RUN49_METADATA['indexes'][first])
        for entries in indexes.values():
            if tuple(entry[2] for entry in entries[:2]) == ('tenant_id', 'client_id'):
                owner = list(entries[1])
                owner[2] = 'owner_jiacn'
                entries.insert(2, owner)
                for sequence, entry in enumerate(entries, 1):
                    entry[1] = sequence
        rows = []
        for name, entries in sorted(indexes.items()):
            for non_unique, seq, col, sub, kind, direction, visible in entries:
                rows.append([hx(first), hx(name), str(non_unique), str(seq), hx(col),
                             '-' if sub is None else '+' + str(sub), hx(kind),
                             hx(direction), hx(visible)])
        self.state['expected'][first]['STATISTICS'] = rows
        self.write_state()

    def test_run49_create_only_uses_actual_show_without_new_grants_or_first_recreate(self):
        self.use_current_owner_metadata()
        second = f06.TABLE_ORDER[1]
        self.state['expected'][second]['COLUMNS'] = []
        self.state['show_rows'][second] = synthetic_show_rows(second, self.collation)
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload['tables'][f06.TABLE_ORDER[0]]['status'], 'existing_equivalent')
        self.assertEqual(payload['tables'][f06.TABLE_ORDER[1]]['status'], 'created_equivalent')
        self.assertEqual(self.read_state()['creates'], [f06.TABLE_ORDER[1]])
        self.assertEqual(self.read_state()['grants'], RUN49_GRANTS)

    def test_real_show_is_complete_and_unknown_syntax_or_any_contract_drift_is_rejected(self):
        first = f06.TABLE_ORDER[0]
        columns = f06.parse_show_create(CURRENT_OWNER_SHOW_ROWS, first, self.collation)
        self.assertEqual(len(columns), 17)
        self.assertEqual(tuple(col[1:6] for col in columns), f06.EXPECTED_TABLES[first]['columns'])
        changes = [
            ('`id` bigint', '`id` int'),
            ('bigint NOT NULL AUTO_INCREMENT', 'bigint DEFAULT NULL AUTO_INCREMENT'),
            ('NOT NULL AUTO_INCREMENT', 'NOT NULL'),
            ('varchar(100) NOT NULL', "varchar(100) NOT NULL DEFAULT 'evil'"),
            ('varchar(100) NOT NULL', 'varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL'),
            ('varchar(100) NOT NULL', 'varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL'),
            ('UNIQUE KEY `uk_', 'KEY `uk_'),
            ('`client_id`,`owner_jiacn`,`artifact_id`', '`task_id`,`owner_jiacn`,`artifact_id`'),
            ('ENGINE=InnoDB', 'ENGINE=MyISAM'),
            ('CHARSET=utf8mb4', 'CHARSET=utf8'),
            ('COLLATE=utf8mb4_0900_ai_ci', 'COLLATE=utf8mb4_bin'),
            ("COMMENT 'Primary key'", "COMMENT 'Primary key' INVISIBLE"),
            ('(`id`)', '(`id`(1))'),
            ("= 64)),", "= 64)) NOT ENFORCED,"),
            ('NOT NULL AUTO_INCREMENT', 'NOT NULL AUTO_INCREMENT ON UPDATE 1'),
        ]
        for before, after in changes:
            with self.subTest(change=(before, after)):
                rows = [[field.replace(before, after) for field in row] for row in CURRENT_OWNER_SHOW_ROWS]
                self.assertNotEqual(rows, CURRENT_OWNER_SHOW_ROWS)
                with self.assertRaises(f06.SchemaError):
                    f06.parse_show_create(rows, first, self.collation)
        malformed = [[], CURRENT_OWNER_SHOW_ROWS[:-1], CURRENT_OWNER_SHOW_ROWS[:1] + CURRENT_OWNER_SHOW_ROWS[2:]]
        reordered = copy.deepcopy(CURRENT_OWNER_SHOW_ROWS)
        reordered[1], reordered[2] = reordered[2], reordered[1]
        malformed.extend([reordered, CURRENT_OWNER_SHOW_ROWS + [['trailing SQL']],
                          [[first + '_foreign', CURRENT_OWNER_SHOW_ROWS[0][1]]] + CURRENT_OWNER_SHOW_ROWS[1:]])
        for rows in malformed:
            with self.subTest(rows=rows[:1]):
                with self.assertRaises(f06.SchemaError):
                    f06.parse_show_create(rows, first, self.collation)

    def test_valid_show_does_not_mask_information_schema_indexes_checks_or_table_drift(self):
        for drift in ('index_drift', 'constraint_drift', 'collation_drift'):
            with self.subTest(drift=drift):
                self.use_current_owner_metadata()
                self.state['tables'][f06.TABLE_ORDER[0]] = drift
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertEqual(self.read_state()['creates'], [])

    def test_zero_columns_without_complete_show_remains_blocked_before_ddl(self):
        self.use_run49_metadata()
        self.state['show_rows'] = {}
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'show_create_metadata_invalid')
        self.assertEqual(self.read_state()['creates'], [])
        self.state['metadata_error_tag'] = 'SHOWFIRST'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'metadata_visibility_show_create_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_run49_visible_metadata_with_synthetic_complete_columns_is_equivalent(self):
        self.use_current_owner_metadata(complete_synthetic_columns=True)
        result, payload = self.execute()  # plan: second table remains absent
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload['tables'][f06.TABLE_ORDER[0]]['status'], 'existing_equivalent')
        self.assertEqual(payload['tables'][f06.TABLE_ORDER[1]]['status'], 'planned_create')
        self.assertEqual(self.read_state()['creates'], [])

    def test_both_absent_tables_need_exact_create_before_first_ddl_not_new_privileges(self):
        for missing in f06.TABLE_ORDER:
            with self.subTest(missing=missing):
                self.state['grants'] = [grant for grant in RUN49_GRANTS if '`%s`' % missing not in grant]
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'exact_table_create_privilege_required')
                self.assertEqual(payload['failed_table'], missing)
                self.assertEqual(self.read_state()['creates'], [])

    def test_privilege_scope_column_grant_and_query_failure_are_fail_closed(self):
        valid = list(self.state['grants'])
        changes = [
            ('`jia`.`%s`' % f06.TABLE_ORDER[1], '`jia`.*'),
            ('`jia`.', '`other`.'),
            ('CREATE', 'CREATE, SELECT'),
            ('CREATE', 'CREATE, REFERENCES (`id`)'),
            ('@`localhost`', '@`%`'),
            ('@`localhost`', '@`localhost` WITH GRANT OPTION'),
        ]
        for before, after in changes:
            with self.subTest(change=(before, after)):
                self.state['grants'] = [valid[0], valid[1].replace(before, after), valid[2]]
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'metadata_privilege_scope_invalid')
                self.assertEqual(self.read_state()['creates'], [])
        self.state['grants'] = valid
        self.state['metadata_error_tag'] = 'GRANTS'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'metadata_privilege_query_failed')
        self.assertEqual(self.read_state()['creates'], [])

    def test_existing_create_grants_suffice_but_references_does_not_imply_create(self):
        self.state['grants'] = list(RUN49_GRANTS)
        self.write_state()
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, payload)
        self.state['grants'] = [grant.replace('GRANT CREATE ', 'GRANT REFERENCES ')
                                for grant in self.state['grants']]
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'exact_table_create_privilege_required')
        self.assertEqual(self.read_state()['creates'], [])

    def test_column_collation_and_unique_scope_remain_exact(self):
        first = f06.TABLE_ORDER[0]
        self.state['tables'][first] = 'equivalent'
        changes = [
            ('COLUMNS', 1, 7, optional('utf8'), 'column_charset'),
            ('COLUMNS', 1, 8, optional('utf8mb4_bin'), 'column_collation'),
            ('STATISTICS', -1, 2, '1', 'index_attributes'),
            ('STATISTICS', -1, 4, hx('task_id'), 'indexes'),
        ]
        for tag, row, field, value, mismatch in changes:
            with self.subTest(change=(tag, field, value)):
                self.state['expected'][first] = expected_rows(first, self.collation)
                self.state['expected'][first][tag][row][field] = value
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(mismatch, payload['tables'][first]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])

    def test_partial_columns_and_post_create_invisible_columns_never_pass(self):
        first = f06.TABLE_ORDER[0]
        full = copy.deepcopy(self.state['expected'][first]['COLUMNS'])
        for columns in (full[:1], full[:-1]):
            with self.subTest(columns=len(columns)):
                self.state['tables'][first] = 'equivalent'
                self.state['expected'][first]['COLUMNS'] = columns
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('columns', payload['tables'][first]['mismatches'])
                self.assertEqual(self.read_state()['creates'], [])
        self.state['tables'][first] = 'absent'
        self.state['expected'][first]['COLUMNS'] = []
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'created_table_not_equivalent')
        self.assertIn('post_create_introspection', payload['tables'][first]['mismatches'])
        self.assertEqual(self.read_state()['creates'], [first])
        self.assertEqual(self.read_state()['tables'][first], 'equivalent')  # durable, not dropped
        self.assertEqual(self.read_state()['tables'][f06.TABLE_ORDER[1]], 'absent')

    def test_explicit_charset_uses_exact_session_default_not_any_utf8mb4_collation(self):
        first = f06.TABLE_ORDER[0]
        self.state['tables'][first] = 'equivalent'
        # Table+columns consistently drifted together still must not pass.
        for actual in ('utf8mb4_general_ci', 'utf8mb4_bin'):
            with self.subTest(actual=actual):
                self.state['expected'][first] = expected_rows(first, actual)
                self.write_state()
                result, payload = self.execute()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('table_collation', payload['tables'][first]['mismatches'])
        # general_ci is equivalent only when the same CREATE would use it.
        self.state['default_rows'] = [[hx('utf8mb4_general_ci')]]
        self.state['expected'][first] = expected_rows(first, 'utf8mb4_general_ci')
        self.write_state()
        result, payload = self.execute()
        self.assertEqual(result.returncode, 0, payload)
        for rows in ([], [['']], [[hx('utf8mb4_bin')]], [[hx(self.collation)], [hx(self.collation)]]):
            with self.subTest(default_rows=rows):
                self.state['default_rows'] = rows
                self.write_state()
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'create_collation_metadata_invalid')
                self.assertEqual(self.read_state()['creates'], [])

    def test_runner_file_lock_waits_without_backend_or_schema_mutation(self):
        lock_path = self.root / 'f06-runner.lock'
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

    def test_source_contains_no_lifecycle_or_foreign_release_lock_control(self):
        source = RUNNER.read_text()
        self.assertNotIn('/usr/local/sbin/cyf-api-kit', source)
        self.assertNotIn('/tmp/cyf-release-api.lock', source)
        statements = f06.split_exact_statements(f06.F06_SQL_BYTES)
        self.assertEqual(set(statements), set(f06.TABLE_ORDER))
        for statement in statements.values():
            self.assertRegex(statement, r'^CREATE TABLE IF NOT EXISTS ')
            for forbidden in (' ALTER ', ' DROP ', ' INSERT ', ' UPDATE ', ' DELETE ', ' REPLACE '):
                self.assertNotIn(forbidden, ' ' + statement.upper() + ' ')

    def test_existing_column_drift_fails_before_any_create(self):
        self.state['tables'][f06.TABLE_ORDER[0]] = 'column_drift'
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'existing_schema_drift')
        self.assertIn('columns', payload['tables'][f06.TABLE_ORDER[0]]['mismatches'])
        self.assertEqual(self.read_state()['creates'], [])

    def test_partial_autocommit_is_preserved_and_retry_verifies_before_continuing(self):
        second = f06.TABLE_ORDER[1]
        self.state['create_fail_on'] = second
        self.write_state()
        first_result, first_payload = self.execute('--apply')
        self.assertNotEqual(first_result.returncode, 0)
        self.assertEqual(first_payload['failed_table'], second)
        self.assertEqual(first_payload['tables'][f06.TABLE_ORDER[0]]['status'], 'created_equivalent')
        after_first = self.read_state()
        self.assertEqual(after_first['tables'][f06.TABLE_ORDER[0]], 'equivalent')
        self.assertEqual(after_first['tables'][second], 'absent')
        self.assertEqual(after_first['creates'], list(f06.TABLE_ORDER))

        after_first.pop('create_fail_on')
        after_first['creates'] = []
        self.state = after_first
        self.write_state()
        second_result, second_payload = self.execute('--apply')
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        self.assertEqual(self.read_state()['creates'], [second])
        self.assertEqual(second_payload['tables'][f06.TABLE_ORDER[0]]['status'],
                         'existing_equivalent')
        self.assertEqual(second_payload['tables'][second]['status'], 'created_equivalent')

    def test_post_create_drift_is_not_dropped_or_followed_by_second_create(self):
        first = f06.TABLE_ORDER[0]
        self.state['create_drift_on'] = first
        self.write_state()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['failed_table'], first)
        state = self.read_state()
        self.assertEqual(state['tables'][first], 'column_drift')
        self.assertEqual(state['tables'][f06.TABLE_ORDER[1]], 'absent')
        self.assertEqual(state['creates'], [first])

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
        self.assertEqual(payload['error'], 'f06_resource_digest_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())
        self.assertEqual(self.read_state()['creates'], [])

    def test_wrong_nested_module_location_is_rejected(self):
        self.rebuild_release(nested_name='BOOT-INF/lib/not-the-mapper.jar')
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'mapper_jar_location_invalid')
        self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_record_receipt_source_run_mismatch_is_rejected(self):
        self.rebuild_release(record_overrides={'run_id': '40'})
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'receipt_release_identity_mismatch')
        self.assertFalse((self.root / 'mysql-args.json').exists())

    def test_arbitrary_cli_payload_is_rejected_without_touching_backend(self):
        result, payload = self.execute('--apply', '--database=evil')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload['error'], 'arguments_rejected')
        self.assertFalse((self.root / 'mysql-args.json').exists())
        self.assertEqual(self.read_state()['creates'], [])

    def test_missing_password_fails_without_starting_mysql(self):
        del self.env['CYF_F06_MYSQL_PASSWORD']
        result, payload = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'mysql_password_environment_missing')
        self.assertFalse((self.root / 'mysql-args.json').exists())


    def test_preservation_f06_current_sql_and_mandatory_owner_catalog_are_exact(self):
        self.assertEqual(f06.RESOURCE_SHA256,
                         '80df95b430e6d6e806c8f5b2bf487b63115a23d9692ac1bafd51f9d81e13fb53')
        self.assertEqual(digest(f06.F06_SQL_BYTES), f06.RESOURCE_SHA256)
        self.assertIn(b'owner_jiacn', f06.F06_SQL_BYTES)
        for table in f06.TABLE_ORDER:
            spec = f06.EXPECTED_TABLES[table]
            self.assertIn(('owner_jiacn', 'varchar(50)', 'NO', None, ''), spec['columns'])
            for name, unique, columns, kind in spec['indexes']:
                if columns[:2] == ('tenant_id', 'client_id'):
                    self.assertEqual(columns[2], 'owner_jiacn', name)

    def test_preservation_raw_historical_ownerless_show_is_not_current_schema(self):
        first = f06.TABLE_ORDER[0]
        # Original Run49 snapshot stays literal and is NOT relabelled current/live.
        with self.assertRaises(f06.SchemaError):
            f06.parse_show_create(RUN49_SHOW_ROWS, first, self.collation)
        self.use_run49_metadata()
        result, payload = self.execute('--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload['error'], 'show_create_schema_drift')
        self.assertEqual(self.read_state()['creates'], [])

    def test_preservation_only_two_exact_current_owner_column_layouts_pass(self):
        first = f06.TABLE_ORDER[0]
        appended = synthetic_show_rows(first, self.collation)
        columns = f06.parse_show_create(appended, first, self.collation)
        self.assertEqual(len(columns), 17)
        self.assertEqual(tuple(col[1:6] for col in columns), f06.EXPECTED_TABLES[first]['columns'])
        authored = copy.deepcopy(appended)
        owner = next(row for row in authored if row[0].startswith('  `owner_jiacn`'))
        authored.remove(owner)
        client = next(i for i, row in enumerate(authored) if row[0].startswith('  `client_id`'))
        authored.insert(client + 1, owner)
        self.assertEqual({col[1] for col in f06.parse_show_create(authored, first, self.collation)},
                         {value[0] for value in f06.EXPECTED_TABLES[first]['columns']})
        # CHECK-free schema retains all owner columns/indexes.
        without_checks = [row for row in authored if not row[0].startswith('  CONSTRAINT ')]
        without_checks[-2][0] = without_checks[-2][0].rstrip(',')
        self.assertEqual(len(f06.parse_show_create(without_checks, first, self.collation)), 17)
        second = f06.TABLE_ORDER[1]
        decision = [row for row in synthetic_show_rows(second, self.collation)
                    if 'CONSTRAINT `chk_artifact_outcome_decision_' not in row[0]]
        decision[-2][0] = decision[-2][0].rstrip(',')
        self.assertEqual(len(f06.parse_show_create(decision, second, self.collation)),
                         len(f06.EXPECTED_TABLES[second]['columns']))
        wrong = copy.deepcopy(authored)
        wrong.remove(owner)
        wrong.insert(1, owner)
        with self.assertRaises(f06.SchemaError):
            f06.parse_show_create(wrong, first, self.collation)

    def test_preservation_missing_owner_index_or_nullable_owner_is_rejected_before_create(self):
        first = f06.TABLE_ORDER[0]
        self.state['tables'][first] = 'equivalent'
        for drift in ('nullable', 'missing_index_owner'):
            rows = expected_rows(first, self.collation)
            if drift == 'nullable':
                owner = next(row for row in rows['COLUMNS'] if row[2] == hx('owner_jiacn'))
                owner[4] = hx('YES')
            else:
                rows['STATISTICS'] = [row for row in rows['STATISTICS'] if row[4] != hx('owner_jiacn')]
                sequence = {}
                for row in rows['STATISTICS']:
                    sequence[row[1]] = sequence.get(row[1], 0) + 1
                    row[3] = str(sequence[row[1]])
            self.state['expected'][first] = rows
            self.write_state()
            with self.subTest(drift=drift):
                result, payload = self.execute('--apply')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(payload['error'], 'existing_schema_drift')
                self.assertEqual(self.read_state()['creates'], [])


    def test_oracle_sync_current_show_cannot_omit_or_weaken_owner_scope(self):
        first = f06.TABLE_ORDER[0]
        self.assertEqual(digest(f06.F06_SQL_BYTES),
                         '80df95b430e6d6e806c8f5b2bf487b63115a23d9692ac1bafd51f9d81e13fb53')
        parsed = f06.parse_show_create(CURRENT_OWNER_SHOW_ROWS, first, self.collation)
        self.assertEqual(len(parsed), 17)
        self.assertIn(b'(tenant_id, client_id, owner_jiacn, artifact_id, artifact_version)',
                      f06.F06_SQL_BYTES)
        for before, after in (("`owner_jiacn` varchar(50) NOT NULL", "`owner_jiacn` varchar(50) DEFAULT NULL"),
                              ('`client_id`,`owner_jiacn`,`artifact_id`', '`client_id`,`artifact_id`')):
            rows = [[value.replace(before, after) for value in row]
                    for row in CURRENT_OWNER_SHOW_ROWS]
            self.assertNotEqual(rows, CURRENT_OWNER_SHOW_ROWS)
            with self.subTest(change=(before, after)), self.assertRaises(f06.SchemaError):
                f06.parse_show_create(rows, first, self.collation)



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
        self.patch = patch.object(f06, 'local_coordinator_validator', return_value=self.deploy.__dict__)
        self.patch.start()

    def tearDown(self):
        self.patch.stop(); self.fixture.tearDown()

    def verify(self):
        return f06.verify_release_binding(self.paths, os.geteuid(), self.modes)

    def test_v3_consumed_installed_record_has_typed_source_no_fake_flow_identity(self):
        binding = self.verify()
        self.assertEqual(binding['source'], self.inputs.decision['source'])
        self.assertEqual(binding['binding_sha256'], self.deploy.local_binding_sha(self.fixture.binding))
        self.assertEqual(binding['expected_catalog_sha256'], digest(self.deploy.local_canonical(f06.EXPECTED_TABLES)))
        self.assertNotIn('run', binding)
        f06.assert_binding_paths_unchanged(self.paths, os.geteuid(), self.modes, binding, full_digest=True)

    def test_v3_installed_record_cannot_substitute_different_package(self):
        self.paths['package'].write_bytes(b'wrong incoming after installation')
        with self.assertRaises(f06.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_package_invalid')

    def test_v3_unconsumed_approval_cannot_authorize_schema(self):
        path = self.paths['record'].parent / 'approval.json'
        approval = json.loads(path.read_text()); approval.update(consumed=False, consumed_at=None)
        path.write_bytes(self.deploy.local_canonical(approval))
        with self.assertRaises(f06.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_recovery_binding_mismatch')

    def test_v3_noninstalled_phase_cannot_authorize_schema(self):
        record = json.loads(self.paths['record'].read_text()); record.update(status='active_pending', phase='commit')
        self.paths['record'].write_bytes(self.deploy.local_canonical(record))
        with self.assertRaises(f06.SchemaError) as error: self.verify()
        self.assertEqual(error.exception.code, 'local_durable_record_incomplete')

    def test_v3_immutable_inputs_are_rechecked_before_original_ddl_boundary(self):
        binding = self.verify()
        Path(self.inputs.decision['precondition']['schemaInventory']['path']).write_bytes(b'changed schema observation')
        with self.assertRaises(f06.SchemaError) as error:
            f06.assert_binding_paths_unchanged(self.paths, os.geteuid(), self.modes, binding)
        self.assertEqual(error.exception.code, 'local_immutable_input_changed')

if __name__ == '__main__':
    unittest.main()
