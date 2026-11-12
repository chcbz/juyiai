"""Checkout contract only: tiny isolated Git fixtures, no app build or network."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]

class ShallowCheckoutTest(unittest.TestCase):
    def test_release_is_shallow_and_asset_profiles_restore_history(self):
        text = (BASE/'templates/frontend-develop-release.yaml').read_text()
        self.assertIn('    cloneDepth: 1\n', text)
        block = text.split('                # Release tests use the current tree.', 1)[1]
        block = block.split('                manager=', 1)[0]
        script = '# Release tests use the current tree.' + block
        def git(*args, **kwargs):
            return subprocess.check_output(['git']+list(args), stderr=subprocess.DEVNULL,
                                           universal_newlines=True, **kwargs).strip()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'source'; source.mkdir()
            git('init', str(source)); git('-C', str(source), 'checkout', '-b', 'develop')
            for i in range(2):
                (source/'data').write_text(str(i))
                git('-C', str(source), 'add', 'data')
                git('-C', str(source), '-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid',
                    'commit', '-m', str(i))
            sha = git('-C', str(source), 'rev-parse', 'HEAD')
            for profile in ('release', 'assets', 'all', 'unknown'):
                checkout = Path(temp)/profile
                git('clone', '--depth=1', '--branch=develop', source.as_uri(), str(checkout))
                env = dict(os.environ, CYF_TEST_PROFILE=profile, CI_COMMIT_REF_NAME='develop', CI_COMMIT_SHA=sha)
                result = subprocess.run(['bash', '-eu', '-c', script], cwd=str(checkout), env=env,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                self.assertEqual(result.returncode, 1 if profile=='unknown' else 0, result.stderr)
                if profile=='unknown': continue
                shallow = git('-C', str(checkout), 'rev-parse', '--is-shallow-repository')
                self.assertEqual(shallow, 'true' if profile=='release' else 'false')
                self.assertEqual(git('-C', str(checkout), 'rev-parse', 'HEAD'), sha)
                self.assertIn('CYF_SOURCE_CHECKOUT', result.stdout)
                if profile != 'release':
                    self.assertEqual(git('-C', str(checkout), 'show', 'HEAD~1:data'), '0')

if __name__=='__main__': unittest.main()
