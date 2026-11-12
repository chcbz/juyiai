"""Storage policy regressions; no Gradle/npm/build/deploy or mount changes."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from build_storage import require_disk, build_environment


class BuildStorageTest(unittest.TestCase):
    def test_disk_new_directory(self):
        with tempfile.TemporaryDirectory(dir=SCRIPTS) as folder:
            require_disk(Path(folder) / 'not-created' / 'build')
            self.assertFalse((Path(folder) / 'not-created').exists())

    def test_actual_shm_rejected(self):
        with self.assertRaisesRegex(ValueError, 'tmpfs'):
            require_disk('/dev/shm/cyf-policy-test-do-not-create/build')

    def test_symlink_to_shm_rejected(self):
        with tempfile.TemporaryDirectory(dir=SCRIPTS) as folder:
            link = Path(folder) / 'alias'
            link.symlink_to('/dev/shm', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'tmpfs'):
                require_disk(link / 'new-build')

    def test_filesystem_not_path_name_controls_policy(self):
        for kind in ('tmpfs', 'ramfs'):
            with patch('build_storage.subprocess.check_output', return_value=kind+'\n'):
                with self.assertRaisesRegex(ValueError, kind):
                    require_disk(SCRIPTS / 'new-build')

    def test_stat_failure_does_not_start_build(self):
        with patch('build_storage.subprocess.check_output', side_effect=OSError('stat failed')):
            with self.assertRaises(OSError):
                require_disk(SCRIPTS)

    def test_environment_uses_batch_disk_and_preserves_other_options(self):
        inherited = dict(TMPDIR='/dev/shm', JAVA_TOOL_OPTIONS='-Xmx128m -Djava.io.tmpdir=/dev/shm', OTHER='kept')
        with tempfile.TemporaryDirectory(dir=SCRIPTS) as folder:
            env = build_environment(folder, inherited)
            for key in ('TMPDIR', 'TMP', 'TEMP'):
                self.assertEqual(str(Path(folder)/'tmp'), env[key])
            self.assertTrue((Path(folder)/'tmp').is_dir())
            self.assertIn('-Xmx128m', env['JAVA_TOOL_OPTIONS'])
            self.assertNotIn('/dev/shm', env['JAVA_TOOL_OPTIONS'])
            self.assertEqual('kept', env['OTHER'])
            self.assertEqual('/dev/shm', inherited['TMPDIR'])

    def test_all_python_entrypoints_reject_shm_before_build(self):
        bad = '/dev/shm/cyf-policy-{}-not-created'.format(os.getpid())
        commands = [
            ['local_build.py', '--source', str(SCRIPTS), '--output', bad,
             '--cache-home', str(SCRIPTS), '--jdk', '/usr', '--version', 'test',
             '--batch-id', 'storage-test', '--task-id', 'storage-test'],
            ['local_web_build.py', '--source', str(SCRIPTS), '--output', bad,
             '--batch-id', 'storage-test', '--expected-commit', 'a'*40],
        ]
        if os.geteuid() == 0:
            commands.append(['local_release.py', '--api-source', str(SCRIPTS),
                '--web-source', str(SCRIPTS), '--output', bad,
                '--evidence-dir', bad+'-evidence', '--cache-home', str(SCRIPTS),
                '--jdk', '/usr', '--task-id', 'storage-test', '--batch-id', 'storage-test',
                '--api-version', 'test', '--expected-api-commit', 'a'*40,
                '--expected-web-commit', 'b'*40, '--install'])
        for command in commands:
            with self.subTest(entry=command[0]):
                result = subprocess.run([sys.executable, str(SCRIPTS/command[0])] + command[1:],
                                        capture_output=True, text=True)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('local build storage must not use tmpfs', result.stderr)
                self.assertFalse(Path(bad).exists())
                self.assertFalse(Path(bad+'-evidence').exists())


if __name__ == '__main__':
    unittest.main()
