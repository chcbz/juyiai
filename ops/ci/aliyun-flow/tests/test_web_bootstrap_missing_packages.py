"""Exercise the exact Flow shell fragment without network, RPM or host mutation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

TEMPLATE = Path(__file__).resolve().parents[1] / 'templates/frontend-develop-release.yaml'


class BootstrapTests(unittest.TestCase):
    def run_fragment(self, installed, manager_exit=0):
        source = TEMPLATE.read_text()
        start = source.index('                missing_packages=')
        end = source.index('                node_sha=', start)
        fragment = '\n'.join(line[16:] for line in source[start:end].splitlines())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rpm = root / 'rpm'
            rpm.write_text('#!/bin/sh\ncase " $INSTALLED " in *" $3 "*) exit 0;; *) exit 1;; esac\n')
            manager = root / 'manager'
            manager.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CALL_LOG"\nexit "$MANAGER_EXIT"\n')
            for path in (rpm, manager):
                path.chmod(0o700)
            log = root / 'call.log'
            env = dict(os.environ, PATH=folder+':'+os.environ['PATH'], INSTALLED=installed,
                       manager=str(manager), CALL_LOG=str(log), MANAGER_EXIT=str(manager_exit))
            result = subprocess.run(['/bin/sh', '-ec', fragment], env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            return result.returncode, log.read_text().splitlines() if log.exists() else []

    def test_installed_packages_skip_manager(self):
        self.assertEqual(self.run_fragment('ca-certificates curl tar xz git'), (0, []))

    def test_only_missing_packages_are_requested(self):
        code, args = self.run_fragment('ca-certificates curl tar git')
        self.assertEqual(code, 0)
        self.assertEqual(args, ['-y', '--setopt=gpgcheck=1', '--setopt=install_weak_deps=False', 'install', 'xz'])

    def test_empty_image_still_installs_all_required_packages(self):
        code, args = self.run_fragment('')
        self.assertEqual(code, 0)
        self.assertEqual(args[-5:], ['ca-certificates', 'curl', 'tar', 'xz', 'git'])

    def test_install_failure_is_not_ignored(self):
        code, args = self.run_fragment('curl tar xz git', manager_exit=19)
        self.assertEqual(code, 19)
        self.assertEqual(args[-1], 'ca-certificates')

    def test_full_test_build_and_integrity_commands_are_preserved(self):
        source = TEMPLATE.read_text()
        for command in ('npm ci --include=dev', 'npm run test', 'npm run build',
                        'sha256sum -c -', '--setopt=gpgcheck=1'):
            self.assertIn(command, source)


if __name__ == '__main__':
    unittest.main()
