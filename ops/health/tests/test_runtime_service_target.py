"""The retired engine service must never be the live Runtime health target."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


class RuntimeServiceTargetTest(unittest.TestCase):
    def test_live_runtime_service_is_checked(self):
        path = Path(__file__).resolve().parents[1] / 'cyf-juyiting-health.py'
        spec = importlib.util.spec_from_file_location('runtime_service_health', str(path))
        health = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(health)
        with patch.object(health.Effects, '_run', return_value={
                'returncode': 3, 'stdout': 'inactive\n'}) as run:
            self.assertEqual(health.Effects().agent(), {
                'healthy': False, 'classification': 'agent_inactive'})
        run.assert_called_once_with([
            '/usr/bin/systemctl', 'is-active',
            'cyf-agent-runtime-v1@unified.service'], 5)


if __name__ == '__main__':
    unittest.main()
