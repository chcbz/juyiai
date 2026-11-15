"""Real MySQL 8.0 fixtures on a private Unix socket; never connect to production."""
import os
from pathlib import Path
import pwd
import subprocess
import tempfile
import time
import unittest

BASE = Path('/home/isp/apps/mysql')
POLICY = Path(__file__).resolve().parents[1] / 'mysql-audit-retention.sql'


class AuditRetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='cyf-audit-retention-test-', dir='/var/tmp')
        cls.root = Path(cls.tmp.name)
        cls.data = cls.root / 'data'; cls.data.mkdir()
        cls.sock = cls.root / 'mysql.sock'
        cls.user = pwd.getpwuid(os.getuid()).pw_name
        cls.proc = None
        try:
            init = [str(BASE / 'bin/mysqld'), '--no-defaults', '--basedir=' + str(BASE),
                    '--datadir=' + str(cls.data), '--user=' + cls.user, '--initialize-insecure',
                    '--skip-log-bin', '--innodb-buffer-pool-size=64M', '--innodb-log-file-size=16M']
            with (cls.root / 'initialize.log').open('w') as log:
                subprocess.run(init, stdout=log, stderr=log, check=True)
            command = [str(BASE / 'bin/mysqld'), '--no-defaults', '--basedir=' + str(BASE),
                       '--datadir=' + str(cls.data), '--user=' + cls.user,
                       '--socket=' + str(cls.sock), '--pid-file=' + str(cls.root / 'mysql.pid'),
                       '--log-error=' + str(cls.root / 'mysql.log'), '--skip-networking',
                       '--mysqlx=OFF', '--skip-log-bin', '--event-scheduler=ON',
                       '--innodb-buffer-pool-size=64M', '--innodb-log-file-size=16M']
            cls.proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            until = time.monotonic() + 60
            while True:
                if cls.proc.poll() is not None:
                    raise RuntimeError('isolated mysqld failed to start')
                if cls.sock.exists():
                    r = subprocess.run(cls.client() + ['-e', 'SELECT 1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if r.returncode == 0:
                        break
                if time.monotonic() >= until:
                    raise RuntimeError('isolated fixture did not become ready')
                time.sleep(0.1)
            cls.query('CREATE DATABASE jia; CREATE TABLE jia.core_log (id BIGINT PRIMARY KEY, create_time BIGINT) ENGINE=InnoDB;')
            cls.query(POLICY.read_text())
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        if cls.proc is not None and cls.proc.poll() is None:
            subprocess.run([str(BASE / 'bin/mysqladmin'), '--no-defaults', '--protocol=socket',
                            '--socket=' + str(cls.sock), '-uroot', 'shutdown'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                cls.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                cls.proc.terminate()  # only the exact fixture Popen, never server discovery
                cls.proc.wait(timeout=30)
        cls.tmp.cleanup()

    @classmethod
    def client(cls):
        return [str(BASE / 'bin/mysql'), '--no-defaults', '--protocol=socket',
                '--socket=' + str(cls.sock), '-uroot', '--batch', '--skip-column-names']

    @classmethod
    def query(cls, sql, check=True):
        r = subprocess.run(cls.client(), input=sql, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True)
        if check and r.returncode:
            raise AssertionError(r.stderr)
        return r

    def setUp(self):
        self.query('TRUNCATE jia.core_log;')  # isolated fixture only

    def test_old_removed_recent_unknown_and_boundary_retained(self):
        sql = '''SET @cut=CAST(UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3)-INTERVAL 7 DAY)*1000 AS UNSIGNED);
        INSERT INTO jia.core_log VALUES (1,@cut-1),(2,@cut),(3,@cut+100000),(4,NULL),(5,0),(6,-1),(7,@cut+9999999999);
        CALL jia.cyf_core_log_retention_7d(@cut,NULL,@n);
        SELECT @n; SELECT GROUP_CONCAT(id ORDER BY id) FROM jia.core_log;'''
        self.assertEqual(self.query(sql).stdout.strip().splitlines(), ['1', '2,3,4,5,6,7'])

    def test_future_cutoff_cannot_shorten_seven_days(self):
        sql = '''SET @now=CAST(UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000 AS UNSIGNED);
        INSERT INTO jia.core_log VALUES(1,@now-86400000),(2,@now-8*86400000);
        CALL jia.cyf_core_log_retention_7d(@now+86400000,NULL,@n); SELECT @n; SELECT id FROM jia.core_log;'''
        self.assertEqual(self.query(sql).stdout.strip().splitlines(), ['1', '1'])

    def test_upper_id_binds_initial_backup_scope(self):
        self.assertEqual(self.query('INSERT INTO jia.core_log VALUES(1,1000000000000),(2,1000000000000); CALL jia.cyf_core_log_retention_7d(NULL,1,@n); SELECT @n; SELECT id FROM jia.core_log;').stdout.strip().splitlines(), ['1', '2'])

    def test_multiple_windows_and_repeated_clean_are_idempotent(self):
        values = ','.join('(%d,%s)' % (i, 'NULL' if i % 1000 == 0 else '1000000000000') for i in range(1, 10006))
        self.query('INSERT INTO jia.core_log VALUES ' + values)
        result = self.query('CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n); SELECT @n; CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n); SELECT @n; SELECT COUNT(*) FROM jia.core_log;')
        self.assertEqual(result.stdout.strip().splitlines(), ['9995', '0', '10'])

    def test_empty_table(self):
        self.assertEqual(self.query('CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n); SELECT @n;').stdout.strip(), '0')

    def test_autocommit_disabled_is_rejected(self):
        result = self.query('SET autocommit=0; CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n);', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires autocommit', result.stderr)

    def test_lock_conflict_never_releases_other_owner(self):
        holder = subprocess.Popen(self.client() + ['--unbuffered'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        try:
            holder.stdin.write("SELECT GET_LOCK('jia.core_log.retention_7d',0);\n"); holder.stdin.flush()
            self.assertEqual(holder.stdout.readline().strip(), '1')
            result = self.query('CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n);', check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already running', result.stderr)
            holder.stdin.write("SELECT IS_USED_LOCK('jia.core_log.retention_7d')=CONNECTION_ID();\n"); holder.stdin.flush()
            self.assertEqual(holder.stdout.readline().strip(), '1')
        finally:
            holder.communicate('quit\n', timeout=5)

    def test_exception_releases_own_lock(self):
        self.query('RENAME TABLE jia.core_log TO jia.fixture_saved;')
        try:
            result = self.query('CALL jia.cyf_core_log_retention_7d(NULL,NULL,@n);', check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.query("SELECT IS_FREE_LOCK('jia.core_log.retention_7d');").stdout.strip(), '1')
        finally:
            self.query('RENAME TABLE jia.fixture_saved TO jia.core_log;')

    def test_daily_event_enabled_with_single_cleanup_owner(self):
        self.assertEqual(self.query("SELECT STATUS,INTERVAL_VALUE,INTERVAL_FIELD,EVENT_DEFINITION FROM information_schema.EVENTS WHERE EVENT_SCHEMA='jia' AND EVENT_NAME='cyf_core_log_retention_7d';").stdout.strip(),
                         'ENABLED\t1\tDAY\tCALL `jia`.`cyf_core_log_retention_7d`(NULL, NULL, @cyf_audit_deleted)')


if __name__ == '__main__':
    unittest.main()
