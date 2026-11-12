"""Lightweight host adapter tests: no Java, database, build or production paths."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

INSTALLER = Path(__file__).resolve().parents[4] / 'ops/ci/aliyun-flow/host/cyf-api-flow-install'


class RestoredRetryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cyf-restored-retry-')
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.record = self.root / 'record.json'
        self.auth = self.root / 'retry-authorization.json'
        self.value = dict(status='failed', phase='activating_candidate_recovery',
                          recovery='restored_healthy', run_id='409', source_commit_sha='a' * 40,
                          candidate_sha256='b' * 64, previous_sha256='c' * 64)
        source = INSTALLER.read_text()
        self.body = source.split("<<'RETRY_PY'\n", 1)[1].split('\nRETRY_PY', 1)[0]
        self.prepare()

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self):
        self.raw = json.dumps(self.value).encode()
        self.record.write_bytes(self.raw)
        self.record.chmod(0o600)
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.auth.write_text(json.dumps(dict(schema_version=1,
                            failed_record_sha256=self.digest, reason='Explicit fixture retry')))
        self.auth.chmod(0o600)

    def run_guard(self):
        return subprocess.run(['/usr/bin/python3', '-I', '-B', '-', str(self.root),
                               str(self.record), str(os.getuid())], input=self.body,
                              universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_explicit_restored_retry_archives_failure_and_consumes_authorization(self):
        self.assertEqual(0, self.run_guard().returncode)
        self.assertEqual(self.raw, self.record.read_bytes())
        archive = self.root / 'retry-history' / self.digest
        self.assertEqual(self.raw, (archive / 'failed-record.json').read_bytes())
        self.assertTrue((archive / 'authorization.json').is_file())
        self.assertFalse(self.auth.exists())
        self.assertNotEqual(0, self.run_guard().returncode)
        self.prepare()
        self.assertNotEqual(0, self.run_guard().returncode)

    def test_changed_failed_record_is_rejected(self):
        self.record.write_text(json.dumps(dict(self.value, run_id='410')))
        self.assertNotEqual(0, self.run_guard().returncode)
        self.assertFalse((self.root / 'retry-history').exists())

    def test_start_failure_and_unfinished_recovery_are_not_retries(self):
        for field, value in [('phase', 'candidate_start_failed'), ('status', 'activating'),
                             ('recovery', 'candidate_stop_unverified')]:
            with self.subTest(field=field):
                original = dict(self.value)
                self.value[field] = value
                self.prepare()
                self.assertNotEqual(0, self.run_guard().returncode)
                self.value = original

    def test_missing_or_unsafe_authorization_is_rejected(self):
        self.auth.chmod(0o644)
        self.assertNotEqual(0, self.run_guard().returncode)
        self.auth.unlink()
        self.assertNotEqual(0, self.run_guard().returncode)

    def test_symlink_authorization_is_rejected(self):
        saved = self.root / 'saved.json'
        self.auth.rename(saved)
        self.auth.symlink_to(saved)
        self.assertNotEqual(0, self.run_guard().returncode)

    def test_exact_release_and_old_jar_checks_still_precede_retry(self):
        source = INSTALLER.read_text()
        branch = source[source.index('  case "$RECORD_STATUS" in'):]
        self.assertIn('if (( RECORD_MATCH )); then', source)
        self.assertLess(branch.index('failed transaction found unexpected canonical bytes'),
                        branch.index('      authorize_restored_retry'))
        self.assertLess(branch.index('      lifecycle_healthy || fail'),
                        branch.index('      authorize_restored_retry'))


if __name__ == '__main__':
    unittest.main()
