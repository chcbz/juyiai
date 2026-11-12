"""Offline tests for pending online-index verification; no host or Flow mutation."""
import contextlib
import hashlib
import importlib.machinery
import io
import json
from pathlib import Path
import unittest
import urllib.error
from unittest import mock


ROOT = Path(__file__).resolve().parents[4]
HELPER = ROOT / 'ops/ci/aliyun-flow/host/cyf-web-flow-deploy'


def load():
    return importlib.machinery.SourceFileLoader(
        'web_flow_cache_verifier_fixture', str(HELPER)).load_module()


class Response(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class CacheVerifierTest(unittest.TestCase):
    def setUp(self):
        self.web = load()
        self.expected_bytes = b'<html>expected</html>'
        self.old_bytes = b'<html>previous</html>'
        self.expected = {'index.html': {
            'size': len(self.expected_bytes),
            'sha256': hashlib.sha256(self.expected_bytes).hexdigest(),
        }}
        self.identity = ('4403172', '99', 'a' * 40)

    def test_waits_past_three_known_prior_cache_reads_for_exact_match(self):
        responses = [Response(self.old_bytes) for _ in range(4)] + [Response(self.expected_bytes)]
        sleeps = []
        stderr = io.StringIO()
        with mock.patch.object(self.web.urllib.request, 'urlopen', side_effect=responses) as urlopen, \
                mock.patch.object(self.web.time, 'sleep', side_effect=sleeps.append), \
                contextlib.redirect_stderr(stderr):
            self.web.verify_online_index(*self.identity, self.expected,
                                         hashlib.sha256(self.old_bytes).hexdigest())

        self.assertEqual(urlopen.call_count, 5)
        self.assertEqual(sleeps, [self.web.ONLINE_VERIFY_POLL_DELAY_SECONDS] * 4)
        events = [json.loads(line.split(' ', 1)[1]) for line in stderr.getvalue().splitlines()]
        self.assertEqual([event['response_kind'] for event in events[:-1]], ['known_prior_index'] * 4)
        self.assertTrue(events[-1]['match'])
        self.assertNotIn('response_kind', events[-1])

    def test_wrong_hash_is_never_accepted_and_outer_cancellation_propagates(self):
        wrong = Response(b'<html>unrelated</html>')
        stderr = io.StringIO()
        with mock.patch.object(self.web.urllib.request, 'urlopen', return_value=wrong), \
                mock.patch.object(self.web.time, 'sleep', side_effect=KeyboardInterrupt), \
                contextlib.redirect_stderr(stderr):
            with self.assertRaises(KeyboardInterrupt):
                self.web.verify_online_index(*self.identity, self.expected,
                                             hashlib.sha256(self.old_bytes).hexdigest())

        event = json.loads(stderr.getvalue().splitlines()[0].split(' ', 1)[1])
        self.assertFalse(event['match'])
        self.assertEqual(event['response_kind'], 'unexpected_response')
        self.assertNotEqual(event['actual_sha256'], self.expected['index.html']['sha256'])

    def test_request_error_remains_pending_until_exact_response(self):
        responses = [urllib.error.URLError('temporary network error'), Response(self.expected_bytes)]
        stderr = io.StringIO()
        with mock.patch.object(self.web.urllib.request, 'urlopen', side_effect=responses), \
                mock.patch.object(self.web.time, 'sleep') as sleep, \
                contextlib.redirect_stderr(stderr):
            self.web.verify_online_index(*self.identity, self.expected)

        sleep.assert_called_once_with(self.web.ONLINE_VERIFY_POLL_DELAY_SECONDS)
        events = [json.loads(line.split(' ', 1)[1]) for line in stderr.getvalue().splitlines()]
        self.assertEqual(events[0]['error_type'], 'URLError')
        self.assertEqual(events[0]['response_kind'], 'request_error')
        self.assertFalse(events[0]['match'])
        self.assertTrue(events[1]['match'])


if __name__ == '__main__':
    unittest.main()
