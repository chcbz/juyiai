import importlib.machinery
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[4]
controller = importlib.machinery.SourceFileLoader(
    'release_schedule_controller', str(ROOT / 'ops/ci/aliyun-flow/release_schedule_controller.py')
).load_module()


class ReleaseScheduleControllerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cyf-release-schedule-')
        self.root = pathlib.Path(self.tmp.name)
        controller.ROOT = self.root
        controller.INTENTS = self.root/'intents'
        controller.LOCK = self.root/'controller.lock'
        controller.ALLOWLIST = self.root/'allowlist.json'

    def tearDown(self):
        self.tmp.cleanup()

    def test_written_intent_is_exact_run_bound(self):
        target = controller.TARGETS['backend-nightly']
        path = controller.write_intent(target, '77', 'a'*40)
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual({
            'schema_version': 1, 'kind': 'backend-nightly', 'pipeline_id': '5260799',
            'run_id': '77', 'commit': 'a'*40, 'issued_at': json.loads(path.read_text())['issued_at'],
        }, json.loads(path.read_text()))

    def test_same_deployed_commit_does_not_start_flow(self):
        target = controller.TARGETS['backend-nightly']
        target = dict(target, record=self.root/'approval.json')
        controller.TARGETS['backend-nightly'] = target
        target['record'].write_text(json.dumps({'source_commit_sha': 'a'*40}))
        target['record'].chmod(0o600)
        controller.ALLOWLIST.write_text('{}')
        with mock.patch.object(controller, 'remote_develop', return_value='a'*40), \
                mock.patch.object(controller, 'flow') as flow:
            self.assertEqual(0, controller.start_once('backend-nightly'))
        self.assertFalse(flow.called)


if __name__ == '__main__':
    unittest.main()
