"""Frontend manifest versions: actual release prereleases are valid SemVer."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[4]


class FrontendSemverTest(unittest.TestCase):
    def test_strict_manifest_versions_without_new_dependency(self):
        template = (ROOT / 'ops/ci/aliyun-flow/templates/frontend-develop-release.yaml').read_text()
        line = next(line for line in template.splitlines() if "throw Error('Invalid package version')" in line)
        regex = line.split("||!", 1)[1].split('.test(packageVersion)', 1)[0]
        cases = {
            '0.0.0': True, '1.14.0': True,
            '1.14.0-consolidated.20261009': True,
            '1.0.0-alpha.0': True, '1.0.0-00a': True,
            '1.0.0+001': True, '1.0.0-alpha.1+build.003': True,
            '01.0.0': False, '1.0': False, 'v1.0.0': False,
            '1.0.0-01': False, '1.0.0-': False, '1.0.0+': False,
            '1.0.0-alpha..1': False, '1.0.0+build..1': False,
            '1.0.0 x': False,
        }
        script = 'const r=' + regex + ';const c=' + json.dumps(cases) + ';for(const [v,ok] of Object.entries(c)){if(r.test(v)!==ok)throw Error(v)}'
        result = subprocess.run(['node', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
