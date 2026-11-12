import ast
import pathlib
import re
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[4]


class StaticContractTest(unittest.TestCase):
    def test_cloud_runner_shell_is_valid_and_uses_orchestrator(self):
        runner = ROOT / "ops/ci/aliyun-flow/run-cloud.sh"
        subprocess.check_call(["sh", "-n", str(runner)])
        text = runner.read_text(encoding="utf-8")
        self.assertIn("cyf_orchestrator.py", text)
        self.assertIn("flow-remote run", text)
        self.assertNotIn("./gradlew", text)

    def test_init_script_keeps_cold_build_outside_checkout(self):
        text = (ROOT / "ops/ci/aliyun-flow/cold-init.gradle").read_text(encoding="utf-8")
        self.assertIn("includeBuild(localPlugin.absolutePath)", text)
        self.assertIn("CYF_FLOW_BUILD_ROOT", text)
        self.assertIn("layout.buildDirectory", text)
        self.assertIn("Nested Gradle Exec task is forbidden", text)
        self.assertNotIn("mavenLocal()", text)

    def test_plugin_management_include_build_uses_string_path(self):
        # Cloud Run1 failed because PluginManagementSpec accepts String, not File.
        text = (ROOT / "ops/ci/aliyun-flow/cold-init.gradle").read_text(encoding="utf-8")
        self.assertIn("def localPlugin = new File(settings.settingsDir, 'plugin')", text)
        self.assertIn("if (new File(localPlugin, 'settings.gradle').isFile())", text)
        self.assertRegex(text, r"\bincludeBuild\(localPlugin\.absolutePath\)")
        self.assertNotRegex(text, r"\bincludeBuild\(\s*localPlugin\s*\)")

    def test_orchestrator_exposes_narrow_dispatcher(self):
        result = subprocess.check_output([
            "python3", str(ROOT / "ops/orchestration/cyf_orchestrator.py"), "flow-remote", "--", "--help"
        ], stderr=subprocess.STDOUT).decode("utf-8")
        self.assertIn("issue", result)
        self.assertIn("run", result)
        self.assertIn("inspect", result)

    def test_r3_fixed_consumer_endpoints_and_no_publish_credentials(self):
        text = (ROOT / "ops/ci/aliyun-flow/cold-init.gradle").read_text(encoding="utf-8")
        self.assertEqual({
            "releaseRepository": "https://packages.aliyun.com/5fb7d76ee6f9d07f148529c7/maven/2049636-release-r6d3t8",
            "snapshotRepository": "https://packages.aliyun.com/5fb7d76ee6f9d07f148529c7/maven/2049636-snapshot-tdmfld",
        }, dict(re.findall(r"def (releaseRepository|snapshotRepository) = '([^']+)'", text)))
        self.assertIn("https://packages.aliyun.com:443/", text)
        self.assertIn("allowInsecureProtocol = false", text)
        self.assertIn("authentication { basic(BasicAuthentication) }", text)
        self.assertNotIn("HttpHeaderCredentials", text)
        self.assertIn("consumerRepositories(repositories, true)", text)
        self.assertIn("consumerRepositories(repositories, false)", text)
        self.assertIn("consumerRepositories(project.repositories, false)", text)
        self.assertIn("project.ext.repoUsername = ''", text)
        self.assertIn("project.ext.repoPassword = ''", text)
        self.assertNotRegex(text, r"project\.ext\.\w+\s*=\s*consumer")
        self.assertIn("childEnvironment.remove('CYF_MAVEN_USERNAME')", text)
        self.assertIn("childEnvironment.remove('CYF_MAVEN_PASSWORD')", text)
        self.assertIn("task instanceof Test || task instanceof JavaExec || task instanceof Exec", text)
        self.assertNotIn("snapshotRepository = null", text)

    def test_r3_opencv_hash_is_checked_at_resolution_not_task_completion(self):
        text = (ROOT / "ops/ci/aliyun-flow/cold-init.gradle").read_text(encoding="utf-8")
        bridge = (ROOT / "ops/orchestration/flow_remote.py").read_text(encoding="utf-8")
        pin = "323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4"
        self.assertIn(pin, text)
        self.assertIn(pin, bridge)
        self.assertIn("722802", text)
        self.assertIn("722802", bridge)
        self.assertIn("configuration.incoming.afterResolve", text)
        self.assertIn("incoming.artifacts.artifacts.each { artifact -> verifyOpenCv(artifact) }", text)
        self.assertIn("def jar = artifact.file", text)
        self.assertIn("actualSha256 != pinnedOpenCvSha256", text)
        self.assertIn("throw new GradleException('Resolved OpenCV JAR SHA-256/size drift rejected before consumption')", text)
        self.assertIn("excludeModule('org.opencv', 'opencv')", text)
        self.assertIn("opencv-resolved.json", text)
        self.assertNotIn("doLast {", text)

    def test_python_syntax_without_bytecode_or_external_tools(self):
        for path in [ROOT / "ops/orchestration/flow_remote.py"] + sorted((ROOT / "ops/ci/aliyun-flow/tests").glob("*.py")):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
