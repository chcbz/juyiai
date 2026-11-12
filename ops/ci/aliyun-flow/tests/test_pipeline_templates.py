import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[4]
TEMPLATES = ROOT / "ops/ci/aliyun-flow/templates"
STANDARD_ALLOWED_STEPS = {"ArtifactUpload", "CustomEnvironmentBuild", "JavaBuild"}


def read_template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def standard_step_enums(text):
    return set(re.findall(r"^\s*step:\s*([A-Za-z][A-Za-z0-9]*)\s*$", text, re.MULTILINE))


class PipelineTemplateTest(unittest.TestCase):
    def test_templates_are_ci_only_and_develop_bound(self):
        for name in ("backend-develop-ci.yaml", "frontend-develop-ci.yaml"):
            text = read_template(name)
            self.assertNotIn("schema: tb", text)
            self.assertIn("type: git", text)
            self.assertIn("defaultWorkspace: repo_0", text)
            self.assertIn("branch: develop", text)
            self.assertIn("branchesFilter: develop", text)
            self.assertIn("triggerEvents: []", text)
            self.assertNotRegex(text, r"(?im)^\s*component:\s*VMDeploy\s*$")
            self.assertNotRegex(text, r"(?im)^\s*(?:deploy|deployment):\s*$")
            self.assertNotRegex(text, r"(?i)(?:systemctl|/usr/local/sbin/|kubectl|helm\s+release)")

    def test_templates_use_only_reviewed_standard_step_enums(self):
        for name in ("backend-develop-ci.yaml", "frontend-develop-ci.yaml"):
            steps = standard_step_enums(read_template(name))
            self.assertTrue(steps)
            self.assertTrue(steps <= STANDARD_ALLOWED_STEPS)

    def test_frontend_custom_environment_preserves_full_ci_gate_and_artifact(self):
        text = read_template("frontend-develop-ci.yaml")
        self.assertIn("step: CustomEnvironmentBuild", text)
        self.assertIn("image: build-steps-public-registry.cn-beijing.cr.aliyuncs.com/build-steps/alinux3:latest", text)
        self.assertIn('test "${CI_COMMIT_REF_NAME:-}" = develop', text)
        self.assertIn('test -n "${CI_COMMIT_SHA:-}"', text)
        self.assertIn('test "$(git rev-parse HEAD)" = "$CI_COMMIT_SHA"', text)
        self.assertIn("--setopt=gpgcheck=1", text)
        self.assertIn("6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6", text)
        self.assertIn("https://mirrors.aliyun.com/nodejs-release/v24.22.1/node-v24.22.1-linux-x64.tar.xz", text)
        self.assertIn("https://cdn.npmmirror.com/binaries/node/v24.22.1/node-v24.22.1-linux-x64.tar.xz", text)
        self.assertIn("node-v24.22.1-linux-x64/bin", text)
        self.assertIn('test "$(node --version)" = v24.22.1', text)
        self.assertEqual(text.count("npm ci"), 1)
        self.assertIn("npm ci --include=dev", text)
        self.assertIn("--registry=https://registry.npmmirror.com", text)
        self.assertIn("--replace-registry-host=npmjs", text)
        self.assertIn("--fetch-timeout=120000", text)
        self.assertIn("--no-audit --no-fund", text)
        self.assertIn("test -x node_modules/.bin/vite", text)
        self.assertIn("test -f node_modules/vite/bin/vite.js", text)
        self.assertNotRegex(text, r"(?m)^\s*npm install(?:\s|$)")
        self.assertLess(text.index("npm ci"), text.index("npm run test"))
        self.assertLess(text.index("npm run test"), text.index("npm run build"))
        self.assertIn('cp -a dist "$export_root/dist"', text)
        self.assertIn('cp -a mochawesome-report "$export_root/mochawesome-report"', text)
        self.assertIn("step: ArtifactUpload", text)
        self.assertIn("- _cyf_web_develop_ci_export/", text)
        self.assertNotRegex(text, r"(?i)(?:token|password|secret|authorization)\s*:")

    def test_frontend_release_manifest_carries_package_version(self):
        text = read_template("frontend-develop-release.yaml")
        self.assertIn("JSON.parse(fs.readFileSync('package.json','utf8')).version", text)
        self.assertIn('package_version:packageVersion', text)

    def test_backend_host_installer_uses_candidate_bound_ticket_argument(self):
        text = (ROOT / "ops/ci/aliyun-flow/host/cyf-api-flow-auto-approve-install").read_text(encoding="utf-8")
        self.assertIn("len(sys.argv) not in (4, 5, 6)", text)
        self.assertIn("expected_ticket = sys.argv[4]", text)
        self.assertIn("LEGACY_EXPECTED_TICKET_FILE", text)
        self.assertIn("receipt.get('ticket_sha256') != expected_ticket", text)
        self.assertNotRegex(text, r"EXPECTED_TICKET\s*=\s*['\"][0-9a-f]{64}")

    def test_backend_keeps_only_a_fail_closed_ticket_placeholder(self):
        text = read_template("backend-develop-ci.yaml")
        self.assertIn("step: JavaBuild", text)
        self.assertIn("CYF_FLOW_GRADLE_ACTIVE=1", text)
        self.assertIn(":starter:bootJar", text)
        self.assertIn("q37x7n8snxqq744z", text)
        self.assertNotIn("__FILL_", text)
        self.assertIn("step: ArtifactUpload", text)
        self.assertNotRegex(text, r"(?i)(?:ticket_?sha256|ticketsha256)\s*=\s*['\"]?[0-9a-f]{64}")
        self.assertNotRegex(text, r"\b[0-9a-f]{64}\b")


if __name__ == "__main__":
    unittest.main()
