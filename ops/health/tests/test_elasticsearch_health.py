"""Local injected probes only; never touches production ES or mail."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from test_cyf_juyiting_health import health, FakeEffects, Clock


class ElasticsearchHealthTests(unittest.TestCase):
    def probe(self, responses):
        effects = health.Effects()
        with patch.object(effects, '_elasticsearch_json', side_effect=responses) as call:
            result = effects.elasticsearch()
        return result, call

    def good_search(self):
        return {'timed_out': False, '_shards': {'total': 1, 'successful': 1, 'failed': 0}}

    def test_green_and_single_node_yellow_are_searchable(self):
        for color in ('green', 'yellow'):
            result, calls = self.probe([{'status': color, 'timed_out': False}, self.good_search()])
            self.assertTrue(result['healthy'])
            self.assertEqual('es_search_ok_' + color, result['classification'])
            self.assertEqual('/chat_memory/_search?size=0&terminate_after=1', calls.call_args[0][0])

    def test_red_timeout_and_unknown_cluster_fail(self):
        for response in ({'status': 'red', 'timed_out': False}, {'status': 'green', 'timed_out': True}, {}):
            result, calls = self.probe([response])
            self.assertFalse(result['healthy'])
            self.assertEqual(1, calls.call_count)

    def test_partial_missing_and_timeout_search_fail(self):
        for response in ({}, {'timed_out': True, '_shards': {'total': 1, 'successful': 1, 'failed': 0}},
                         {'timed_out': False, '_shards': {'total': 1, 'successful': 0, 'failed': 1}}):
            result, _ = self.probe([{'status': 'green', 'timed_out': False}, response])
            self.assertFalse(result['healthy'])

    def test_auth_missing_index_and_connection_errors_are_not_empty_success(self):
        for error in (HTTPError('local', 401, 'secret', {}, None), HTTPError('local', 404, 'secret', {}, None), URLError('secret')):
            result, _ = self.probe([error])
            self.assertFalse(result['healthy'])
            self.assertNotIn('secret', str(result))

    def test_es_incident_alerts_without_api_restart_and_recovers(self):
        clock = Clock()
        effects = FakeEffects()
        effects.es_result = {'healthy': False, 'classification': 'es_http_404'}
        state = health.initial_state(clock.now)
        monitor = health.Monitor(effects, lambda s: None, clock, lambda: False)
        config = {'schema_version': 1, 'web_marker': 'app', 'email_enabled': True,
                  'reminder_interval_seconds': 21600}
        for _ in range(3):
            monitor.check_once(state, config)
            clock.now += 60
        self.assertIn('elasticsearch', state['incident']['components'])
        self.assertEqual([], effects.recoveries)
        self.assertTrue(effects.mail_calls)
        effects.es_result = {'healthy': True, 'classification': 'es_search_ok_green'}
        for _ in range(3):
            monitor.check_once(state, config)
            clock.now += 60
        self.assertIsNone(state['incident'])
        self.assertEqual([], effects.recoveries)
