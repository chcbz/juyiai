import os
import fcntl
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[4]
INSTALLER = ROOT / 'ops/ci/aliyun-flow/host/cyf-api-flow-install'


class ApiFlowInstallLockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix='cyf-api-flow-install-lock-', dir='/tmp')
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        (self.root / 'state/incoming').mkdir(parents=True, mode=0o700)
        (self.root / 'service').mkdir(mode=0o700)
        (self.root / 'bin').mkdir(mode=0o700)
        lifecycle = self.root / 'bin/cyf-api-kit'
        lifecycle.write_text('#!/bin/sh\nexit 0\n')
        lifecycle.chmod(0o700)
        self.lock = self.root / 'cyf-release-api.lock'
        self.lock.write_bytes(b'')
        self.lock.chmod(0o600)
        self.package = self.root / 'state/incoming/package.tgz'
        self.package.write_bytes(b'not inspected before the lock')
        self.package.chmod(0o644)
        self.env = dict(os.environ)
        self.env.update(
            CYF_RELEASE_OFFLINE_TEST='YES',
            CYF_API_FLOW_INSTALL_TEST_ROOT=str(self.root),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_installer(self):
        started = time.monotonic()
        result = subprocess.run(
            [str(INSTALLER)],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return result, time.monotonic() - started

    def hold_lock(self, seconds):
        marker = self.root / 'holder-ready'
        holder = subprocess.Popen([
            'flock', '-x', str(self.lock), 'sh', '-c',
            'printf held > "$1"; sleep "$2"',
            'lock-holder', str(marker), str(seconds),
        ])
        deadline = time.monotonic() + 5
        while not marker.exists() and holder.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(marker.exists(), 'temporary holder did not acquire fixture lock')
        self.assertIsNone(holder.poll(), 'temporary holder exited before installer started')
        return holder

    def assert_reached_first_post_lock_action(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approval is missing or unsafe', result.stderr)
        self.assertNotIn('another API release is active', result.stderr)
        self.assertEqual(self.package.stat().st_mode & 0o777, 0o600)

    def test_immediate_acquisition_reaches_post_lock_action(self):
        result, elapsed = self.run_installer()

        self.assert_reached_first_post_lock_action(result)
        self.assertLess(elapsed, 5)

    def test_short_holder_release_allows_bounded_waiter_to_acquire(self):
        holder = self.hold_lock(0.5)
        result, elapsed = self.run_installer()
        holder.wait(timeout=5)

        self.assert_reached_first_post_lock_action(result)
        self.assertGreaterEqual(elapsed, 0.2)
        self.assertLess(elapsed, 5)

    def test_contention_waits_without_mutation_then_proceeds(self):
        original = self.package.read_bytes()
        with self.lock.open('r+') as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            waiter = subprocess.Popen([str(INSTALLER)], env=self.env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True)
            try:
                time.sleep(0.3)
                self.assertIsNone(waiter.poll())
                self.assertEqual(self.package.read_bytes(), original)
                self.assertFalse((self.root / 'state/record.json').exists())
            finally:
                fcntl.flock(held, fcntl.LOCK_UN)
            out, err = waiter.communicate(timeout=5)
        self.assertIn('approval is missing or unsafe', err)
        self.assertNotEqual(waiter.returncode, 0)
        self.assertNotIn('another API release is active', err)


    def test_preservation_same_fd8_precedes_package_mutation_and_lifecycle_descendants(self):
        source = INSTALLER.read_text()
        acquire = source.index('flock -x 8')
        self.assertLess(acquire, source.index('chmod 0600 "$INCOMING_PACKAGE"'))
        self.assertIn('CYF_RELEASE_LOCK_INHERITED_FD=8', source)
        self.assertIn('CYF_RELEASE_LOCK_DEVICE="$LOCK_DEVICE"', source)
        self.assertIn('CYF_RELEASE_LOCK_INODE="$LOCK_INODE"', source)
        self.assertNotIn('flock -w', source)
        self.assertNotIn('LOCK_NB', source)

    def test_preservation_forward_repair_requires_exact_same_record_and_candidate(self):
        source = INSTALLER.read_text()
        start = source.index('resume_forward_candidate() {')
        end = source.index('\ncommit_candidate() {', start)
        repair = source[start:end]
        self.assertIn('"$RECORD_MATCH" == 1', repair)
        self.assertIn('"$RECORD_STATUS" == failed', repair)
        self.assertIn('"$RECORD_RECOVERY" == forward_only_candidate_retained', repair)
        self.assertIn('"$TARGET_STATE" == "$JAR_SHA"', repair)
        self.assertIn('write_record activating forward_repair candidate_retained', repair)
        self.assertNotIn('restore_backup', repair)
        self.assertNotIn('detach_candidate', repair)


if __name__ == '__main__':
    unittest.main()
