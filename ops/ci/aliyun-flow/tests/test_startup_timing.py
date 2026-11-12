"""In-memory arithmetic only; no app, DB, subprocess, or network."""
import importlib.util
import json
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'diagnostics' / 'startup_timing.py'
spec = importlib.util.spec_from_file_location('startup_timing', str(PATH))
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)


def mark(component, pid, point, time):
    return 'CYF_DEPLOY_TIMING component={} pid={} point={} monotonic_s={} wall=ignored'.format(component, pid, point, time)


class TimingTest(unittest.TestCase):
    def test_timezone_formats(self):
        a = timing.timestamp('2026-09-13T17:00:00.123+08:00')
        self.assertEqual(a, timing.timestamp('[2026-09-13T17:00:00.123+0800]'))
        self.assertEqual(a, timing.timestamp('2026-09-13T09:00:00.123Z'))
        self.assertEqual(a, timing.timestamp('wall=2026-09-13T09:00:00.123000999Z'))

    def test_spring_intervals_and_sensitive_body_omitted(self):
        report = timing.spring_timing('\n'.join([
            '2026-09-13T17:00:01.000+08:00 Starting JiaApplication password=do-not-output',
            '[2026-09-13T17:00:02.000+0800][2s][gc] GC(0) Pause Young 8M->1M(12M) 123.0ms',
            '[2026-09-13T17:00:02.000+0800][2s][gc,start] GC(0) Pause Young',
            '2026-09-13T17:00:02.000+08:00 Skipping MapperFactoryBean secret=do-not-output',
            '2026-09-13T17:00:04.000+08:00 Skipping MapperFactoryBean',
            '2026-09-13T17:00:10.000+08:00 Started JiaApplication in 10.0 seconds (process running for 11.0)',
            '2026-09-13T17:00:11.000+08:00 Skipping MapperFactoryBean',
        ]))
        self.assertEqual(report['intervalSumSeconds'], 10)
        self.assertEqual(report['mapperDuplicateWarnings'], 2)
        self.assertEqual(report['gc']['springWindowPauseCount'], 1)
        self.assertEqual(report['gc']['springWindowPauseSeconds'], .123)
        self.assertNotIn('do-not-output', json.dumps(report))
        self.assertTrue(all(not item['exclusiveComponentTime'] for item in report['intervals']))

    def test_missing_started_unknown(self):
        self.assertEqual(timing.spring_timing('nothing')['status'], 'unknown')

    def test_multiple_boots_unknown(self):
        line = '2026-09-13T17:00:10.000+08:00 Started App in 10.0 seconds (process running for 11.0)'
        self.assertEqual(timing.spring_timing(line+'\n'+line)['status'], 'unknown')

    def test_nested_processes_not_mixed(self):
        text = '\n'.join([mark('installer', 1, 'start_wait.begin', 1),
                          mark('lifecycle', 2, 'health_wait.begin', 2),
                          mark('lifecycle', 2, 'health_wait.end', 5),
                          mark('installer', 1, 'start_wait.end', 6)])
        result = timing.deploy_timing(text)
        self.assertEqual([span['seconds'] for span in result['spans']], [3, 5])
        self.assertNotIn('totalSeconds', result)

    def test_missing_failed_and_clock_regression_not_zero(self):
        for lines, reason in [([mark('installer', 1, 'backup.begin', 1)], 'missing_end'),
                              ([mark('installer', 1, 'backup.end', 2)], 'missing_begin'),
                              ([mark('lifecycle', 1, 'status_health.begin', 1), mark('lifecycle', 1, 'status_health.failed', 2)], 'failed'),
                              ([mark('installer', 1, 'backup.begin', 4), mark('installer', 1, 'backup.end', 2)], 'clock_regression')]:
            result = timing.deploy_timing('\n'.join(lines))
            self.assertEqual(result['spans'], [])
            self.assertEqual(result['incomplete'][0]['reason'], reason)
            self.assertNotIn('seconds', result['incomplete'][0])

    def test_repeated_pair_kept_separate(self):
        text = '\n'.join(mark('lifecycle', 2, 'status.'+kind, tick)
                         for kind, tick in [('begin', 1), ('end', 3), ('begin', 4), ('end', 7)])
        self.assertEqual([s['seconds'] for s in timing.deploy_timing(text)['spans']], [2, 3])

    def test_overwritten_begin_reported(self):
        text = '\n'.join(mark('installer', 1, 'backup.'+kind, tick)
                         for kind, tick in [('begin', 1), ('begin', 2), ('end', 4)])
        result = timing.deploy_timing(text)
        self.assertEqual(result['incomplete'][0]['reason'], 'repeated_begin')
        self.assertEqual(result['spans'][0]['seconds'], 2)

    def test_cross_pid_not_paired(self):
        result = timing.deploy_timing(mark('installer', 1, 'backup.begin', 1)+'\n'+mark('installer', 2, 'backup.end', 2))
        self.assertFalse(result['spans'])
        self.assertEqual(len(result['incomplete']), 2)



class ActualStartupStepTest(unittest.TestCase):
    def line(self, event, identity, parent, tick, name='spring.beans.instantiate', thread=1, extra=''):
        return ('CYF_STARTUP_STEP event={} id={} parent={} thread={} name={} '
                'wall=2026-09-13T10:00:00.000Z monotonic_ns={}{}').format(
                    event, identity, parent, thread, name, tick, ' '+extra if extra else '')

    def test_exact_boundaries_and_child_subtraction(self):
        data = '\n'.join([
            self.line('BEGIN', 1, 0, 0), self.line('BEGIN', 2, 1, 10),
            self.line('TAG', 2, 1, 11, extra='key=beanName value=fixture'),
            self.line('END', 2, 1, 30, extra='duration_ns=20 outcome=ended'),
            self.line('END', 1, 0, 50, extra='duration_ns=50 outcome=success'),
            'CYF_STARTUP_SUMMARY steps=2 open=0 output_ns=1 output_failures=0'])
        result = timing.startup_steps(data)
        self.assertTrue(result['traceComplete'])
        self.assertEqual(result['steps'][0]['seconds'], 50 / 1e9)
        self.assertEqual(result['steps'][0]['selfWallSeconds'], 30 / 1e9)
        self.assertEqual(result['steps'][1]['tags']['beanName'], 'fixture')
        self.assertEqual(result['steps'][1]['outcome'], 'ended')

    def test_missing_end_unknown_not_next_log_timestamp(self):
        data = self.line('BEGIN', 1, 0, 10)+'\n2026-09-13T11:00:00.000+08:00 unrelated completion'
        result = timing.startup_steps(data)
        self.assertFalse(result['traceComplete'])
        self.assertIsNone(result['steps'][0]['seconds'])
        self.assertIsNone(result['steps'][0]['selfWallSeconds'])

    def test_truncation_keeps_elapsed_but_forbids_self_time(self):
        data = '\n'.join([self.line('BEGIN', 1, 0, 10),
                          self.line('END', 1, 0, 20, extra='duration_ns=10 outcome=ended'),
                          'CYF_STARTUP_SUMMARY steps=3 open=0 output_ns=0 output_failures=0'])
        result = timing.startup_steps(data)
        self.assertEqual(result['steps'][0]['seconds'], 10 / 1e9)
        self.assertIsNone(result['steps'][0]['selfWallSeconds'])
        self.assertFalse(result['traceComplete'])

    def test_negative_monotonic_epoch_allowed_but_duration_mismatch_rejected(self):
        data = '\n'.join([self.line('BEGIN', 1, 0, -10),
                          self.line('END', 1, 0, -5, extra='duration_ns=9 outcome=failed')])
        result = timing.startup_steps(data)
        self.assertEqual(result['steps'][0]['status'], 'invalid_duration')
        self.assertIsNone(result['steps'][0]['seconds'])

    def test_failed_scope_duration_is_still_measured(self):
        data = '\n'.join([self.line('BEGIN', 1, 0, 0),
                          self.line('END', 1, 0, 10, extra='duration_ns=10 outcome=failed'),
                          'CYF_STARTUP_SUMMARY steps=1 open=0 output_ns=0 output_failures=0'])
        row = timing.startup_steps(data)['steps'][0]
        self.assertEqual(row['status'], 'measured')
        self.assertEqual(row['outcome'], 'failed')

    def test_cross_thread_parent_rejected(self):
        data = '\n'.join([self.line('BEGIN', 1, 0, 0), self.line('BEGIN', 2, 1, 1, thread=2),
                          self.line('END', 2, 1, 4, thread=2, extra='duration_ns=3 outcome=ended'),
                          self.line('END', 1, 0, 5, extra='duration_ns=5 outcome=ended'),
                          'CYF_STARTUP_SUMMARY steps=2 open=0 output_ns=0 output_failures=0'])
        result = timing.startup_steps(data)
        self.assertFalse(result['traceComplete'])
        self.assertEqual(result['errors'][0]['reason'], 'invalid_parent_interval')

    def test_lifecycle_requires_actual_trace_start_and_debug_end(self):
        log = ('2026-09-13T10:00:00.000+08:00 TRACE o.s.c.s.DefaultLifecycleProcessor : Starting bean \'fixture\' of type [Fixture]\n'
               '2026-09-13T10:00:02.000+08:00 DEBUG o.s.c.s.DefaultLifecycleProcessor : Successfully started bean \'fixture\'')
        result = timing.lifecycle_steps(log)
        self.assertEqual(result['spans'][0]['seconds'], 2)
        result = timing.lifecycle_steps(log.split('\n')[1])
        self.assertFalse(result['spans'])
        self.assertEqual(result['incomplete'][0]['reason'], 'missing_TRACE_begin')


if __name__ == '__main__':
    unittest.main()
