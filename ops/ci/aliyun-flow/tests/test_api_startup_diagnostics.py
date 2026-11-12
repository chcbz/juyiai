"""Tiny shell/installer fixtures only. No real JVM, service, database or Flow run."""
import os
from pathlib import Path
import re
import subprocess
import unittest

import test_api_gate_policy as fixture

HOST = Path(__file__).resolve().parents[1] / 'host'


class StartupDiagnosticsShellTest(unittest.TestCase):
    def script(self, name, body, enabled=None, closed_stderr=False):
        source = (HOST / name).read_text()
        snippet = source.split('# BEGIN STARTUP_DIAGNOSTICS\n', 1)[1].split('# END STARTUP_DIAGNOSTICS', 1)[0]
        env = dict(os.environ, DIAGNOSTIC_SECRET_CANARY='must-not-be-logged')
        env.pop('CYF_API_STARTUP_DIAGNOSTICS', None)
        if enabled is not None:
            env['CYF_API_STARTUP_DIAGNOSTICS'] = enabled
        script = 'set -euo pipefail\n' + snippet + '\n'
        if closed_stderr:
            script += 'exec 2>&-\n'
        return subprocess.run(['bash', '-c', script + body], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=5)

    def test_off_is_silent(self):
        for name in ('cyf-api-kit', 'cyf-api-flow-install'):
            result = self.script(name, 'diagnostic_mark fixture.begin\n')
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout + result.stderr, '')

    def test_enabled_emits_only_fixed_fields_to_stderr(self):
        for name in ('cyf-api-kit', 'cyf-api-flow-install'):
            result = self.script(name, 'diagnostic_mark fixture.begin\ndiagnostic_mark fixture.end\n', '1')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            lines = result.stderr.splitlines()
            self.assertEqual(len(lines), 2)
            ticks = []
            for line in lines:
                self.assertRegex(line, r'^CYF_DEPLOY_TIMING component=(installer|lifecycle) pid=\d+ point=fixture\.(begin|end) monotonic_s=\d+\.\d+ wall=\S+$')
                ticks.append(float(re.search(r'monotonic_s=([\d.]+)', line).group(1)))
            self.assertGreaterEqual(ticks[1], ticks[0])
            self.assertNotIn('must-not-be-logged', result.stderr)

    def test_closed_diagnostic_sink_does_not_fail_command(self):
        result = self.script('cyf-api-kit', 'diagnostic_mark fixture.begin\nprintf success\n', '1', True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'success')

    def test_existing_failure_still_exits_before_end(self):
        result = self.script('cyf-api-flow-install', 'diagnostic_mark fixture.begin\nfalse\ndiagnostic_mark fixture.end\n', '1')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('fixture.end', result.stderr)

    def test_only_allowlisted_debug_args_and_off_has_no_args(self):
        source = (HOST / 'cyf-api-kit').read_text()
        snippet = source.split('start_api() {\n', 1)[1].split('  local pid ticks stamp', 1)[0]
        expected = [
            '--logging.level.org.springframework.beans.factory.support.DefaultListableBeanFactory=DEBUG',
            '--logging.level.org.springframework.context.support.DefaultLifecycleProcessor=TRACE',
            '--cyf.startup-tracing.enabled=true',
            '--logging.level.org.mybatis.spring.mapper.ClassPathMapperScanner=DEBUG',
        ]
        for flag in ('0', '1'):
            script = 'set -euo pipefail\nf() {\n' + snippet + '\nfor arg in "${startup_debug_args[@]}"; do printf "%s\\n" "$arg"; done\n}\nf\n'
            result = subprocess.run(['bash', '-c', script], env=dict(os.environ, CYF_API_STARTUP_DIAGNOSTICS=flag),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), expected if flag == '1' else [])
        self.assertIn('--logging.level.root=info', source)
        self.assertIn('--logging.level.org.springframework.security=info', source)
        self.assertIn('"${startup_debug_args[@]}" \\\n', source)


class StartupDiagnosticsInstallerTest(fixture.ApiGatePolicyTest):
    # Re-run the existing success/integrity/recovery-space fixtures with logging ON.
    def setUp(self):
        super().setUp()
        self.env.update(CYF_API_STARTUP_DIAGNOSTICS='1', DIAGNOSTIC_SECRET_CANARY='must-not-be-logged')

    def install(self):
        try:
            return super().install()
        except subprocess.TimeoutExpired as exc:
            # Keep the original failure and limit, but retain value-free progress
            # so slow execution can be distinguished from an actual stuck phase.
            output = exc.stderr or ''
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='replace')
            points = re.findall(r'CYF_DEPLOY_TIMING component=\w+ pid=\d+ point=[a-z_.]+ monotonic_s=[\d.]+', output)
            raise AssertionError('fixture timeout after %ss; observed progress: %s' %
                                 (exc.timeout, '; '.join(points[-8:]))) from exc

    def test_full_fixture_records_each_success_phase(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('CYF_DEPLOY_TIMING', result.stdout)
        self.assertNotIn('must-not-be-logged', result.stderr)
        points = re.findall(r'point=([a-z_.]+)', result.stderr)
        for phase in ('release_lock', 'unpack_validate', 'backup', 'stop_verify', 'activate', 'start_wait',
                      'status_first', 'final_jar_hash', 'status_final', 'commit_records'):
            self.assertEqual(points.count(phase + '.begin'), 1, phase)
            self.assertEqual(points.count(phase + '.end'), 1, phase)
            self.assertLess(points.index(phase + '.begin'), points.index(phase + '.end'))
        self.assertIn('installed', points)
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['stop', 'status', 'start', 'status', 'status'])


if __name__ == '__main__':
    unittest.main()
