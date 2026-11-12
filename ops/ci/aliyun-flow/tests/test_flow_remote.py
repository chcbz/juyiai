import contextlib
import base64
import hashlib
import zipfile
import datetime as dt
import importlib.util
import io
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import types
import unittest
from unittest import mock


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = REPO_ROOT / "ops/orchestration/flow_remote.py"
SPEC = importlib.util.spec_from_file_location("flow_remote_under_test", str(MODULE_PATH))
flow_remote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flow_remote)


def git(cwd, *args):
    return subprocess.check_output(["git", "-C", str(cwd)] + list(args)).decode().strip()


@contextlib.contextmanager
def no_lock(_path):
    yield


class FlowRemoteTest(unittest.TestCase):
    def setUp(self):
        for prefix in (flow_remote.TOOL_PREFIX, flow_remote.RUN_PREFIX, flow_remote.TICKET_PREFIX):
            prefix.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix="flow-remote-test-", dir="/tmp"))
        self.tool_root = pathlib.Path(tempfile.mkdtemp(prefix="test-tools-", dir="/tmp/cyf-flow-tools"))
        self.api_root = pathlib.Path(tempfile.mkdtemp(prefix="cyf-flow-source-", dir="/tmp"))
        self.run_base = pathlib.Path(tempfile.mkdtemp(prefix="test-runs-", dir="/tmp/cyf-flow-runs"))
        self.ticket_dir = pathlib.Path(tempfile.mkdtemp(prefix="test-tickets-", dir="/tmp/cyf-flow-tickets"))
        self.nonce_dir = self.temp / "nonces"
        self.repo_url = "https://example.invalid/jia.git"
        self.fake_opencv = b"fake-opencv-fixture-not-production-artifact"
        pins = mock.patch.multiple(flow_remote,
                                   OPENCV_JAR_SHA256=hashlib.sha256(self.fake_opencv).hexdigest(),
                                   OPENCV_JAR_SIZE=len(self.fake_opencv))
        pins.start()
        self.addCleanup(pins.stop)
        self._create_tool_repo()
        self._create_api_repo(exit_code=0)
        self.controller_gate = "targeted_verification"
        self.controller_owner = {
            "agent": "test-agent",
            "profile": "critical_worker",
            "mode": "writer",
        }

    def tearDown(self):
        for path in (self.temp, self.tool_root, self.api_root, self.run_base, self.ticket_dir):
            shutil.rmtree(str(path), ignore_errors=True)

    def _git_init(self, root):
        subprocess.check_call(["git", "init", "-q", str(root)])
        subprocess.check_call(["git", "-C", str(root), "config", "user.email", "test@example.invalid"])
        subprocess.check_call(["git", "-C", str(root), "config", "user.name", "Flow Test"])

    def _create_tool_repo(self):
        self._git_init(self.tool_root)
        for logical in flow_remote.TOOL_PATHS:
            source = REPO_ROOT / logical
            target = self.tool_root / logical
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(source), str(target))
            os.chmod(str(target), source.stat().st_mode & 0o777)
        subprocess.check_call(["git", "-C", str(self.tool_root), "add", "."])
        subprocess.check_call(["git", "-C", str(self.tool_root), "commit", "-qm", "tools"])
        self.controller_commit = git(self.tool_root, "rev-parse", "HEAD")
        self.controller_tree = git(self.tool_root, "rev-parse", "HEAD^{tree}")

    def _create_api_repo(self, exit_code):
        self._git_init(self.api_root)
        (self.api_root / "gradle/wrapper").mkdir(parents=True)
        gradlew = self.api_root / "gradlew"
        # Python shebang wrapper: not a Gradle runtime. It exercises the actual
        # subprocess/redaction/package path and writes a real (synthetic) ZIP.
        gradlew.write_text(
            "#!/usr/bin/env python3\n"
            "import sys; sys.dont_write_bytecode = True\n"
            "import os, pathlib, json, hashlib, zipfile, base64\n"
            "assert os.environ['CYF_MAVEN_USERNAME'] == 'synthetic-reader-4680'\n"
            "assert os.environ['CYF_MAVEN_PASSWORD'] == 'synthetic-password-5917'\n"
            "assert 'UNRELATED_SECRET' not in os.environ\n"
            "assert 'ALIBABA_CLOUD_ACCESS_KEY_SECRET' not in os.environ\n"
            "assert 'ORG_GRADLE_PROJECT_repoPassword' not in os.environ\n"
            "root = pathlib.Path(os.environ['CYF_FLOW_BUILD_ROOT'])\n"
            "libs = root / 'jia/starter/libs'\n"
            "libs.mkdir(parents=True)\n"
            "with zipfile.ZipFile(str(libs / 'starter.jar'), 'w', zipfile.ZIP_DEFLATED) as jar:\n"
            "    jar.writestr('app.class', b'jar-bytes')\n"
            "dependency = pathlib.Path(os.environ['GRADLE_USER_HOME']) / 'opencv-4.5.5.jar'\n"
            "dependency.write_bytes(" + repr(self.fake_opencv) + ")\n"
            "record = dict(coordinate='org.opencv:opencv:4.5.5', jar_sha256=hashlib.sha256(dependency.read_bytes()).hexdigest(), jar_size=dependency.stat().st_size, resolved_file=str(dependency))\n"
            "(root / 'opencv-resolved.json').write_text(json.dumps(record))\n"
            "tests = root / 'jia/common__jia-common-core/test-results/test'\n"
            "tests.mkdir(parents=True)\n"
            "(tests / 'TEST-SensitiveDataSanitizerTest.xml').write_text('<testsuite name=\"SensitiveDataSanitizerTest\" tests=\"8\" failures=\"0\" errors=\"0\" skipped=\"0\"><system-out>' + os.environ['CYF_MAVEN_PASSWORD'] + '</system-out></testsuite>')\n"
            "print(os.environ['CYF_MAVEN_PASSWORD'])\n"
            "print('Basic ' + base64.b64encode((os.environ['CYF_MAVEN_USERNAME'] + ':' + os.environ['CYF_MAVEN_PASSWORD']).encode()).decode(), file=sys.stderr)\n"
            "sys.exit({})\n".format(exit_code),
            encoding="utf-8",
        )
        os.chmod(str(gradlew), 0o755)
        (self.api_root / "gradle/wrapper/gradle-wrapper.properties").write_text(
            "distributionUrl=https\\://mirrors.cloud.tencent.com/gradle/gradle-9.3.1-bin.zip\n",
            encoding="utf-8",
        )
        (self.api_root / "settings.gradle").write_text("rootProject.name='jia'\n", encoding="utf-8")
        (self.api_root / "build.gradle").write_text("tasks.register('validateLayering')\n", encoding="utf-8")
        subprocess.check_call(["git", "-C", str(self.api_root), "add", "."])
        subprocess.check_call(["git", "-C", str(self.api_root), "commit", "-qm", "api"])
        subprocess.check_call(["git", "-C", str(self.api_root), "branch", "-M", "develop"])
        subprocess.check_call(["git", "-C", str(self.api_root), "remote", "add", "origin", self.repo_url])
        subprocess.check_call([
            "git", "-C", str(self.api_root), "update-ref",
            "refs/remotes/origin/develop", "HEAD",
        ])
        self.api_commit = git(self.api_root, "rev-parse", "HEAD")
        self.api_tree = git(self.api_root, "rev-parse", "HEAD^{tree}")
        self.ledger_source_commit = self.api_commit
        self.ledger_source_tree = self.api_tree

    def _controller(self):
        task_item = {
            "owner": self.controller_owner,
            "exact_sha_tree": {
                "commit_sha": self.ledger_source_commit,
                "tree_sha": self.ledger_source_tree,
            },
            "current_gate": self.controller_gate,
            "blocker": None,
            "next_action": "test",
        }
        ledger = {"tasks": {"FLOW-CI-01": task_item}}
        return {
            "root": self.tool_root,
            "control_lock": self.temp / "control.lock",
            "exclusive_lock": no_lock,
            "load_ledger": lambda: ledger,
            "task": lambda loaded, task_id: loaded["tasks"][task_id],
            "gradle_gates": {"targeted_verification", "verifying"},
        }

    def _issue_args(self, name="ticket.json"):
        return types.SimpleNamespace(
            task_id="FLOW-CI-01",
            ticket=str(self.ticket_dir / name),
            api_git_repo=str(self.api_root),
            repo_url=self.repo_url,
            branch="develop",
            commit_sha=self.api_commit,
            tree_sha=self.api_tree,
            selector="backend-cold-smoke-v1",
            test_filter=flow_remote.DEFAULT_TEST_FILTER,
            flow_organization="org-test",
            flow_pipeline="pipeline-test",
            remote_cwd=str(self.api_root),
            remote_tool_root=str(self.tool_root),
            remote_run_base=str(self.run_base),
            ttl_seconds=3600,
        )

    def _issue(self, name="ticket.json"):
        args = self._issue_args(name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, flow_remote.issue_ticket(args, self._controller()))
        path = pathlib.Path(args.ticket)
        ticket = json.loads(path.read_text(encoding="utf-8"))
        return path, ticket, flow_remote.sha256_file(path)

    def _flow_env(self):
        return mock.patch.dict(os.environ, {
            "CYF_MAVEN_USERNAME": "synthetic-reader-4680",
            "CYF_MAVEN_PASSWORD": "synthetic-password-5917",
            "UNRELATED_SECRET": "never-copy-this-sentinel",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "never-copy-ak-sentinel",
            "ORG_GRADLE_PROJECT_repoPassword": "never-copy-publish-sentinel",
            "CYF_FLOW_ORGANIZATION_ID": "org-test",
            "CYF_FLOW_PIPELINE_ID": "pipeline-test",
            "CYF_FLOW_RUN_ID": "run-123",
            "CYF_FLOW_JOB_ID": "job-456",
            "CYF_FLOW_SOURCE_TIP_SHA": "97ae8ef12c0a0306a40a04017f44139e1ca27823",
        }, clear=False)

    def test_issue_requires_gate_and_writes_immutable_ticket(self):
        self.controller_gate = "implementing"
        with self.assertRaisesRegex(flow_remote.RemoteError, "verification gate"):
            flow_remote.issue_ticket(self._issue_args(), self._controller())

        self.controller_gate = "targeted_verification"
        (self.tool_root / "unrelated-controller-change.txt").write_text("dirty", encoding="utf-8")
        ticket_path, ticket, ticket_hash = self._issue()
        self.assertEqual("develop", ticket["source"]["branch"])
        self.assertEqual(self.api_tree, ticket["fixture"]["inputs"]["source_tree_sha"])
        self.assertEqual(self.api_commit, ticket["task"]["ledger_source_commit_sha"])
        self.assertEqual(self.api_tree, ticket["task"]["ledger_source_tree_sha"])
        self.assertNotIn("next_action", ticket_path.read_text(encoding="utf-8"))
        self.assertNotIn("blocker", ticket_path.read_text(encoding="utf-8"))
        self.assertEqual(0, ticket_path.stat().st_mode & 0o222)
        self.assertRegex(ticket_hash, r"^[0-9a-f]{64}$")
        with self.assertRaisesRegex(flow_remote.RemoteError, "overwrite immutable"):
            flow_remote.issue_ticket(self._issue_args(), self._controller())

    def test_issue_rejects_ledger_source_mismatch(self):
        self.ledger_source_tree = "0" * 40
        with self.assertRaisesRegex(flow_remote.RemoteError, "ledger exact tree"):
            flow_remote.issue_ticket(self._issue_args(), self._controller())

    def test_tool_tamper_is_rejected_by_remote_verification(self):
        _ticket_path, ticket, _ticket_hash = self._issue("tool-ticket.json")
        target = self.tool_root / "ops/ci/aliyun-flow/run-cloud.sh"
        target.write_text(target.read_text(encoding="utf-8") + "# tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(flow_remote.RemoteError, "tool bytes"):
            flow_remote.verify_tools(ticket, self.tool_root)

    def test_python_blob_scanner_detects_nested_gradle(self):
        flow_remote.verify_nested_gradle_absent(self.api_root)
        build_file = self.api_root / "build.gradle"
        build_file.write_text(
            "tasks.register('nested', Exec) { commandLine './gradlew', 'help' }\n",
            encoding="utf-8",
        )
        subprocess.check_call(["git", "-C", str(self.api_root), "add", "build.gradle"])
        subprocess.check_call(["git", "-C", str(self.api_root), "commit", "-qm", "nested"])
        with self.assertRaisesRegex(flow_remote.RemoteError, "immutable build source"):
            flow_remote.verify_nested_gradle_absent(self.api_root)

    def test_python_blob_scanner_skips_only_ticket_verified_init_script(self):
        trusted = self.api_root / "ops/ci/aliyun-flow/cold-init.gradle"
        trusted.parent.mkdir(parents=True)
        nested = "tasks.register('nested', Exec) { commandLine './gradlew', 'help' }\n"
        trusted.write_text(nested, encoding="utf-8")
        subprocess.check_call(["git", "-C", str(self.api_root), "add", "ops/ci/aliyun-flow/cold-init.gradle"])
        subprocess.check_call(["git", "-C", str(self.api_root), "commit", "-qm", "trusted-init"])
        with self.assertRaisesRegex(flow_remote.RemoteError, "immutable build source"):
            flow_remote.verify_nested_gradle_absent(self.api_root)
        flow_remote.verify_nested_gradle_absent(
            self.api_root, flow_remote.TRUSTED_SOURCE_SCAN_EXCLUSIONS
        )
        other = self.api_root / "ops/ci/aliyun-flow/other.gradle"
        other.write_text(nested, encoding="utf-8")
        subprocess.check_call(["git", "-C", str(self.api_root), "add", "ops/ci/aliyun-flow/other.gradle"])
        subprocess.check_call(["git", "-C", str(self.api_root), "commit", "-qm", "untrusted-init"])
        with self.assertRaisesRegex(flow_remote.RemoteError, "ops/ci/aliyun-flow/other.gradle"):
            flow_remote.verify_nested_gradle_absent(
                self.api_root, flow_remote.TRUSTED_SOURCE_SCAN_EXCLUSIONS
            )
        with self.assertRaisesRegex(flow_remote.RemoteError, "unexpected Gradle source scanner exclusion"):
            flow_remote.verify_nested_gradle_absent(self.api_root, {"build.gradle"})

    def test_hash_tamper_expiry_unknown_field_and_dangerous_argv_rejected(self):
        ticket_path, ticket, ticket_hash = self._issue()
        raw = ticket_path.read_bytes()
        tampered_path = self.ticket_dir / "tampered.json"
        tampered_path.write_bytes(raw + b" ")
        with self.assertRaisesRegex(flow_remote.RemoteError, "SHA-256 mismatch"):
            flow_remote.load_verified_ticket(tampered_path, ticket_hash)

        expired = dict(ticket)
        expired["issued_at"] = "2026-09-09T00:00:00Z"
        expired["expires_at"] = "2026-09-09T00:01:00Z"
        with self.assertRaisesRegex(flow_remote.RemoteError, "expired"):
            flow_remote.validate_ticket(
                expired,
                now_value=dt.datetime(2026, 9, 9, 0, 2, tzinfo=dt.timezone.utc),
            )

        unknown = dict(ticket)
        unknown["signature"] = "not-trusted"
        with self.assertRaisesRegex(flow_remote.RemoteError, "fields must be exactly"):
            flow_remote.validate_ticket(unknown, check_time=False)

        dangerous = json.loads(json.dumps(ticket))
        dangerous["gradle"]["argv"].extend(["-x", "test"])
        dangerous["fixture"]["inputs"]["argv"] = dangerous["gradle"]["argv"]
        dangerous["fixture"]["digest"] = flow_remote.sha256_bytes(
            flow_remote.canonical_bytes(dangerous["fixture"]["inputs"])
        )
        with self.assertRaisesRegex(flow_remote.RemoteError, "frozen command"):
            flow_remote.validate_ticket(dangerous, check_time=False)

    def test_dirty_source_is_rejected(self):
        _ticket_path, ticket, _ticket_hash = self._issue()
        dirty = self.api_root / "untracked.txt"
        dirty.write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(flow_remote.RemoteError, "dirty"):
            flow_remote.verify_source(ticket, self.api_root)

    def test_native_nonzero_exit_is_returned_and_nonce_replay_is_denied(self):
        shutil.rmtree(str(self.api_root))
        self.api_root = pathlib.Path(tempfile.mkdtemp(prefix="cyf-flow-source-", dir="/tmp"))
        self._create_api_repo(exit_code=7)
        ticket_path, ticket, ticket_hash = self._issue("failure-ticket.json")
        args = types.SimpleNamespace(
            ticket=str(ticket_path),
            expected_ticket_sha256=ticket_hash,
            cwd=str(self.api_root),
            receipt=ticket["execution"]["receipt_path"],
        )
        with self._flow_env(), mock.patch.object(flow_remote, "java_identity", return_value='openjdk version "21"'):
            self.assertEqual(7, flow_remote.execute_run(args, self.tool_root, nonce_dir=self.nonce_dir))
        receipt = json.loads(pathlib.Path(args.receipt).read_text(encoding="utf-8"))
        self.assertEqual(7, receipt["gradle_exit_code"])
        self.assertEqual(7, receipt["bridge_exit_code"])
        self.assertEqual("gradle_failed", receipt["status"])
        with self._flow_env(), mock.patch.object(flow_remote, "java_identity", return_value='openjdk version "21"'):
            with self.assertRaisesRegex(flow_remote.RemoteError, "nonce"):
                flow_remote.execute_run(args, self.tool_root, nonce_dir=self.nonce_dir)

    def test_success_packages_unique_jar_and_inspect_never_auto_accepts(self):
        ticket_path, ticket, ticket_hash = self._issue("success-ticket.json")
        args = types.SimpleNamespace(
            ticket=str(ticket_path),
            expected_ticket_sha256=ticket_hash,
            cwd=str(self.api_root),
            receipt=ticket["execution"]["receipt_path"],
        )
        with self._flow_env(), mock.patch.object(flow_remote, "java_identity", return_value='openjdk version "21"'):
            self.assertEqual(0, flow_remote.execute_run(args, self.tool_root, nonce_dir=self.nonce_dir))
        receipt_path = pathlib.Path(args.receipt)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual("success", receipt["status"])
        run_root = receipt_path.parent
        for name in ("home", "gradle-user-home", "build", "tmp", "project-cache"):
            self.assertFalse((run_root / name).exists(), name)
        for path in list(run_root.rglob("*")) + [ticket_path]:
            if path.is_file():
                data = path.read_bytes()
                for value in (b"synthetic-reader-4680", b"synthetic-password-5917",
                              base64.b64encode(b"synthetic-reader-4680:synthetic-password-5917")):
                    self.assertNotIn(value, data, str(path))
        self.assertEqual(1, len([item for item in receipt["files"] if item["kind"] == "dependency_provenance"]))
        self.assertEqual(1, len([item for item in receipt["files"] if item["kind"] == "test_xml"]))
        self.assertEqual("97ae8ef12c0a0306a40a04017f44139e1ca27823", receipt["flow"]["source_tip_sha"])
        self.assertNotEqual(receipt["flow"]["source_tip_sha"], receipt["source"]["commit_sha"])
        self.assertEqual(8, receipt["tests"]["tests"])
        self.assertEqual(1, len([item for item in receipt["files"] if item["kind"] == "application_jar"]))
        self.assertEqual("", git(self.api_root, "status", "--porcelain", "--untracked-files=all"))

        inspect_args = types.SimpleNamespace(
            ticket=str(ticket_path),
            expected_ticket_sha256=ticket_hash,
            receipt=str(receipt_path),
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(0, flow_remote.inspect_receipt(inspect_args))
        packet = json.loads(output.getvalue())
        self.assertTrue(packet["candidate_for_controller_evidence_put"])
        self.assertFalse(packet["automatically_accepted"])
        self.assertTrue(packet["authenticated_flow_review_required"])

    def test_missing_partial_auth_denied_before_gradle_or_nonce(self):
        ticket_path, ticket, ticket_hash = self._issue()
        args = types.SimpleNamespace(ticket=str(ticket_path), expected_ticket_sha256=ticket_hash,
                                     cwd=str(self.api_root), receipt=ticket["execution"]["receipt_path"])
        for pair in ({}, {"CYF_MAVEN_USERNAME": "synthetic-reader-4680"},
                     {"CYF_MAVEN_PASSWORD": "synthetic-password-5917"}):
            with mock.patch.dict(os.environ, pair, clear=True), mock.patch.object(flow_remote, "run_tee") as run:
                with self.assertRaisesRegex(flow_remote.RemoteError, "both CYF_MAVEN"):
                    flow_remote.execute_run(args, self.tool_root, nonce_dir=self.nonce_dir)
                run.assert_not_called()
                self.assertFalse(self.nonce_dir.exists())

    def test_resolved_jar_drift_and_missing_provenance_fail_closed(self):
        root = self.temp / "provenance-run"
        build = root / "build"
        build.mkdir(parents=True)
        (root / "gradle-user-home").mkdir()
        with self.assertRaisesRegex(flow_remote.RemoteError, "missing"):
            flow_remote.collect_opencv_provenance(root, build)
        jar = root / "gradle-user-home/opencv.jar"
        jar.write_bytes(self.fake_opencv + b"drift")
        record = dict(coordinate=flow_remote.OPENCV_COORDINATE,
                      jar_sha256=flow_remote.OPENCV_JAR_SHA256,
                      jar_size=flow_remote.OPENCV_JAR_SIZE, resolved_file=str(jar))
        (build / "opencv-resolved.json").write_text(json.dumps(record))
        with self.assertRaisesRegex(flow_remote.RemoteError, "controller pin"):
            flow_remote.collect_opencv_provenance(root, build)
        self.assertFalse((root / "dependency-provenance.json").exists())
        jar.write_bytes(self.fake_opencv)
        record = flow_remote.collect_opencv_provenance(root, build)
        self.assertEqual("dependency_provenance", record["kind"])

    def test_redaction_and_failed_xml_processing_preserve_native_exit(self):
        shutil.rmtree(str(self.api_root))
        self.api_root = pathlib.Path(tempfile.mkdtemp(prefix="cyf-flow-source-", dir="/tmp"))
        self._create_api_repo(exit_code=9)
        path, ticket, digest = self._issue()
        args = types.SimpleNamespace(ticket=str(path), expected_ticket_sha256=digest,
                                     cwd=str(self.api_root), receipt=ticket["execution"]["receipt_path"])
        with self._flow_env(), mock.patch.object(flow_remote, "java_identity", return_value='openjdk version "21"'), \
                mock.patch.object(flow_remote, "export_test_xml", side_effect=flow_remote.RemoteError("synthetic-password-5917")):
            self.assertEqual(9, flow_remote.execute_run(args, self.tool_root, nonce_dir=self.nonce_dir))
        receipt = pathlib.Path(args.receipt).read_text()
        self.assertNotIn("synthetic-password-5917", receipt)
        self.assertEqual(9, json.loads(receipt)["gradle_exit_code"])


class SecretBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.credentials = {"CYF_MAVEN_USERNAME": "reader<&-4680", "CYF_MAVEN_PASSWORD": "password+5917&<>"}
        self.patterns = flow_remote.secret_patterns(self.credentials)

    def test_every_chunk_split_raw_escaped_and_basic_is_redacted_before_both_sinks(self):
        raw = b"prefix " + b" | ".join(self.patterns) + b" suffix"
        expected = flow_remote.redact_bytes(raw, self.patterns)
        for split in range(len(raw) + 1):
            redactor = flow_remote.StreamRedactor(self.patterns)
            actual = redactor.feed(raw[:split]) + redactor.feed(raw[split:]) + redactor.feed(b"", final=True)
            self.assertEqual(expected, actual, split)
        redactor = flow_remote.StreamRedactor(self.patterns)
        self.assertEqual(expected, b"".join(redactor.feed(bytes([char])) for char in raw) + redactor.feed(b"", final=True))
        for pattern in self.patterns:
            self.assertNotIn(pattern, expected)

        class Chunks(object):
            def __init__(self):
                self.parts = iter([raw[:13], raw[13:22], raw[22:], b""])
            def read(self, _size):
                return next(self.parts)
            def close(self):
                pass
        disk, console = io.BytesIO(), io.BytesIO()
        errors = []
        flow_remote.pump_stream(Chunks(), disk, types.SimpleNamespace(buffer=console), self.patterns, errors)
        self.assertEqual([], errors)
        self.assertEqual(expected, disk.getvalue())
        self.assertEqual(expected, console.getvalue())

    def test_fake_zip_declared_size_limit_diagnostic_is_numeric_and_redacted(self):
        secret_member = "member-{}-path.jar".format(self.credentials["CYF_MAVEN_PASSWORD"])
        entries = [
            types.SimpleNamespace(filename="safe.bin", file_size=1024 * 1024 * 1024, comment=b"", extra=b""),
            types.SimpleNamespace(filename=secret_member, file_size=1, comment=b"", extra=b""),
        ]
        self._assert_fake_zip_limit_diagnostic(
            entries, "declared_size", 1024 * 1024 * 1024,
            1024 * 1024 * 1024, 1024 * 1024 * 1024 + 1, 1, 0, 2,
            secret_member,
        )

    def test_fake_zip_entry_count_limit_diagnostic_is_numeric_and_redacted(self):
        secret_member = "member-{}-path.jar".format(self.credentials["CYF_MAVEN_PASSWORD"])
        entries = [
            types.SimpleNamespace(filename="safe.bin", file_size=0, comment=b"", extra=b"")
            for _ in range(150000)
        ]
        entries.append(types.SimpleNamespace(filename=secret_member, file_size=7, comment=b"", extra=b""))
        self._assert_fake_zip_limit_diagnostic(
            entries, "entry_count", 150000, 150000, 150001, 7, 0, 150001,
            secret_member,
        )

    def _assert_fake_zip_limit_diagnostic(self, entries, dimension, configured_limit,
                                          prior_total, attempted_total,
                                          current_declared_size, depth, ordinal,
                                          secret_member):
        class FakeZipFile(object):
            comment = b""

            def __init__(self, _handle):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def infolist(self):
                return entries

            def open(self, _entry):
                return io.BytesIO(b"")

        with tempfile.TemporaryDirectory(prefix="flow-fake-archive-test-") as directory:
            archive = pathlib.Path(directory) / "archive.jar"
            archive.write_bytes(b"not-a-real-zip")
            with mock.patch.object(flow_remote.zipfile, "is_zipfile", return_value=True), \
                    mock.patch.object(flow_remote.zipfile, "ZipFile", FakeZipFile):
                with self.assertRaises(flow_remote.RemoteError) as caught:
                    flow_remote.verify_export_jar(archive, self.patterns)

        self.assertEqual(
            "artifact archive inspection limit exceeded: {} "
            "configured_limit={} prior_total={} attempted_total={} "
            "current_declared_size={} depth={} ordinal={}".format(
                dimension, configured_limit, prior_total, attempted_total,
                current_declared_size, depth, ordinal,
            ),
            str(caught.exception),
        )
        self.assertNotIn(secret_member, str(caught.exception))
        self.assertNotIn(self.credentials["CYF_MAVEN_PASSWORD"], str(caught.exception))

    def test_compressed_nested_jar_secret_is_rejected_not_rewritten(self):
        with tempfile.TemporaryDirectory(prefix="flow-archive-test-") as directory:
            outer = pathlib.Path(directory) / "boot.jar"
            nested = io.BytesIO()
            with zipfile.ZipFile(nested, "w", zipfile.ZIP_DEFLATED) as jar:
                jar.writestr("leak.txt", self.credentials["CYF_MAVEN_PASSWORD"])
            with zipfile.ZipFile(str(outer), "w", zipfile.ZIP_DEFLATED) as jar:
                jar.writestr("BOOT-INF/lib/dependency.jar", nested.getvalue())
            before = outer.read_bytes()
            with self.assertRaisesRegex(flow_remote.RemoteError, "credential material"):
                flow_remote.verify_export_jar(outer, self.patterns)
            self.assertEqual(before, outer.read_bytes())
            with zipfile.ZipFile(str(outer), "w", zipfile.ZIP_DEFLATED) as jar:
                jar.writestr("safe.txt", "no credentials")
            flow_remote.verify_export_jar(outer, self.patterns)


if __name__ == "__main__":
    unittest.main()
