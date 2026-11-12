import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import mock

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "cyf_orchestrator.py"
SPEC = importlib.util.spec_from_file_location("cyf_orchestrator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.originals = {
            "LEDGER_PATH": MODULE.LEDGER_PATH,
            "EVIDENCE_PATH": MODULE.EVIDENCE_PATH,
            "CONTROL_LOCK": MODULE.CONTROL_LOCK,
            "EVIDENCE_LOCK": MODULE.EVIDENCE_LOCK,
            "GRADLE_LOCK": MODULE.GRADLE_LOCK,
            "NOTIFICATION_LOCK": MODULE.NOTIFICATION_LOCK,
            "NOTIFICATION_OUTBOX": MODULE.NOTIFICATION_OUTBOX,
        }

    def tearDown(self):
        for name, value in self.originals.items():
            setattr(MODULE, name, value)

    def valid_ledger(self):
        return {
            "schema_version": 2,
            "updated_at": "2026-08-25T00:00:00+08:00",
            "critical_path": ["A", "B"],
            "tasks": {
                "A": {
                    "owner": {"agent": "x", "profile": "critical_worker", "mode": "writer"},
                    "exact_sha_tree": {"commit_sha": "a" * 40, "tree_sha": "b" * 40},
                    "current_gate": "implementing",
                    "blocker": None,
                    "next_action": "finish A",
                },
                "B": {
                    "owner": None,
                    "exact_sha_tree": {"commit_sha": None, "tree_sha": None},
                    "current_gate": "blocked_dependency",
                    "blocker": {
                        "category": "dependency",
                        "summary": "A",
                        "consecutive_failures": 0,
                        "attempts": [],
                    },
                    "next_action": "wait A",
                },
            },
        }

    def install_temp_control_plane(self, directory, ledger=None):
        root = pathlib.Path(directory)
        ledger_path = root / "TASKS.yaml"
        evidence_path = root / "EVIDENCE_CACHE.json"
        payload = ledger or self.valid_ledger()
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        ledger_path.write_text(
            "schema_version: 1\n"
            + MODULE.LEDGER_BEGIN
            + "runtime_ledger_json: |\n"
            + "".join("  " + line + "\n" for line in body.splitlines())
            + MODULE.LEDGER_END
            + "tasks: []\n",
            encoding="utf-8",
        )
        evidence_path.write_text('{"schema_version":1,"updated_at":"x","records":{}}\n', encoding="utf-8")
        MODULE.LEDGER_PATH = ledger_path
        MODULE.EVIDENCE_PATH = evidence_path
        MODULE.CONTROL_LOCK = root / "control.lock"
        MODULE.EVIDENCE_LOCK = root / "evidence.lock"
        MODULE.GRADLE_LOCK = root / "gradle.lock"
        MODULE.NOTIFICATION_LOCK = root / "notify.lock"
        MODULE.NOTIFICATION_OUTBOX = root / "notifications.jsonl"
        return ledger_path, evidence_path

    def test_validates_exact_five_task_fields(self):
        self.assertEqual([], MODULE.validate_ledger(self.valid_ledger()))
        ledger = self.valid_ledger()
        ledger["tasks"]["A"]["extra"] = True
        self.assertTrue(any("fields must be exactly" in error for error in MODULE.validate_ledger(ledger)))

    def test_rejects_legacy_exact_and_gate_field_names(self):
        ledger = self.valid_ledger()
        item = ledger["tasks"]["A"]
        item["exact"] = item.pop("exact_sha_tree")
        item["gate"] = item.pop("current_gate")
        errors = MODULE.validate_ledger(ledger)
        self.assertTrue(any("exact_sha_tree" in error or "fields must be exactly" in error for error in errors))

    def test_allows_two_task_scoped_active_writers(self):
        ledger = self.valid_ledger()
        ledger["tasks"]["B"]["owner"] = {"agent": "y", "profile": "critical_worker", "mode": "writer"}
        ledger["tasks"]["B"]["current_gate"] = "remediating"
        self.assertEqual([], MODULE.validate_ledger(ledger))

    def test_rejects_preemption_blocker_categories(self):
        for category in sorted(MODULE.FORBIDDEN_BLOCKER_CATEGORIES):
            with self.subTest(category=category):
                ledger = self.valid_ledger()
                ledger["tasks"]["B"]["blocker"]["category"] = category
                errors = MODULE.validate_ledger(ledger)
                self.assertTrue(any(category in error and "forbidden" in error for error in errors))

        ledger = self.valid_ledger()
        ledger["tasks"]["B"]["blocker"]["attempts"] = [{"category": "process_preemption"}]
        errors = MODULE.validate_ledger(ledger)
        self.assertTrue(any("attempts[0]" in error and "process_preemption" in error for error in errors))

    def test_evidence_key_is_exact_and_stable(self):
        key = MODULE.evidence_key("a" * 40, "Test#case", "f" * 64)
        self.assertEqual(key, MODULE.evidence_key("a" * 40, "Test#case", "f" * 64))
        self.assertNotEqual(key, MODULE.evidence_key("b" * 40, "Test#case", "f" * 64))
        self.assertNotEqual(key, MODULE.evidence_key("a" * 40, "Test#other", "f" * 64))
        self.assertNotEqual(key, MODULE.evidence_key("a" * 40, "Test#case", "e" * 64))

    def test_atomic_write_round_trip_and_preserves_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "ledger.json"
            path.write_text("{}\n", encoding="utf-8")
            os.chmod(str(path), 0o755)
            MODULE.atomic_write(path, self.valid_ledger())
            self.assertEqual(self.valid_ledger(), json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(0o755, path.stat().st_mode & 0o777)

    def test_two_failures_stop_emit_matrix_and_block_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path, _ = self.install_temp_control_plane(directory)
            args = Namespace(
                task_id="A",
                category="test",
                summary="failed",
                evidence="log",
                root_cause="cause",
                remediation="fix",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(1, MODULE.cmd_fail(args))
                self.assertEqual(2, MODULE.cmd_fail(args))
            ledger = MODULE.load_ledger()
            self.assertEqual("blocked_root_cause", ledger["tasks"]["A"]["current_gate"])
            self.assertEqual(2, ledger["tasks"]["A"]["blocker"]["consecutive_failures"])
            claim = Namespace(
                task_id="A",
                agent="writer",
                profile="critical_worker",
                commit_sha="a" * 40,
                tree_sha="b" * 40,
                next_action="blind third try",
            )
            with self.assertRaises(SystemExit):
                MODULE.cmd_claim(claim)
            self.assertIn('"event": "root_cause_matrix_required"', MODULE.NOTIFICATION_OUTBOX.read_text(encoding="utf-8"))
            self.assertIn('"current_gate": "blocked_root_cause"', ledger_path.read_text(encoding="utf-8"))

    def test_authorized_remediation_is_explicit_and_resets_consecutive_counter(self):
        with tempfile.TemporaryDirectory() as directory:
            self.install_temp_control_plane(directory)
            fail = Namespace(
                task_id="A",
                category="test",
                summary="failed",
                evidence="log",
                root_cause="cause",
                remediation="fix",
            )
            with redirect_stdout(StringIO()):
                MODULE.cmd_fail(fail)
                MODULE.cmd_fail(fail)
                result = MODULE.cmd_authorize_remediation(
                    Namespace(
                        task_id="A",
                        agent="writer-r7",
                        profile="critical_worker",
                        commit_sha="c" * 40,
                        tree_sha="d" * 40,
                        matrix_ref="handoffs/A.md#matrix",
                        next_action="bounded remediation",
                    )
                )
            self.assertEqual(0, result)
            item = MODULE.load_ledger()["tasks"]["A"]
            self.assertEqual("remediating", item["current_gate"])
            self.assertEqual(0, item["blocker"]["consecutive_failures"])
            self.assertEqual(2, len(item["blocker"]["attempts"]))
            self.assertIn("matrix", item["blocker"]["summary"])

    def test_evidence_hit_skips_gradle_after_exact_worktree_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.valid_ledger()
            ledger["tasks"]["A"]["owner"] = {"agent": "v", "profile": "gpt_test_runner", "mode": "verifier"}
            ledger["tasks"]["A"]["current_gate"] = "verifying"
            _, evidence_path = self.install_temp_control_plane(directory, ledger)
            key = MODULE.evidence_key("b" * 40, "selector", "N/A")
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "updated_at": "x",
                        "records": {
                            key: {
                                "tree_sha": "b" * 40,
                                "selector": "selector",
                                "fixture_digest": "N/A",
                                "result": "accepted",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            args = Namespace(
                task_id="A",
                heavy=False,
                cwd=pathlib.Path(directory),
                tree_sha="b" * 40,
                selector="selector",
                fixture_digest="N/A",
                artifact=None,
                command=["./gradlew", "must-not-run"],
            )
            with mock.patch.object(MODULE, "verify_exact_worktree", return_value=pathlib.Path(directory)):
                with mock.patch.object(MODULE, "record_gradle_resource_telemetry") as telemetry:
                    with redirect_stdout(StringIO()) as output:
                        self.assertEqual(0, MODULE.cmd_gradle(args))
            telemetry.assert_called_once_with(False)
            self.assertIn("EVIDENCE_HIT", output.getvalue())

    def test_gradle_child_identity_drops_groups_gid_then_uid(self):
        args = Namespace(run_uid=61006, run_gid=61006)
        with mock.patch.object(MODULE.os, "geteuid", return_value=0), \
             mock.patch.object(MODULE.os, "setgroups") as setgroups, \
             mock.patch.object(MODULE.os, "setgid") as setgid, \
             mock.patch.object(MODULE.os, "setuid") as setuid:
            preexec = MODULE.gradle_child_identity(args)
            self.assertIsNotNone(preexec)
            preexec()
        setgroups.assert_called_once_with([])
        setgid.assert_called_once_with(61006)
        setuid.assert_called_once_with(61006)

    def test_gradle_child_identity_is_fail_closed(self):
        with self.assertRaises(SystemExit):
            MODULE.gradle_child_identity(Namespace(run_uid=61006, run_gid=None))
        with self.assertRaises(SystemExit):
            MODULE.gradle_child_identity(Namespace(run_uid=0, run_gid=0))
        with mock.patch.object(MODULE.os, "geteuid", return_value=61006):
            with self.assertRaises(SystemExit):
                MODULE.gradle_child_identity(Namespace(run_uid=61006, run_gid=61006))

    def test_every_gradle_invocation_records_all_resource_metrics_without_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            meminfo = pathlib.Path(directory) / "meminfo"
            meminfo.write_text(
                "MemTotal: 999 kB\nMemAvailable: 123 kB\nSwapFree: 456 kB\n",
                encoding="utf-8",
            )
            with mock.patch.object(MODULE, "PROC_MEMINFO", meminfo), mock.patch.object(
                MODULE.shutil, "disk_usage", return_value=mock.Mock(free=789)
            ), mock.patch.object(MODULE.os, "statvfs", return_value=mock.Mock(f_favail=321)):
                for heavy, label in ((False, "standard"), (True, "heavy")):
                    with self.subTest(heavy=heavy), redirect_stderr(StringIO()) as output:
                        observation = MODULE.record_gradle_resource_telemetry(heavy)
                    self.assertEqual(123 * 1024, observation["mem_available_bytes"])
                    self.assertEqual(456 * 1024, observation["swap_free_bytes"])
                    self.assertEqual(789, observation["disk_available_bytes"])
                    self.assertEqual(321, observation["inode_available"])
                    self.assertEqual(label, observation["gradle_label"])
                    self.assertEqual([], observation["telemetry_errors"])
                    self.assertIn('"admission_gate": "disabled_by_user_2026-08-28"', output.getvalue())

    def test_resource_telemetry_collection_failure_is_visible_and_non_blocking(self):
        with mock.patch.object(
            MODULE, "read_meminfo_resource_bytes", side_effect=OSError("meminfo unavailable")
        ), mock.patch.object(
            MODULE.shutil, "disk_usage", side_effect=OSError("disk unavailable")
        ), mock.patch.object(
            MODULE.os, "statvfs", side_effect=OSError("inode unavailable")
        ), redirect_stderr(StringIO()) as output:
            observation = MODULE.record_gradle_resource_telemetry(False)

        self.assertIsNone(observation["mem_available_bytes"])
        self.assertIsNone(observation["swap_free_bytes"])
        self.assertIsNone(observation["disk_available_bytes"])
        self.assertIsNone(observation["inode_available"])
        self.assertEqual(
            ["meminfo:OSError", "disk:OSError", "inode:OSError"],
            observation["telemetry_errors"],
        )
        self.assertIn("RESOURCE_OBSERVATION", output.getvalue())

    def test_notification_outbox_deduplicates_same_event(self):
        with tempfile.TemporaryDirectory() as directory:
            self.install_temp_control_plane(directory)
            with redirect_stdout(StringIO()) as output:
                MODULE.emit_notification("A", "completed", "next", {"x": 1})
                MODULE.emit_notification("A", "completed", "next", {"x": 1})
            lines = MODULE.NOTIFICATION_OUTBOX.read_text(encoding="utf-8").splitlines()
            self.assertEqual(1, len(lines))
            self.assertIn("NOTIFY_REUSED", output.getvalue())

    def test_conflict_alert_notifies_without_mutating_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path, _ = self.install_temp_control_plane(directory)
            before = ledger_path.read_bytes()
            args = Namespace(
                requesting_task="B",
                conflicting_task="A",
                summary="B is waiting for the active source writer",
                next_action="coordinate with the exact A owner; do not preempt",
            )
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(0, MODULE.cmd_conflict_alert(args))
            self.assertEqual(before, ledger_path.read_bytes())
            records = [
                json.loads(line)
                for line in MODULE.NOTIFICATION_OUTBOX.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(1, len(records))
            self.assertEqual("coordination_required", records[0]["event"])
            self.assertEqual("B", records[0]["details"]["requesting_task"])
            self.assertEqual("A", records[0]["details"]["conflicting_task"])
            self.assertEqual(
                "alert_only_no_process_or_evidence_operation",
                records[0]["details"]["policy"],
            )
            self.assertIn("NOTIFY", output.getvalue())

    def test_orchestrator_has_no_process_termination_primitive(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\bos\.kill\s*\(")
        self.assertNotRegex(source, r"\b(?:signal\.)?SIG(?:TERM|KILL)\b")
        self.assertNotRegex(source, r"\bsystemctl\b[^\n]*\bstop\b")

    def test_claim_rejects_blocked_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            self.install_temp_control_plane(directory)
            args = Namespace(
                task_id="B",
                agent="writer",
                profile="critical_worker",
                commit_sha="a" * 40,
                tree_sha="b" * 40,
                next_action="write B",
            )
            with self.assertRaises(SystemExit):
                MODULE.cmd_claim(args)

    def test_claim_allows_parallel_noncritical_ready_task(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.valid_ledger()
            ledger["tasks"]["B"]["current_gate"] = "waiting_writer"
            ledger["tasks"]["B"]["blocker"] = None
            self.install_temp_control_plane(directory, ledger)
            args = Namespace(
                task_id="B",
                agent="writer-b",
                profile="critical_worker",
                commit_sha="c" * 40,
                tree_sha="d" * 40,
                next_action="write B independently",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(0, MODULE.cmd_claim(args))
            updated = MODULE.load_ledger()
            self.assertEqual("claimed", updated["tasks"]["B"]["current_gate"])
            self.assertEqual("writer-b", updated["tasks"]["B"]["owner"]["agent"])
            self.assertEqual("implementing", updated["tasks"]["A"]["current_gate"])

    def test_save_ledger_preserves_yaml_outside_embedded_block_and_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger_path, _ = self.install_temp_control_plane(directory)
            os.chmod(str(ledger_path), 0o755)
            ledger = MODULE.load_ledger()
            ledger["tasks"]["A"]["next_action"] = "changed"
            MODULE.save_ledger(ledger)
            text = ledger_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("schema_version: 1\n"))
            self.assertTrue(text.endswith("tasks: []\n"))
            self.assertIn('"next_action": "changed"', text)
            self.assertEqual(0o755, ledger_path.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
