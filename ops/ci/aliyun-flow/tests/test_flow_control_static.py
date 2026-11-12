import ast
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[4]
CONTROL = ROOT / "ops/ci/aliyun-flow/flow-control.cjs"


class FlowControlStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONTROL.read_text(encoding="utf-8")

    def test_versioned_narrow_command_surface(self):
        self.assertIn("const CLI_VERSION = '1.1.0'", self.text)
        self.assertIn("['config', 'list', 'create', 'update', 'start', 'status']", self.text)
        self.assertIn("OPTION_NAMES", self.text)
        for forbidden in ("deletePipeline", "retryPipelineJobRun"):
            self.assertNotIn(forbidden, self.text)

    def test_no_retry_loop_or_raw_exception_output(self):
        self.assertNotRegex(self.text, r"\b(?:retry|retries|backoff|setTimeout|setInterval)\b")
        self.assertNotRegex(self.text, r"console\.(?:log|error)\([^)]*(?:error|err|response|body)")
        self.assertIn("reconcile read-only; do not repeat a write", self.text)
        for code in ("FLOW_API_FORBIDDEN", "FLOW_API_INVALID_YAML"):
            self.assertIn(code, self.text)

    def test_credentials_are_input_only_and_not_output(self):
        self.assertIn("ALIBABA_CLOUD_ACCESS_KEY_ID", self.text)
        self.assertIn("ALIBABA_CLOUD_ACCESS_KEY_SECRET", self.text)
        self.assertIn("credentials-file", self.text)
        stdout_blocks = re.findall(r"process\.stdout\.write\((.*?)\);", self.text, re.DOTALL)
        stderr_blocks = re.findall(r"process\.stderr\.write\((.*?)\);", self.text, re.DOTALL)
        emitted = "\n".join(stdout_blocks + stderr_blocks)
        for secret_name in ("accessKeyId", "accessKeySecret", "securityToken", "CREDENTIAL_KEYS"):
            self.assertNotIn(secret_name, emitted)
        self.assertNotIn("String(error", self.text)
        self.assertNotIn("JSON.stringify(error", self.text)

    def test_candidate_hash_and_single_write_readback_gates(self):
        self.assertIn("candidate-sha256", self.text)
        self.assertIn("CANDIDATE_SHA256_MISMATCH", self.text)
        self.assertIn("canonicalFlowText", self.text)
        self.assertIn("canonicalConfigSha256", self.text)
        self.assertEqual(1, self.text.count("client.createPipeline("))
        self.assertIn("write.body.pipelinId", self.text)
        self.assertEqual(1, self.text.count("client.updatePipeline("))
        update = re.search(r"async function commandUpdate.*?\n}\n\nasync function commandStart", self.text, re.DOTALL).group(0)
        self.assertLess(update.index("getPipeline(client, org, pipeline)"), update.index("client.updatePipeline("))
        self.assertGreater(update.rindex("getPipeline(client, org, pipeline)"), update.index("client.updatePipeline("))

    def test_frozen_start_context_and_pre_start_run_record(self):
        self.assertIn("context-sha256", self.text)
        self.assertIn("CONTEXT_SHA256_MISMATCH", self.text)
        self.assertIn("existingRunIds", self.text)
        self.assertIn("requestStartedAt", self.text)
        self.assertIn("START_CONTEXT_STALE", self.text)
        self.assertEqual(1, self.text.count("client.startPipelineRun("))
        start = re.search(r"async function commandStart.*?\n}\n\nasync function main", self.text, re.DOTALL).group(0)
        self.assertLess(start.index("const requestStartedAt = now();"), start.index("client.startPipelineRun("))

    def test_org_pipeline_and_allowlist_guards(self):
        self.assertIn("options.org", self.text)
        self.assertIn("options.pipeline", self.text)
        self.assertIn("options.allowlist", self.text)
        self.assertIn("ORG_NOT_ALLOWLISTED", self.text)
        self.assertIn("PIPELINE_NOT_ALLOWLISTED", self.text)
        self.assertIn("WRITE_ALLOWLIST_REQUIRED", self.text)
        self.assertIn("CREATE_NOT_ALLOWLISTED", self.text)

    def test_python_test_syntax(self):
        ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
