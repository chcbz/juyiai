import importlib.machinery
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
policy = importlib.machinery.SourceFileLoader(
    'release_schedule_policy', str(ROOT / 'ops/ci/aliyun-flow/release_schedule_policy.py')
).load_module()


class ReleaseSchedulePolicyTest(unittest.TestCase):
    def test_user_defined_frontend_major_boundary(self):
        self.assertEqual('scheduled-major', policy.frontend_release_lane('1.0.7', '1.2.0'))
        self.assertEqual('immediate', policy.frontend_release_lane('1.0.7', '1.1.0'))
        self.assertEqual('immediate', policy.frontend_release_lane('1.0.7', '1.0.8'))

    def test_major_semver_change_is_scheduled(self):
        self.assertEqual('scheduled-major', policy.frontend_release_lane('1.9.9', '2.0.0'))

    def test_unknown_version_does_not_create_a_rejection_path(self):
        self.assertEqual('unclassified', policy.frontend_release_lane('1.0.0', '1.2.0-rc.1'))
        self.assertEqual('unclassified', policy.frontend_release_lane(None, '1.2.0'))

    def test_backend_daytime_is_build_only(self):
        self.assertEqual('release-window', policy.backend_release_lane(0))
        self.assertEqual('build-only', policy.backend_release_lane(6))
        self.assertEqual('build-only', policy.backend_release_lane(23))


if __name__ == '__main__':
    unittest.main()
