import importlib.util
import os
import unittest
p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cyf-juyiting-health.py')
spec = importlib.util.spec_from_file_location('health', p)
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)

class RuntimeChannelHealthTest(unittest.TestCase):
    def snapshot(self):
        return dict(version=1, pid=123, observedAt=100000, heartbeatIntervalMs=30000,
                    agents=[dict(connected=True, registered=True, ready=True, channelState='ready', lastPresenceAckAt=90000)])

    def test_ready_requires_fresh_receipt(self):
        x = self.snapshot()
        self.assertTrue(health.assess_agent_snapshot(x,123,100000)['healthy'])
        x['agents'][0]['lastPresenceAckAt'] = None
        self.assertEqual(health.assess_agent_snapshot(x,123,100000)['classification'], 'agent_presence_ack_stale')

    def test_old_process_stale_missing_and_isolated_are_not_healthy(self):
        for mutation in [lambda x:x.update(pid=122),lambda x:x.update(observedAt=1),lambda x:x.update(agents=[]),
                         lambda x:x['agents'][0].update(registered=False),lambda x:x['agents'][0].update(channelState='isolated'),
                         lambda x:x['agents'][0].update(ready=False)]:
            x=self.snapshot();mutation(x)
            self.assertFalse(health.assess_agent_snapshot(x,123,100000)['healthy'])

    def test_current_process_oom_only(self):
        text='2026-10-21T07:35 ERROR 122 --- [thread] java.lang.OutOfMemoryError: Metaspace'
        self.assertFalse(health.current_api_memory_failure(text,123))
        self.assertTrue(health.current_api_memory_failure(text,122))
        self.assertFalse(health.current_api_memory_failure('2026 INFO 123 --- MetaspaceSize=192m',123))

    def test_probe_reads_private_nonexecutable_snapshot_and_actual_pid(self):
        import tempfile
        import json
        import time
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'health.json')
            data = self.snapshot()
            data['observedAt'] = int(time.time()*1000)
            data['agents'][0]['lastPresenceAckAt'] = data['observedAt']
            with open(path,'w') as f: json.dump(data,f)
            os.chmod(path,0o600)
            effects = health.Effects()
            with mock.patch.object(health,'AGENT_HEALTH_PATH',path), mock.patch.object(effects,'_run',side_effect=[
                dict(returncode=0,stdout='active'),dict(returncode=0,stdout='123')]):
                self.assertTrue(effects.agent()['healthy'])

    def test_canonical_pin_mismatch_is_preflight_denial(self):
        from unittest import mock
        effects = health.Effects()
        with mock.patch.object(effects, '_trusted_canonical', return_value=True), \
             mock.patch.object(health, 'validate_trusted_executable'), \
             mock.patch.object(health, 'validate_regular'), \
             mock.patch.object(health, 'sha256_file', return_value=health.RECOVERY_CARRIER_SHA256), \
             mock.patch.object(effects, '_run', return_value=dict(returncode=125, stdout='', stderr='CYF_HEALTHMON_CHECK_ERROR=canonical_hash_mismatch\n')):
            self.assertEqual(effects.recovery_precondition('start', 'I000056-1788792725', 1),
                             dict(permitted=False, classification='canonical_hash_mismatch'))

    def test_carrier_check_only_validates_never_launches(self):
        from unittest import mock
        import io
        cp = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cyf-juyiting-recovery-carrier.py')
        spec = importlib.util.spec_from_file_location('carrier_health_test', cp)
        carrier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(carrier)
        with mock.patch.object(carrier, 'validate_canonical') as check, \
             mock.patch.object(carrier.os, 'execve', side_effect=AssertionError('must not launch')), \
             mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(carrier.main(['--check']), 0)
            check.assert_called_once_with()
            self.assertEqual(out.getvalue().strip(), 'CYF_HEALTHMON_CANONICAL=OK')
        with mock.patch.object(carrier, 'validate_canonical', side_effect=carrier.CarrierError('canonical_hash_mismatch')), \
             mock.patch('sys.stderr', new_callable=io.StringIO) as err:
            self.assertEqual(carrier.main(['--check']), 125)
            self.assertIn('canonical_hash_mismatch', err.getvalue())
