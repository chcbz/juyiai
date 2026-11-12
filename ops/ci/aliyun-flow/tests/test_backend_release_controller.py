import hashlib
import importlib.util
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "backend_release_controller", ROOT / "ops/ci/aliyun-flow/backend_release_controller.py"
)
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class BackendReleaseControllerTest(unittest.TestCase):
    commit = "a" * 40
    tree = "b" * 40

    def test_remote_lookup_and_local_validation_are_read_only_git_commands(self):
        calls = []

        def runner(command, **_kwargs):
            calls.append(command)
            if command[:3] == ["git", "ls-remote", "--refs"]:
                return subprocess.CompletedProcess(command, 0, self.commit + "\trefs/heads/develop\n", "")
            if "rev-parse" in command:
                return subprocess.CompletedProcess(command, 0, self.tree + "\n", "")
            if "remote" in command:
                return subprocess.CompletedProcess(command, 0, controller.REPOSITORY_URL + "\n", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        self.assertEqual(self.commit, controller.read_remote_develop_sha(runner=runner))
        value = controller.validate_local_api_source("/tmp", self.commit, runner=runner)
        self.assertEqual(self.tree, value["tree_sha"])
        flattened = " ".join(" ".join(call) for call in calls)
        self.assertNotIn("fetch", flattened)
        self.assertNotIn("reset", flattened)
        self.assertNotIn("checkout", flattened)

    def test_render_only_replaces_ticket_literals_and_exposes_readback_hashes(self):
        template = b"""name: cyf-api-kit-ci
branch: develop
branchesFilter: develop
triggerEvents: []
PIPELINE = '5260799'
step: JavaBuild
TICKET_ZLIB_B64 = 'old'
TICKET_SHA256 = 'old'
"""
        ticket = b'{"immutable":"ticket"}\n'
        rendered, ticket_sha = controller.render_ticket_only_template(template, ticket)
        summary = controller.readback_summary(
            rendered,
            template_sha256=hashlib.sha256(template).hexdigest(),
            ticket_sha256=ticket_sha,
        )
        self.assertEqual(hashlib.sha256(ticket).hexdigest(), ticket_sha)
        self.assertEqual(hashlib.sha256(rendered).hexdigest(), summary["candidate_config_sha256"])
        self.assertTrue(summary["source_develop"])
        self.assertTrue(summary["trigger_events_empty"])
        self.assertTrue(summary["deploy_step_absent"])
        self.assertTrue(summary["ticket_literals_present"])
        self.assertNotIn(ticket.decode(), rendered.decode())

    def test_render_binds_deploy_invocation_to_same_ticket_sha(self):
        template = b"""name: cyf-api-kit-ci
branch: develop
branchesFilter: develop
triggerEvents: []
PIPELINE = '5260799'
step: JavaBuild
TICKET_ZLIB_B64 = 'old'
TICKET_SHA256 = 'old'
component: VMDeploy
run: /usr/local/sbin/cyf-api-flow-auto-approve-install "$PIPELINE_ID" "$BUILD_NUMBER" "$CI_COMMIT_SHA"
"""
        ticket = b'{"immutable":"next-ticket"}\n'
        rendered, ticket_sha = controller.render_ticket_only_template(template, ticket)
        text = rendered.decode()
        self.assertIn(
            'cyf-api-flow-auto-approve-install "$PIPELINE_ID" "$BUILD_NUMBER" "$CI_COMMIT_SHA" "{}"'.format(ticket_sha),
            text,
        )
        summary = controller.readback_summary(
            rendered,
            template_sha256=hashlib.sha256(template).hexdigest(),
            ticket_sha256=ticket_sha,
        )
        self.assertFalse(summary["deploy_step_absent"])
        self.assertTrue(summary["deploy_ticket_bound"])

    def test_issue_command_is_fixed_to_orchestrator_and_runs_once(self):
        command = controller.build_issue_command(
            task_id="FLOW-CI-01",
            ticket_path="/tmp/cyf-flow-tickets/FLOW-CI-01.json",
            api_git_repo="/tmp/api",
            commit_sha=self.commit,
            tree_sha=self.tree,
            selector="backend-cold-smoke-v1",
            remote_cwd="/flow/workspace/api",
            remote_tool_root="/flow/workspace/flow-tools",
            remote_run_base="/flow/workspace/flow-output",
            orchestrator="/tmp/cyf_orchestrator.py",
        )
        self.assertIn("flow-remote", command)
        self.assertIn("issue", command)
        self.assertNotIn("run", command)
        invocations = []

        def runner(actual, **_kwargs):
            invocations.append(actual)
            return subprocess.CompletedProcess(actual, 0, '{"ticket_sha256":"x"}\n', "")

        self.assertIn("ticket_sha256", controller.issue_ticket_once(command, runner))
        self.assertEqual([command], invocations)
        invalid = list(command)
        invalid[1] = "/tmp/not_orchestrator.py"
        with self.assertRaisesRegex(controller.ControllerError, "non-flow-remote"):
            controller.issue_ticket_once(invalid, runner)

    def test_rejects_unknown_origin_and_ambiguous_template(self):
        with self.assertRaisesRegex(controller.ControllerError, "origin"):
            controller._safe_repository_url("https://example.invalid/jia.git")
        with self.assertRaisesRegex(controller.ControllerError, "exactly one"):
            controller.render_ticket_only_template(
                b"branch: develop\nPIPELINE = '5260799'\nTICKET_ZLIB_B64 = 'a'\n", b"x"
            )
        with self.assertRaisesRegex(controller.ControllerError, "deploy template"):
            controller.render_ticket_only_template(
                b"branch: develop\nPIPELINE = '5260799'\nTICKET_ZLIB_B64 = 'a'\nTICKET_SHA256 = 'a'\ncomponent: VMDeploy\n",
                b"x",
            )


if __name__ == "__main__":
    unittest.main()
