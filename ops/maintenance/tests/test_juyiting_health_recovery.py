"""Offline regressions: no live restart, state writes, or SMTP calls."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import stat
import types
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parents[1] / 'health_monitor'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(BASE / filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


carrier = load('recovery_carrier', 'cyf-juyiting-recovery-carrier.py')
monitor = load('health_monitor', 'cyf-juyiting-health.py')


class CarrierTests(unittest.TestCase):
    def test_monitor_pin_matches_candidate_carrier(self):
        self.assertEqual(monitor.RECOVERY_CARRIER_SHA256,
                         hashlib.sha256((BASE / 'cyf-juyiting-recovery-carrier.py').read_bytes()).hexdigest())

    def test_check_is_readonly(self):
        with mock.patch.object(carrier, 'validate_canonical') as validate, \
                mock.patch.object(carrier, 'configure_own_swappiness') as cgroup, \
                mock.patch.object(carrier.subprocess, 'Popen') as spawn, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(carrier.main(['--check']), 0)
        validate.assert_called_once_with()
        cgroup.assert_not_called()
        spawn.assert_not_called()
        self.assertEqual(output.getvalue(), 'CYF_HEALTHMON_CANONICAL=OK\n')

    def test_check_reports_exact_pin_failure_without_dispatch(self):
        with mock.patch.object(carrier, 'validate_canonical',
                               side_effect=carrier.CarrierError('canonical_hash_mismatch')), \
                mock.patch.object(carrier.subprocess, 'Popen') as spawn, \
                contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(carrier.main(['--check']), 125)
        spawn.assert_not_called()
        self.assertEqual(error.getvalue(), 'CYF_HEALTHMON_CHECK_ERROR=canonical_hash_mismatch\n')

    def test_check_does_not_leak_os_error(self):
        with mock.patch.object(carrier, 'validate_canonical', side_effect=OSError('SECRET')), \
                contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(carrier.main(['--check']), 125)
        self.assertEqual(error.getvalue(), 'CYF_HEALTHMON_CHECK_ERROR=canonical_unavailable\n')

    def test_content_hash_still_enforced(self):
        info = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o755, st_uid=0, st_nlink=1, st_size=100)
        with mock.patch.object(carrier.os, 'open', return_value=9), \
                mock.patch.object(carrier.os, 'close'), \
                mock.patch.object(carrier.os, 'fstat', return_value=info), \
                mock.patch.object(carrier, 'sha256_fd', return_value='0' * 64):
            with self.assertRaisesRegex(carrier.CarrierError, 'canonical_hash_mismatch'):
                carrier.validate_canonical()

    def test_file_identity_still_enforced(self):
        for changes in ({'st_uid': 1000}, {'st_nlink': 2}, {'st_mode': stat.S_IFREG | 0o777},
                        {'st_mode': stat.S_IFLNK | 0o755}):
            fields = dict(st_mode=stat.S_IFREG | 0o755, st_uid=0, st_nlink=1, st_size=100)
            fields.update(changes)
            with self.subTest(changes=changes), \
                    mock.patch.object(carrier.os, 'open', return_value=9), \
                    mock.patch.object(carrier.os, 'close'), \
                    mock.patch.object(carrier.os, 'fstat', return_value=types.SimpleNamespace(**fields)):
                with self.assertRaisesRegex(carrier.CarrierError, 'canonical_identity_invalid'):
                    carrier.validate_canonical()


class PreflightTests(unittest.TestCase):
    def preflight(self, result, carrier_hash=None):
        effects = monitor.Effects()
        with mock.patch.object(effects, '_trusted_canonical', return_value=True), \
                mock.patch.object(monitor, 'validate_trusted_executable'), \
                mock.patch.object(monitor, 'validate_regular'), \
                mock.patch.object(monitor, 'sha256_file', return_value=carrier_hash or monitor.RECOVERY_CARRIER_SHA256), \
                mock.patch.object(effects, '_run', return_value=result) as run:
            answer = effects.recovery_precondition('start', 'I000128-1790603942', 1)
        return answer, run

    def test_success(self):
        answer, run = self.preflight(dict(returncode=0, stdout='CYF_HEALTHMON_CANONICAL=OK\n', stderr=''))
        self.assertTrue(answer['permitted'])
        run.assert_called_once_with([monitor.MAIL_PYTHON, '-I', monitor.RECOVERY_CARRIER, '--check'], None)

    def test_stale_pin_is_deterministic_failure(self):
        answer, _ = self.preflight(dict(returncode=125, stdout='',
                                       stderr='CYF_HEALTHMON_CHECK_ERROR=canonical_hash_mismatch\n'))
        self.assertEqual(answer, dict(permitted=False, classification='canonical_hash_mismatch'))

    def test_wrong_carrier_never_executes(self):
        answer, run = self.preflight({}, carrier_hash='0' * 64)
        self.assertEqual(answer['classification'], 'recovery_carrier_hash_mismatch')
        run.assert_not_called()

    def test_unknown_error_is_not_exposed(self):
        answer, _ = self.preflight(dict(returncode=125, stdout='', stderr='SECRET'))
        self.assertEqual(answer, dict(permitted=False, classification='canonical_preflight_failed'))

    def test_success_requires_marker(self):
        answer, _ = self.preflight(dict(returncode=0, stdout='', stderr=''))
        self.assertEqual(answer, dict(permitted=False, classification='canonical_preflight_invalid'))

    def test_stale_pin_does_not_consume_recovery_attempt(self):
        class FakeEffects(monitor.Effects):
            def canonical_status(self):
                return dict(healthy=False, classification='stopped', recovery_safe=True, returncode=3)
            def web(self, marker):
                return dict(healthy=True, classification='web_ok')
            def public_api(self):
                return dict(healthy=False, classification='auth_boundary_invalid', http_status=502)
            def mysql(self):
                return dict(healthy=True, classification='mysql_reachable')
            def redis(self):
                return dict(healthy=True, classification='redis_reachable')
            def agent(self):
                return dict(healthy=True, classification='agent_active')
            def resources(self):
                return dict(healthy=False, classification='resources_below_canonical_minimum')
            def recover(self, *args):
                raise AssertionError('must not launch native recovery')
        effects = FakeEffects()
        state = monitor.initial_state(1000)
        state['component_streaks']['local_api'] = 2
        state['component_streaks']['public_api'] = 2
        machine = monitor.Monitor(effects, lambda state: None, clock=lambda: 1001,
                                  maintenance_check=lambda: False)
        with mock.patch.object(effects, '_trusted_canonical', return_value=True), \
                mock.patch.object(monitor, 'validate_trusted_executable'), \
                mock.patch.object(monitor, 'validate_regular'), \
                mock.patch.object(monitor, 'sha256_file', return_value=monitor.RECOVERY_CARRIER_SHA256), \
                mock.patch.object(effects, '_run', return_value=dict(returncode=125, stdout='',
                                  stderr='CYF_HEALTHMON_CHECK_ERROR=canonical_hash_mismatch\n')):
            result = machine.check_once(state, dict(email_enabled=False, web_marker='app',
                                                    reminder_interval_seconds=21600))
        self.assertEqual(result['recovery']['decision'], 'canonical_hash_mismatch')
        self.assertEqual(state['recovery']['attempts'], 0)
        self.assertFalse(state['recovery']['circuit_latched'])
        self.assertIsNone(state['recovery']['in_flight'])


class EmailTests(unittest.TestCase):
    def send(self, result):
        effects = monitor.Effects()
        with mock.patch.object(monitor, 'validate_trusted_executable'), \
                mock.patch.object(monitor, 'validate_regular'), \
                mock.patch.object(monitor, 'sha256_file', return_value=monitor.MAIL_HELPER_SHA256), \
                mock.patch.object(effects, '_run', return_value=result), \
                mock.patch.object(monitor, 'guard_log') as log:
            answer = effects.send_email('test', 'test')
        return answer, log

    def test_auth_error_is_actionable_and_sanitized(self):
        answer, log = self.send(dict(returncode=1, stderr="smtplib.SMTPAuthenticationError: (526, b'SECRET')\n"))
        self.assertEqual(answer, (False, 'smtp_authentication_failed_526'))
        log.assert_called_once_with('smtp_authentication_failed_526')

    def test_other_errors_are_not_leaked(self):
        answer, log = self.send(dict(returncode=1, stderr='SECRET'))
        self.assertEqual(answer, (False, 'helper_failed'))
        log.assert_called_once_with('helper_failed')

    def test_smtp_acceptance_is_not_inbox_delivery(self):
        answer, log = self.send(dict(returncode=0, stderr=''))
        self.assertEqual(answer, (True, 'helper_accepted'))
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
