import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(HERE, "cyf-juyiting-health.py")
CARRIER_PATH = os.path.join(HERE, "cyf-juyiting-recovery-carrier.py")
SPEC = importlib.util.spec_from_file_location("cyf_juyiting_health", MODULE_PATH)
health = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(health)
CARRIER_SPEC = importlib.util.spec_from_file_location(
    "cyf_juyiting_recovery_carrier", CARRIER_PATH)
carrier_module = importlib.util.module_from_spec(CARRIER_SPEC)
CARRIER_SPEC.loader.exec_module(carrier_module)


def stopped():
    return {"healthy": False, "classification": "stopped", "recovery_safe": True,
            "returncode": 3, "pid": None, "elapsed_seconds": None}


def up():
    return {"healthy": True, "classification": "up", "recovery_safe": False,
            "returncode": 0, "pid": 123, "elapsed_seconds": 2000}


def busy():
    return {"healthy": False, "classification": "canonical_busy_or_error",
            "recovery_safe": False, "returncode": 1, "pid": None, "elapsed_seconds": None}


def unsafe():
    return {"healthy": False, "classification": "canonical_unsafe_identity_or_listener",
            "recovery_safe": False, "returncode": 5, "pid": None, "elapsed_seconds": None}


def not_ready(age=1600, safe=True, pid=123):
    return {"healthy": False,
            "classification": "not_ready_trusted" if safe else "not_ready_identity_incomplete",
            "recovery_safe": safe, "returncode": 4, "pid": pid,
            "elapsed_seconds": age}


class FakeEffects(object):
    def __init__(self, statuses=None):
        self.statuses = list(statuses or [up()])
        self.recoveries = []
        self.recovery_calls = []
        self.recovery_rc = 0
        self.carrier_rc = None
        self.dispatch_confirmed = True
        self.native_invoked = True
        self.terminal_confirmed = True
        self.recovery_precondition_result = {
            "permitted": True, "classification": "recovery_carrier_files_ready"}
        self.recovery_exception = None
        self.recovery_observer = None
        self.web_result = {"healthy": True, "classification": "web_ok"}
        self.public_api_result = {"healthy": True, "classification": "auth_boundary_ok"}
        self.mysql_result = {"healthy": True, "classification": "mysql_reachable"}
        self.redis_result = {"healthy": True, "classification": "redis_reachable"}
        self.agent_result = {"healthy": True, "classification": "agent_active"}
        self.resource_result = {"healthy": True, "classification": "resources_ok"}
        self.mail_results = []
        self.mail_calls = []
        self.events = []
        self.mail_observer = None

    def canonical_status(self):
        self.events.append("status")
        if len(self.statuses) > 1:
            return self.statuses.pop(0)
        return self.statuses[0]

    def recovery_precondition(self, action, incident_id, attempt):
        self.events.append("recovery_precondition")
        return dict(self.recovery_precondition_result)

    def recover(self, action, incident_id, attempt, dispatch_callback,
                native_invoked_callback):
        self.events.append("recover:" + action)
        self.recoveries.append(action)
        self.recovery_calls.append((action, incident_id, attempt))
        if self.recovery_observer is not None:
            self.recovery_observer(action, incident_id, attempt)
        if self.recovery_exception is not None:
            raise self.recovery_exception
        carrier_rc = self.recovery_rc if self.carrier_rc is None else self.carrier_rc
        if self.dispatch_confirmed is True:
            dispatch_callback()
        if self.native_invoked is True:
            native_invoked_callback()
        if self.dispatch_confirmed is False:
            return {
                "returncode": carrier_rc, "carrier_returncode": carrier_rc,
                "dispatch_confirmed": False, "native_invoked": False,
                "native_returncode": None, "terminal_confirmed": True,
                "classification": "carrier_failed_exit_%d" % carrier_rc,
            }
        native_returncode = self.recovery_rc if self.native_invoked is True else None
        return {
            "returncode": self.recovery_rc if native_returncode is not None else 126,
            "carrier_returncode": carrier_rc if self.terminal_confirmed else None,
            "dispatch_confirmed": self.dispatch_confirmed,
            "native_invoked": self.native_invoked,
            "native_returncode": native_returncode,
            "terminal_confirmed": self.terminal_confirmed,
            "classification": "native_exit_%d" % self.recovery_rc
            if native_returncode is not None else "native_result_unknown",
        }

    def web(self, marker):
        self.events.append("web")
        return dict(self.web_result)

    def public_api(self):
        self.events.append("public_api")
        return dict(self.public_api_result)

    def elasticsearch(self):
        return getattr(self, "es_result", {"healthy": True, "classification": "es_search_ok_green"})

    def mysql(self):
        self.events.append("mysql")
        return dict(self.mysql_result)

    def redis(self):
        self.events.append("redis")
        return dict(self.redis_result)

    def agent(self):
        self.events.append("agent")
        return dict(self.agent_result)

    def resources(self):
        self.events.append("resources")
        return dict(self.resource_result)

    def send_email(self, subject, body):
        self.events.append("mail")
        self.mail_calls.append((subject, body))
        if self.mail_observer is not None:
            self.mail_observer(subject, body)
        if self.mail_results:
            return self.mail_results.pop(0)
        return True, "helper_accepted"


class Clock(object):
    def __init__(self, now=2000000000):
        self.now = now

    def __call__(self):
        return self.now


class AdvancingClock(object):
    def __init__(self, now=2000000000):
        self.now = now

    def __call__(self):
        value = self.now
        self.now += 1
        return value


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.config = {"schema_version": 1, "web_marker": '<div id="app"></div>',
                       "email_enabled": True, "reminder_interval_seconds": 21600}
        self.persisted = []

    def monitor(self, effects, maintenance_check=None):
        return health.Monitor(
            effects, lambda state: self.persisted.append(json.loads(json.dumps(state))),
            self.clock, maintenance_check or (lambda: False))

    def test_stopped_threshold_starts_on_third_failure(self):
        effects = FakeEffects([stopped(), stopped(), stopped(), stopped(), up()])
        state = health.initial_state(self.clock.now)
        monitor = self.monitor(effects)
        monitor.check_once(state, self.config)
        monitor.check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        result = monitor.check_once(state, self.config)
        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual("success_health_up", result["recovery"]["result"])
        recovery_index = effects.events.index("recover:start")
        self.assertIn("mail", effects.events[:recovery_index])
        fenced = [item for item in self.persisted if item["recovery"]["in_flight"]]
        self.assertEqual(1, fenced[-1]["recovery"]["attempts"])
        native_fenced = [item for item in fenced
                         if "native_invoked_at" in item["recovery"]["in_flight"]]
        dispatch_fenced = [item for item in fenced
                           if "dispatch_at" in item["recovery"]["in_flight"]]
        dispatch_only = [item for item in dispatch_fenced
                         if "native_invoked_at" not in item["recovery"]["in_flight"]]
        self.assertEqual(1, len(dispatch_only))
        self.assertEqual(1, len(native_fenced))
        self.assertLessEqual(
            dispatch_only[0]["recovery"]["in_flight"]["dispatch_at"],
            native_fenced[0]["recovery"]["in_flight"]["native_invoked_at"])

    def test_rc1_busy_never_recovers(self):
        effects = FakeEffects([busy()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual("identity_or_status_not_recovery_safe", result["recovery"]["decision"])

    def test_rc5_foreign_identity_never_recovers(self):
        effects = FakeEffects([unsafe()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)

    def test_external_only_failure_never_recovers_healthy_api(self):
        effects = FakeEffects([up()])
        effects.public_api_result = {"healthy": False, "classification": "auth_boundary_invalid"}
        state = health.initial_state(self.clock.now)
        monitor = self.monitor(effects)
        for _ in range(3):
            monitor.check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual("local_api_up", state["last_snapshot"]["recovery"]["decision"])
        self.assertEqual(["public_api"], state["incident"]["components"])

    def test_maintenance_reports_but_pauses_recovery(self):
        effects = FakeEffects([stopped()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config, maintenance=True)
        self.assertEqual([], effects.recoveries)
        self.assertTrue(result["maintenance"])
        self.assertEqual("maintenance_paused", result["recovery"]["decision"])
        self.assertFalse(state["last_snapshot"]["checks"]["local_api"]["healthy"])

    def test_cooldown_blocks_second_attempt(self):
        effects = FakeEffects([stopped()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 1
        state["recovery"]["last_attempt_at"] = self.clock.now - 30
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual("cooldown", result["recovery"]["decision"])

    def test_interrupted_attempt_is_fenced(self):
        effects = FakeEffects([stopped()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 1
        state["recovery"]["last_attempt_at"] = self.clock.now - 10
        state["recovery"]["in_flight"] = {"action": "start", "attempt": 1,
                                            "at": self.clock.now - 10}
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual(1, state["recovery"]["attempts"])
        self.assertIsNotNone(state["recovery"]["in_flight"])

    def test_three_trusted_up_checks_clear_early_interruption_before_new_incident(self):
        for interrupted_attempt in (1, 2):
            with self.subTest(interrupted_attempt=interrupted_attempt):
                effects = FakeEffects([up()])
                state = health.initial_state(self.clock.now)
                state["incident"] = {
                    "id": "I000017-1788676023", "opened_at": self.clock.now - 600,
                    "components": ["local_api"], "last_reminder_slot": 0,
                }
                state["recovery"].update({
                    "attempts": interrupted_attempt,
                    "last_attempt_at": self.clock.now - 120,
                    "in_flight": {"action": "start", "attempt": interrupted_attempt,
                                  "at": self.clock.now - 120},
                })
                monitor = self.monitor(effects)

                for _ in range(3):
                    monitor.check_once(state, self.config)

                self.assertIsNone(state["incident"])
                self.assertEqual(0, state["recovery"]["attempts"])
                self.assertFalse(state["recovery"]["circuit_latched"])
                self.assertIsNone(state["recovery"]["in_flight"])
                self.assertIsNone(state["recovery"]["last_result"])
                self.assertFalse(any(item["event"] == "recovery_exhausted"
                                     for item in state["outbox"]))

                effects.statuses = [stopped(), stopped(), up()]
                state["component_streaks"]["local_api"] = 2
                monitor.check_once(state, self.config)
                self.assertEqual(["start"], effects.recoveries)
                self.assertEqual(1, state["recovery"]["attempts"])
                self.assertNotEqual("I000017-1788676023", state["incident"]["id"])

    def test_three_failures_latch_and_never_invoke_a_fourth_recovery(self):
        effects = FakeEffects([stopped()] * 12)
        effects.recovery_rc = 1
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        monitor = self.monitor(effects)
        for expected in (1, 2, 3):
            monitor.check_once(state, self.config)
            self.assertEqual(expected, state["recovery"]["attempts"])
            self.clock.now += health.COOLDOWN_SECONDS
        self.assertEqual(["start", "start", "start"], effects.recoveries)
        self.assertTrue(state["recovery"]["circuit_latched"])
        monitor.check_once(state, self.config)
        self.assertEqual(["start", "start", "start"], effects.recoveries)
        self.assertEqual("circuit_latched", state["last_snapshot"]["recovery"]["decision"])

    def test_third_success_does_not_latch_or_send_exhausted_failure(self):
        effects = FakeEffects([stopped(), stopped(), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 2
        state["recovery"]["last_attempt_at"] = self.clock.now - health.COOLDOWN_SECONDS
        def observe(action, incident_id, attempt):
            fenced = self.persisted[-1]["recovery"]
            self.assertEqual(3, fenced["attempts"])
            self.assertEqual({"action": "start", "attempt": 3, "at": self.clock.now},
                             fenced["in_flight"])
        effects.recovery_observer = observe
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(3, state["recovery"]["attempts"])
        self.assertFalse(state["recovery"]["circuit_latched"])
        self.assertEqual(1, state["api_healthy_streak"])
        self.assertFalse(any(subject in (
            health.SUBJECT_RECOVERY_EXHAUSTED,
            health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
        ) for subject, _ in effects.mail_calls))
        self.assertTrue(any("恢复成功（3/3）" in subject
                            for subject, _ in effects.mail_calls))

    def test_three_healthy_checks_reset_circuit(self):
        effects = FakeEffects([up()])
        state = health.initial_state(self.clock.now)
        state["recovery"].update({"attempts": 3, "circuit_latched": True,
                                  "last_attempt_at": self.clock.now - 100,
                                  "in_flight": {"action": "start", "attempt": 3,
                                                "at": self.clock.now - 100}})
        monitor = self.monitor(effects)
        for _ in range(3):
            monitor.check_once(state, self.config)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertFalse(state["recovery"]["circuit_latched"])
        self.assertIsNone(state["recovery"]["in_flight"])

    def test_dependency_down_blocks_recovery(self):
        effects = FakeEffects([stopped()])
        effects.mysql_result = {"healthy": False, "classification": "mysql_refused"}
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual("dependencies_unreachable", result["recovery"]["decision"])

    def test_not_ready_requires_grace_and_full_identity(self):
        effects = FakeEffects([not_ready(1499)])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual("startup_grace", result["recovery"]["decision"])
        self.assertEqual([], effects.recoveries)

        effects = FakeEffects([not_ready(1500), not_ready(1600), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(["restart"], effects.recoveries)

    def test_rc4_without_runtime_identity_is_alert_only(self):
        effects = FakeEffects([not_ready(5000, safe=False)])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual("identity_or_status_not_recovery_safe", result["recovery"]["decision"])

    def test_exit_zero_without_fresh_up_is_failure(self):
        effects = FakeEffects([stopped(), stopped(), not_ready(1700)])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual("failed_fresh_health_not_up", result["recovery"]["result"])
        self.assertIsNone(state["recovery"]["last_success_at"])

    def test_native_rc1_with_surviving_trusted_java_is_recorded_without_second_actor(self):
        for fresh in (up(), not_ready(1200)):
            with self.subTest(fresh=fresh["classification"]):
                effects = FakeEffects([stopped(), stopped(), fresh])
                effects.recovery_rc = 1
                state = health.initial_state(self.clock.now)
                state["component_streaks"]["local_api"] = 2
                monitor = self.monitor(effects)

                result = monitor.check_once(state, self.config)

                self.assertEqual(["start"], effects.recoveries)
                self.assertEqual(1, state["recovery"]["attempts"])
                self.assertEqual("failed_fresh_health_not_up",
                                 result["recovery"]["result"])
                self.assertEqual("native_exit_1",
                                 result["recovery"]["native_result"])
                self.assertTrue(state["recovery"]["last_result"]["native_invoked"])
                self.assertEqual(1, state["recovery"]["last_result"]["native_returncode"])
                self.assertIsNone(state["recovery"]["last_success_at"])

                self.clock.now += health.COOLDOWN_SECONDS
                monitor.check_once(state, self.config)
                self.assertEqual(["start"], effects.recoveries)

    def test_untrusted_recovery_carrier_is_precondition_skip_not_attempt(self):
        effects = FakeEffects([stopped(), stopped()])
        effects.recovery_precondition_result = {
            "permitted": False,
            "classification": "recovery_carrier_unsafe_executable_owner",
        }
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2

        result = self.monitor(effects).check_once(state, self.config)

        self.assertEqual([], effects.recoveries)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertEqual("not_attempted_after_carrier_precondition",
                         result["recovery"]["result"])
        self.assertEqual("recovery_carrier_unsafe_executable_owner",
                         result["recovery"]["decision"])

    def test_definitive_prelaunch_failure_rolls_back_reserved_third_attempt(self):
        effects = FakeEffects([stopped(), stopped()])
        effects.dispatch_confirmed = False
        effects.native_invoked = False
        effects.carrier_rc = 1
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 2
        previous_attempt_at = self.clock.now - health.COOLDOWN_SECONDS
        state["recovery"]["last_attempt_at"] = previous_attempt_at

        result = self.monitor(effects).check_once(state, self.config)

        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual(2, effects.events.count("status"))
        self.assertEqual(2, state["recovery"]["attempts"])
        self.assertEqual(previous_attempt_at, state["recovery"]["last_attempt_at"])
        self.assertFalse(state["recovery"]["circuit_latched"])
        self.assertIsNone(state["recovery"]["in_flight"])
        self.assertEqual("carrier_failed_not_invoked",
                         state["recovery"]["last_result"]["classification"])
        self.assertFalse(state["recovery"]["last_result"]["dispatch_confirmed"])
        self.assertFalse(state["recovery"]["last_result"]["native_invoked"])
        self.assertIsNone(state["recovery"]["last_result"]["native_returncode"])
        self.assertEqual(1, state["recovery"]["last_result"]["carrier_returncode"])
        self.assertEqual("not_attempted_carrier_failed", result["recovery"]["result"])
        self.assertFalse(any(item["event"] == "recovery_exhausted"
                             for item in state["outbox"]))

    def test_post_dispatch_missing_native_marker_retains_attempt_as_unknown(self):
        effects = FakeEffects([stopped(), stopped(), stopped()])
        effects.dispatch_confirmed = True
        effects.native_invoked = None
        effects.carrier_rc = 1
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2

        result = self.monitor(effects).check_once(state, self.config)

        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual(1, state["recovery"]["attempts"])
        self.assertIsNone(state["recovery"]["in_flight"])
        self.assertEqual("unknown_dispatch_or_terminal",
                         state["recovery"]["last_result"]["classification"])
        self.assertTrue(state["recovery"]["last_result"]["dispatch_confirmed"])
        self.assertIsNone(state["recovery"]["last_result"]["native_invoked"])
        self.assertIsNone(state["recovery"]["last_result"]["native_returncode"])
        self.assertEqual("unknown_dispatch_or_terminal",
                         result["recovery"]["result"])
        unknown_mails = [(subject, body) for subject, body in effects.mail_calls
                         if "恢复未确认" in subject]
        self.assertEqual(1, len(unknown_mails))
        self.assertIn("已保留本次预算与执行围栏", unknown_mails[0][1])

    def test_stream_unknown_keeps_inflight_fence_and_prevents_second_actor(self):
        effects = FakeEffects([stopped(), stopped(), stopped()])
        effects.dispatch_confirmed = None
        effects.native_invoked = None
        effects.terminal_confirmed = False
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        monitor = self.monitor(effects)

        monitor.check_once(state, self.config)

        self.assertEqual(1, state["recovery"]["attempts"])
        self.assertIsNotNone(state["recovery"]["in_flight"])
        self.clock.now += health.COOLDOWN_SECONDS
        monitor.check_once(state, self.config)
        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual("recovery_in_flight",
                         state["last_snapshot"]["recovery"]["decision"])

    def test_third_post_dispatch_unknown_latches_alert_and_never_calls_fourth(self):
        effects = FakeEffects([stopped()] * 5)
        effects.dispatch_confirmed = True
        effects.native_invoked = None
        effects.carrier_rc = 1
        effects.mail_results = [(True, "helper_accepted"), (False, "helper_failed")]
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 2
        state["recovery"]["last_attempt_at"] = self.clock.now - health.COOLDOWN_SECONDS
        monitor = self.monitor(effects)

        monitor.check_once(state, self.config)

        self.assertEqual(3, state["recovery"]["attempts"])
        self.assertTrue(state["recovery"]["circuit_latched"])
        self.assertIsNone(state["recovery"]["in_flight"])
        self.assertEqual("unknown_dispatch_or_terminal",
                         state["recovery"]["last_result"]["classification"])
        urgent = [item for item in state["outbox"]
                  if item["event"] == "recovery_exhausted"]
        self.assertEqual(1, len(urgent))
        self.assertEqual(health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
                         urgent[0]["subject"])
        self.assertIn("结果为 UNKNOWN；已停止自动重试（3/3）", urgent[0]["body"])
        self.assertIn("不推断命令失败或成功", urgent[0]["body"])

        self.clock.now += health.COOLDOWN_SECONDS
        monitor.check_once(state, self.config)
        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual("circuit_latched",
                         state["last_snapshot"]["recovery"]["decision"])

    def test_recovery_exception_is_unknown_third_attempt_and_latches(self):
        effects = FakeEffects([stopped(), stopped(), stopped()])
        effects.recovery_exception = RuntimeError("must not escape into durable payload")
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 2
        state["recovery"]["last_attempt_at"] = self.clock.now - health.COOLDOWN_SECONDS
        def observe(action, incident_id, attempt):
            fenced = self.persisted[-1]["recovery"]
            self.assertEqual(3, fenced["attempts"])
            self.assertEqual({"action": "start", "attempt": 3, "at": self.clock.now},
                             fenced["in_flight"])
        effects.recovery_observer = observe
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(3, state["recovery"]["attempts"])
        self.assertTrue(state["recovery"]["circuit_latched"])
        self.assertEqual("unknown_dispatch_or_terminal",
                         state["recovery"]["last_result"]["classification"])
        self.assertIsNone(state["recovery"]["last_result"]["dispatch_confirmed"])
        self.assertIsNone(state["recovery"]["last_result"]["native_invoked"])
        exhausted = [item for item in state["notice_ids"]
                     if item.endswith("recovery-exhausted")]
        self.assertEqual(1, len(exhausted))

    def test_recovery_result_mail_uses_actual_completion_time(self):
        effects = FakeEffects([stopped(), stopped(), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        started_at = self.clock.now
        def complete_after_long_start(action, incident_id, attempt):
            self.clock.now += 11 * 60
        effects.recovery_observer = complete_after_long_start
        self.monitor(effects).check_once(state, self.config)
        completed_at = started_at + 11 * 60
        self.assertEqual(completed_at, state["recovery"]["last_result"]["at"])
        result_bodies = [body for subject, body in effects.mail_calls
                         if "恢复成功" in subject]
        self.assertEqual(1, len(result_bodies))
        self.assertIn(health.asia_shanghai_text(completed_at), result_bodies[0])

    def test_post_mail_restart_revalidation_healthy_skips_command(self):
        effects = FakeEffects([not_ready(1600), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertEqual("revalidation_became_healthy", result["recovery"]["decision"])

    def test_post_mail_restart_revalidation_pid_change_skips_command(self):
        effects = FakeEffects([not_ready(1600, pid=123), not_ready(1700, pid=124)])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertEqual("revalidation_restart_pid_changed", result["recovery"]["decision"])

    def test_post_mail_restart_same_identity_executes(self):
        effects = FakeEffects([not_ready(1600, pid=123), not_ready(1700, pid=123), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(["restart"], effects.recoveries)
        first_mail = effects.events.index("mail")
        second_status = effects.events.index("status", effects.events.index("status") + 1)
        self.assertLess(first_mail, second_status)
        self.assertLess(second_status, effects.events.index("recover:restart"))

    def test_post_mail_maintenance_change_rechecks_dependencies_and_skips_without_count(self):
        effects = FakeEffects([stopped(), stopped()])
        maintenance = [False]
        effects.mail_observer = lambda subject, body: maintenance.__setitem__(0, True)
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2

        result = self.monitor(effects, lambda: maintenance[0]).check_once(state, self.config)

        self.assertEqual([], effects.recoveries)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertEqual("revalidation_maintenance_active_or_unknown",
                         result["recovery"]["decision"])
        self.assertEqual(2, effects.events.count("mysql"))
        self.assertEqual(2, effects.events.count("redis"))
        self.assertTrue(state["last_snapshot"]["maintenance"])
        self.assertEqual("maintenance_enabled",
                         state["last_snapshot"]["checks"]
                         ["maintenance_revalidation"]["classification"])

    def test_post_mail_dependency_change_skips_without_count(self):
        for dependency in ("mysql", "redis"):
            with self.subTest(dependency=dependency):
                effects = FakeEffects([stopped(), stopped()])
                def change_dependency(subject, body, target=dependency):
                    setattr(effects, target + "_result",
                            {"healthy": False, "classification": target + "_refused"})
                effects.mail_observer = change_dependency
                state = health.initial_state(self.clock.now)
                state["component_streaks"]["local_api"] = 2

                result = self.monitor(effects).check_once(state, self.config)

                self.assertEqual([], effects.recoveries)
                self.assertEqual(0, state["recovery"]["attempts"])
                self.assertEqual("revalidation_dependencies_unreachable",
                                 result["recovery"]["decision"])
                self.assertFalse(state["last_snapshot"]["checks"]
                                 [dependency + "_revalidation"]["healthy"])

    def test_each_mixed_window_probe_has_its_actual_observation_time(self):
        clock = AdvancingClock(self.clock.now)
        effects = FakeEffects([stopped(), stopped(), up()])
        state = health.initial_state(clock.now)
        state["component_streaks"]["local_api"] = 2
        persisted = []
        monitor = health.Monitor(
            effects, lambda value: persisted.append(json.loads(json.dumps(value))),
            clock, lambda: False)

        monitor.check_once(state, self.config)

        snapshot = state["last_snapshot"]
        checks = snapshot["checks"]
        for name in health.COMPONENTS:
            self.assertIn("observed_at", checks[name])
        ordered = [
            checks["local_api"]["observed_at"],
            checks["resource_observation"]["observed_at"],
            checks["maintenance_revalidation"]["observed_at"],
            checks["mysql_revalidation"]["observed_at"],
            checks["redis_revalidation"]["observed_at"],
            checks["local_api_revalidation"]["observed_at"],
            checks["local_api_post_recovery"]["observed_at"],
        ]
        self.assertLess(snapshot["at"], ordered[0])
        self.assertEqual(sorted(ordered), ordered)
        self.assertEqual(len(ordered), len(set(ordered)))

    def test_current_attempt_mail_is_durable_and_prioritized(self):
        effects = FakeEffects([stopped(), stopped(), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        health.enqueue_notice(state, "old-1", "incident_confirmed", "old one", "body", self.clock.now)
        health.enqueue_notice(state, "old-2", "incident_confirmed", "old two", "body", self.clock.now)
        def observe(subject, body):
            self.assertTrue(any(
                any(item["event"] == "recovery_attempted" for item in snapshot["outbox"])
                for snapshot in self.persisted))
        effects.mail_observer = observe
        self.monitor(effects).check_once(state, self.config)
        self.assertTrue(effects.mail_calls[0][0].startswith("【监控】准备恢复（1/3）"))
        self.assertEqual(["start"], effects.recoveries)

    def test_full_outbox_preserves_failed_priority_recovery_notice(self):
        effects = FakeEffects([stopped(), stopped(), up()])
        effects.mail_results = [(False, "helper_failed")]
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        for number in range(health.MAX_OUTBOX):
            health.enqueue_notice(
                state, "old-%d" % number, "recovery_result",
                "old recovery result", "old body", self.clock.now)

        def observe(subject, body):
            if subject.startswith("【监控】准备恢复（1/3）"):
                durable = self.persisted[-1]["outbox"]
                self.assertTrue(any(item["event"] == "digest" for item in durable))
                self.assertTrue(any(item["event"] == "recovery_attempted"
                                    for item in durable))
        effects.mail_observer = observe
        self.monitor(effects).check_once(state, self.config)

        self.assertEqual(["start"], effects.recoveries)
        self.assertTrue(effects.mail_calls[0][0].startswith(
            "【监控】准备恢复（1/3）"))
        current = [item for item in state["outbox"]
                   if item["event"] == "recovery_attempted"]
        self.assertEqual(1, len(current))
        self.assertIn("动作=启动；尝试=1/3", current[0]["body"])
        self.assertEqual(1, current[0]["attempts"])
        self.assertGreater(current[0]["next_attempt_at"], self.clock.now)
        self.assertEqual("helper_failed", current[0]["last_error"])
        self.assertTrue(any(subject == health.SUBJECT_DIGEST
                            for subject, _ in effects.mail_calls[1:]))
        self.assertLessEqual(len(state["outbox"]), health.MAX_OUTBOX)

    def test_resource_warning_does_not_block_recovery(self):
        effects = FakeEffects([stopped(), stopped(), up()])
        effects.resource_result = {"healthy": False,
                                   "classification": "resources_below_canonical_minimum"}
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        result = self.monitor(effects).check_once(state, self.config)
        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual(1, state["recovery"]["attempts"])
        self.assertEqual("warning:resources_below_canonical_minimum",
                         result["recovery"]["resource_observation"])

    def test_precondition_and_revalidation_skips_do_not_consume_attempts(self):
        effects = FakeEffects([stopped()])
        effects.mysql_result = {"healthy": False, "classification": "mysql_refused"}
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(0, state["recovery"]["attempts"])

        effects = FakeEffects([stopped(), up()])
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(0, state["recovery"]["attempts"])
        self.assertEqual([], effects.recoveries)

    def test_third_failure_alert_is_durable_prioritized_deduped_and_survives_mail_failure(self):
        effects = FakeEffects([stopped(), stopped(), stopped(), stopped()])
        effects.recovery_rc = 1
        effects.mail_results = [(True, "helper_accepted"), (False, "helper_failed")]
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["recovery"]["attempts"] = 2
        state["recovery"]["last_attempt_at"] = self.clock.now - health.COOLDOWN_SECONDS
        health.enqueue_notice(state, "old-1", "incident_confirmed", "旧通知", "旧正文", self.clock.now)
        self.monitor(effects).check_once(state, self.config)

        self.assertTrue(state["recovery"]["circuit_latched"])
        self.assertEqual(health.SUBJECT_RECOVERY_EXHAUSTED,
                         effects.mail_calls[1][0])
        body = effects.mail_calls[1][1]
        self.assertIn("恢复失败，已停止自动重试（3/3）", body)
        self.assertIn("服务影响：", body)
        self.assertIn("已确认：", body)
        self.assertIn("未知原因：", body)
        self.assertIn("尝试=3/3；动作=启动；返回码=1；恢复后健康=未确认", body)
        self.assertIn("下一步：", body)
        self.assertIn("CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0", body)
        self.assertIn(health.asia_shanghai_text(self.clock.now), body)
        urgent = [item for item in state["outbox"]
                  if item["event"] == "recovery_exhausted"]
        self.assertEqual(1, len(urgent))
        self.assertEqual(1, urgent[0]["attempts"])
        self.assertEqual("helper_failed", urgent[0]["last_error"])

        # A later tick cannot attempt recovery again; the same urgent notice remains single.
        self.clock.now = urgent[0]["next_attempt_at"]
        effects.mail_results = [(True, "helper_accepted")]
        self.monitor(effects).check_once(state, self.config)
        self.assertEqual(["start"], effects.recoveries)
        self.assertEqual(1, sum(item.endswith("recovery-exhausted")
                                for item in state["notice_ids"]))
        self.assertNotIn("recovery_exhausted", [item["event"] for item in state["outbox"]])

    def test_interrupted_third_attempt_latches_unknown_alert_and_never_invokes_fourth(self):
        effects = FakeEffects([stopped()])
        effects.mail_results = [(False, "helper_failed")]
        state = health.initial_state(self.clock.now)
        state["component_streaks"]["local_api"] = 2
        state["incident"] = {"id": "I000017-1788676023", "opened_at": self.clock.now - 600,
                             "components": ["local_api"], "last_reminder_slot": 0}
        state["recovery"].update({
            "attempts": 3, "last_attempt_at": self.clock.now - 120,
            "in_flight": {"action": "start", "attempt": 3, "at": self.clock.now - 120},
        })
        monitor = self.monitor(effects)

        monitor.check_once(state, self.config)

        self.assertEqual([], effects.recoveries)
        self.assertTrue(state["recovery"]["circuit_latched"])
        self.assertIsNone(state["recovery"]["in_flight"])
        self.assertEqual("unknown_interrupted_no_terminal_receipt",
                         state["recovery"]["last_result"]["classification"])
        urgent = [item for item in state["outbox"]
                  if item["event"] == "recovery_exhausted"]
        self.assertEqual(1, len(urgent))
        self.assertEqual(health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
                         urgent[0]["subject"])
        self.assertIn("UNKNOWN", urgent[0]["body"])
        self.assertIn("不把中断推断为已确认命令失败或成功", urgent[0]["body"])
        self.assertEqual("helper_failed", urgent[0]["last_error"])

        self.clock.now = urgent[0]["next_attempt_at"]
        effects.mail_results = [(True, "helper_accepted")]
        monitor.check_once(state, self.config)
        self.assertEqual([], effects.recoveries)
        self.assertEqual(1, sum(item.endswith("recovery-exhausted")
                                for item in state["notice_ids"]))


class MailQueueTests(unittest.TestCase):
    def test_email_retry_and_dedup(self):
        now = 2000000000
        state = health.initial_state(now)
        added = health.enqueue_notice(state, "same", "incident_confirmed", "subject", "body", now)
        duplicate = health.enqueue_notice(state, "same", "incident_confirmed", "subject", "body", now)
        self.assertTrue(added)
        self.assertFalse(duplicate)
        effects = FakeEffects()
        effects.mail_results = [(False, "helper_failed")]
        config = {"email_enabled": True}
        self.assertEqual(0, health.flush_outbox(state, effects, config, now, 2))
        self.assertEqual(1, len(state["outbox"]))
        self.assertGreater(state["outbox"][0]["next_attempt_at"], now)
        effects.mail_results = [(True, "helper_accepted")]
        retry_at = state["outbox"][0]["next_attempt_at"]
        self.assertEqual(1, health.flush_outbox(state, effects, config, retry_at, 2))
        self.assertEqual([], state["outbox"])

    def test_outbox_is_bounded_and_coalesces(self):
        state = health.initial_state(1)
        for number in range(health.MAX_OUTBOX + 10):
            health.enqueue_notice(state, "n%d" % number, "recovery_result", "subject", "body", number + 1)
        self.assertLessEqual(len(state["outbox"]), health.MAX_OUTBOX)
        self.assertTrue(any(item["event"] == "digest" for item in state["outbox"]))

    def test_full_outbox_reminder_never_evicts_exhausted_alert(self):
        state = health.initial_state(1)
        health.enqueue_notice(
            state, "urgent", "recovery_exhausted",
            health.SUBJECT_RECOVERY_EXHAUSTED, "关键告警", 1)
        for number in range(health.MAX_OUTBOX - 1):
            health.enqueue_notice(state, "old-%d" % number, "recovery_result",
                                  "旧通知", "旧正文", number + 2)
        self.assertEqual(health.MAX_OUTBOX, len(state["outbox"]))
        health.enqueue_notice(state, "later-reminder", "reminder",
                              health.SUBJECT_REMINDER, "提醒正文", 100)
        self.assertEqual(health.MAX_OUTBOX, len(state["outbox"]))
        urgent = [item for item in state["outbox"]
                  if item["event"] == "recovery_exhausted"]
        self.assertEqual(1, len(urgent))
        self.assertEqual("关键告警", urgent[0]["body"])
        self.assertTrue(any(item["event"] == "digest" for item in state["outbox"]))

    def test_new_priority_never_evicts_existing_exhausted_alerts(self):
        state = health.initial_state(1)
        for number in range(health.MAX_PRIORITY_OUTBOX):
            self.assertTrue(health.enqueue_notice(
                state, "urgent-%d" % number, "recovery_exhausted",
                health.SUBJECT_RECOVERY_EXHAUSTED, "关键告警%d" % number,
                number + 1))
        before = [item["id"] for item in state["outbox"]]

        added = health.enqueue_notice(
            state, "new-attempt", "recovery_attempted",
            health.SUBJECT_RECOVERY_ATTEMPT % (1, 3), "新优先通知", 100)

        self.assertFalse(added)
        self.assertEqual(before, [item["id"] for item in state["outbox"]])
        self.assertNotIn("new-attempt", state["notice_ids"])

    def test_new_exhausted_alert_evicts_only_noncritical_items(self):
        state = health.initial_state(1)
        health.enqueue_notice(
            state, "old-urgent", "recovery_exhausted",
            health.SUBJECT_RECOVERY_EXHAUSTED, "旧关键告警", 1)
        for number in range(health.MAX_OUTBOX - 1):
            health.enqueue_notice(state, "ordinary-%d" % number, "recovery_result",
                                  "普通通知", "普通正文", number + 2)

        self.assertTrue(health.enqueue_notice(
            state, "new-urgent", "recovery_exhausted",
            health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN, "新关键告警", 100))

        critical = {item["id"]: item["body"] for item in state["outbox"]
                    if item["event"] == "recovery_exhausted"}
        self.assertEqual("旧关键告警", critical["old-urgent"])
        self.assertEqual("新关键告警", critical["new-urgent"])
        self.assertLessEqual(len(state["outbox"]), health.MAX_PRIORITY_OUTBOX)

    def test_mail_fields_are_sanitized_and_bounded(self):
        state = health.initial_state(1)
        health.enqueue_notice(
            state, "safe-id", "incident_confirmed",
            "主题\r\nBcc: injected" + ("长" * 200),
            "正文\x00\r\n下一行" + ("长" * 2200), 1)
        notice = state["outbox"][0]
        self.assertNotIn("\r", notice["subject"])
        self.assertNotIn("\n", notice["subject"])
        self.assertNotIn("\x00", notice["body"])
        self.assertLessEqual(len(notice["subject"].encode("utf-8")),
                             health.MAIL_SUBJECT_MAX_BYTES)
        self.assertLessEqual(len(notice["body"]), 2000)

    def test_subject_templates_are_short_utf8_and_keep_urgent_attempt_count(self):
        subjects = (
            health.SUBJECT_DIGEST,
            health.SUBJECT_INCIDENT_CONFIRMED,
            health.SUBJECT_RESOLVED,
            health.SUBJECT_REMINDER,
            health.SUBJECT_RECOVERY_ATTEMPT % (3, 3),
            health.SUBJECT_RECOVERY_DEFERRED,
            health.SUBJECT_RECOVERY_RESULT % ("成功", 3, 3),
            health.SUBJECT_RECOVERY_RESULT % ("未成功", 3, 3),
            health.SUBJECT_RECOVERY_RESULT % ("未确认", 3, 3),
            health.SUBJECT_RECOVERY_EXHAUSTED,
            health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
            health.SUBJECT_NOTIFY_TEST,
        )
        for subject in subjects:
            with self.subTest(subject=subject):
                self.assertEqual(subject, health.sanitize_mail_subject(subject))
                self.assertLessEqual(len(subject.encode("utf-8")),
                                     health.MAIL_SUBJECT_MAX_BYTES)
        self.assertIn("3/3", health.SUBJECT_RECOVERY_EXHAUSTED)
        self.assertIn("3/3", health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN)

    def test_legacy_long_subject_is_bounded_again_at_delivery_time(self):
        old_subject = "【聚义厅监控】“三次恢复失败即停止重试”策略已安装；持锁待查"
        state = health.initial_state(1)
        state["outbox"].append({
            "id": "legacy-long", "event": "recovery_result",
            "subject": old_subject, "body": "旧正文", "created_at": 1,
            "attempts": 0, "next_attempt_at": 1, "last_error": "",
        })
        state["notice_ids"].append("legacy-long")
        health.validate_state(state)  # The pre-upgrade state remains loadable.
        effects = FakeEffects()
        effects.mail_results = [(False, "helper_failed")]

        self.assertEqual(0, health.flush_outbox(
            state, effects, {"email_enabled": True}, 1, 1,
            preferred_id="legacy-long"))

        bounded = health.sanitize_mail_subject(old_subject)
        self.assertEqual(bounded, effects.mail_calls[0][0])
        self.assertEqual(bounded, state["outbox"][0]["subject"])
        self.assertLessEqual(len(bounded.encode("utf-8")),
                             health.MAIL_SUBJECT_MAX_BYTES)
        self.assertEqual(1, state["outbox"][0]["attempts"])
        self.assertEqual("helper_failed", state["outbox"][0]["last_error"])

    def test_chinese_incident_recovery_resolved_reminder_and_test_bodies_are_action_first(self):
        events = (
            "incident_confirmed", "recovery_attempt_selected", "recovery_result",
            "resolved_after_three_healthy_checks", "restrained_reminder",
            "explicit_notify_test",
        )
        for event in events:
            body = health.notice_body(event, 2000000000, "I000017-1788676023", ["local_api"])
            self.assertIn("建议：", body)
            self.assertIn("时间（Asia/Shanghai）：", body)
            self.assertLess(body.index("建议："), body.index("时间（Asia/Shanghai）："))
            self.assertNotIn("原始日志", body)
            self.assertNotIn("邮件已送达", body)


class StateStoreSecurityTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="cyf-health-test-")
        self.state_dir = os.path.join(self.root, "state")
        self.store = health.StateStore(self.state_dir, expected_uid=os.getuid(), validate_parents=False)
        self.store.prepare_init()
        self.store.acquire()

    def tearDown(self):
        self.store.release()
        shutil.rmtree(self.root)

    def test_round_trip_atomic_state(self):
        state = health.initial_state(10)
        self.store.write(state)
        self.assertEqual(state, self.store.read())
        self.assertEqual(0o600, stat.S_IMODE(os.lstat(self.store.state_path).st_mode))

    def test_schema_v1_old_state_load_preserves_attempts_incident_and_circuit(self):
        state = health.initial_state(10)
        state["incident"] = {"id": "I000017-1788676023", "opened_at": 10,
                             "components": ["local_api"], "last_reminder_slot": 0}
        state["recovery"].update({
            "attempts": 2,
            "circuit_latched": True,
            "last_attempt_at": 20,
            "in_flight": None,
            "last_result": {"at": 20, "action": "start", "attempt": 2,
                            "classification": "failed_fresh_health_not_up"},
        })
        state["last_snapshot"] = {
            "at": 20, "maintenance": True, "overall_healthy": False,
            "checks": {name: {"healthy": False, "classification": "old"}
                       for name in health.COMPONENTS},
            "recovery": {"decision": "resources_blocked", "result": "not_attempted",
                         "resource_preflight": "resources_below_canonical_minimum"},
        }
        self.store.write(state)
        loaded = self.store.read()
        self.assertEqual("I000017-1788676023", loaded["incident"]["id"])
        self.assertEqual(2, loaded["recovery"]["attempts"])
        self.assertTrue(loaded["recovery"]["circuit_latched"])
        self.assertEqual("resources_below_canonical_minimum",
                         loaded["last_snapshot"]["recovery"]["resource_preflight"])

    def test_state_round_trip_preserves_unknown_dispatch_fence(self):
        state = health.initial_state(10)
        state["recovery"].update({
            "attempts": 1,
            "last_attempt_at": 20,
            "in_flight": {"action": "start", "attempt": 1, "at": 20,
                          "dispatch_at": 21},
            "last_result": {
                "at": 22, "action": "start", "attempt": 1,
                "classification": "unknown_dispatch_or_terminal",
                "dispatch_confirmed": None, "native_invoked": None,
                "native_returncode": None, "carrier_returncode": None,
                "terminal_confirmed": False,
            },
        })
        self.store.write(state)

        loaded = self.store.read()

        self.assertEqual(1, loaded["recovery"]["attempts"])
        self.assertEqual(21, loaded["recovery"]["in_flight"]["dispatch_at"])
        self.assertIsNone(loaded["recovery"]["last_result"]["native_invoked"])
        self.assertFalse(loaded["recovery"]["last_result"]["terminal_confirmed"])

    def test_fail_closed_missing_and_corrupt_state(self):
        with self.assertRaises(health.MonitorError):
            self.store.read()
        with open(self.store.state_path, "w") as stream:
            stream.write("not-json")
        os.chmod(self.store.state_path, 0o600)
        with self.assertRaises(health.MonitorError):
            self.store.read()

    def test_fail_closed_insecure_state_mode(self):
        self.store.write(health.initial_state(10))
        os.chmod(self.store.state_path, 0o644)
        with self.assertRaises(health.MonitorError):
            self.store.read()

    def test_nonblocking_singleton_lock(self):
        second = health.StateStore(self.state_dir, expected_uid=os.getuid(), validate_parents=False)
        with self.assertRaises(health.BusyError):
            second.acquire()
        second.release()

    def test_pause_resume_marker_and_directory_fsync(self):
        self.store.write(health.initial_state(10))
        with mock.patch.object(health.os, "fsync", wraps=health.os.fsync) as fsync:
            self.store.pause(10)
        self.assertGreaterEqual(fsync.call_count, 2)
        self.assertTrue(self.store.maintenance())
        self.store.resume()
        self.assertFalse(self.store.maintenance())


class TrustedExecutableTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="cyf-health-exec-")
        self.target = os.path.join(self.root, "python-real")
        self.link = os.path.join(self.root, "python3")
        with open(self.target, "w") as stream:
            stream.write("#!/bin/sh\n")
        os.chmod(self.target, 0o755)
        os.symlink("python-real", self.link)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_root_owned_safe_python_symlink_chain_allowed(self):
        resolved = health.validate_trusted_executable(
            self.link, expected_uid=os.getuid(), validate_parents=False)
        self.assertEqual(self.target, resolved)

    def test_python_symlink_writable_final_executable_rejected(self):
        os.chmod(self.target, 0o775)
        with self.assertRaises(health.MonitorError):
            health.validate_trusted_executable(
                self.link, expected_uid=os.getuid(), validate_parents=False)


class ConfigSecurityTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="cyf-health-config-")
        self.path = os.path.join(self.root, "config.json")
        self.valid = {"schema_version": 1, "web_marker": '<div id="app"></div>',
                      "email_enabled": True, "reminder_interval_seconds": 21600}

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, data, mode=0o600):
        with open(self.path, "w") as stream:
            json.dump(data, stream)
        os.chmod(self.path, mode)

    def test_valid_config(self):
        self.write(self.valid)
        self.assertEqual(self.valid, health.load_config(self.path, os.getuid(), False))

    def test_rejects_command_or_url_configuration(self):
        data = dict(self.valid)
        data["recovery_command"] = "/bin/true"
        self.write(data)
        with self.assertRaises(health.MonitorError):
            health.load_config(self.path, os.getuid(), False)

    def test_rejects_insecure_mode(self):
        self.write(self.valid, 0o644)
        with self.assertRaises(health.MonitorError):
            health.load_config(self.path, os.getuid(), False)

    def test_rejects_symlink(self):
        target = self.path + ".target"
        with open(target, "w") as stream:
            json.dump(self.valid, stream)
        os.chmod(target, 0o600)
        os.symlink(target, self.path)
        with self.assertRaises(health.MonitorError):
            health.load_config(self.path, os.getuid(), False)

    def test_rejects_duplicate_json_key(self):
        with open(self.path, "w") as stream:
            stream.write('{"schema_version":1,"schema_version":1,"web_marker":"x","email_enabled":true,"reminder_interval_seconds":21600}')
        os.chmod(self.path, 0o600)
        with self.assertRaises(health.MonitorError):
            health.load_config(self.path, os.getuid(), False)


class ProbeContractTests(unittest.TestCase):
    def canonical_output(self, health_value="UP", identity=True, listener=True, elapsed="25:01"):
        lines = ["STATUS=RUNNING", "PID=123",
                 "  PID  PPID                  STARTED     ELAPSED STAT %CPU %MEM   RSS CMD",
                 "  123     1 Sat Sep  5 12:00:00 2026       %s Sl    0.0  1.0 1 java" % elapsed,
                 "ARTIFACT_ATTESTATION=MATCH"]
        if listener:
            lines.append("PORT_10018=LISTENING_BY_PID")
        if identity:
            lines.append("RUNTIME_IDENTITY=" + health.EXPECTED_RUNTIME_IDENTITY)
        lines.append("HEALTH=" + health_value)
        return "\n".join(lines) + "\n"

    def test_canonical_parser_requires_full_up_identity(self):
        parsed = health.parse_canonical_status(0, self.canonical_output())
        self.assertTrue(parsed["healthy"])
        self.assertEqual(1501, parsed["elapsed_seconds"])
        incomplete = health.parse_canonical_status(0, self.canonical_output(identity=False))
        self.assertFalse(incomplete["healthy"])

    def test_canonical_rc4_no_listener_is_not_recovery_safe(self):
        parsed = health.parse_canonical_status(4, self.canonical_output("NOT_READY", identity=False, listener=False))
        self.assertFalse(parsed["recovery_safe"])
        self.assertEqual("not_ready_identity_incomplete", parsed["classification"])

    def test_canonical_status_waits_for_the_real_observation_outcome(self):
        effects = health.Effects()
        completed = {"returncode": 4, "classification": "completed",
                     "stdout": self.canonical_output("NOT_READY"), "stderr": ""}
        with mock.patch.object(effects, "_trusted_canonical", return_value=True), \
                mock.patch.object(effects, "_run", return_value=completed) as runner:
            result = effects.canonical_status()
        runner.assert_called_once_with([health.CANONICAL, "status"], None)
        self.assertEqual("not_ready_trusted", result["classification"])
        self.assertTrue(result["recovery_safe"])

    def test_canonical_status_timeout_result_remains_fail_closed(self):
        effects = health.Effects()
        timed_out = {"returncode": 124, "classification": "timeout",
                     "stdout": "", "stderr": ""}
        with mock.patch.object(effects, "_trusted_canonical", return_value=True), \
                mock.patch.object(effects, "_run", return_value=timed_out) as runner:
            result = effects.canonical_status()
        runner.assert_called_once_with([health.CANONICAL, "status"], None)
        self.assertEqual("canonical_status_timeout", result["classification"])
        self.assertEqual(124, result["returncode"])
        self.assertFalse(result["healthy"])
        self.assertFalse(result["recovery_safe"])

    def test_public_api_uses_waf_compatible_health_monitor_user_agent(self):
        effects = health.Effects()
        captured = []

        class Response(object):
            headers = {"Content-Type": "application/json"}

            def getcode(self):
                return 401

            def read(self, maximum):
                return b'{"code":"E401","msg":"authentication required","status":401}'

            def close(self):
                pass

        class Opener(object):
            def open(self, request, timeout):
                captured.append((request.get_header("User-agent"), timeout))
                return Response()

        with mock.patch.object(health.urlrequest, "build_opener", return_value=Opener()):
            result = effects.public_api()

        self.assertTrue(result["healthy"])
        self.assertEqual("auth_boundary_json_denial", result["classification"])
        self.assertEqual([( "cyf-juyiting-health/1.0", 8)], captured)

    def test_public_api_allows_exact_empty_401_boundary(self):
        effects = health.Effects()
        effects._http = lambda url: (401, "", b"", "completed")
        result = effects.public_api()
        self.assertTrue(result["healthy"])
        self.assertEqual("auth_boundary_empty_401", result["classification"])

    def test_public_api_rejects_html_403_502_and_spa_200(self):
        effects = health.Effects()
        for response in ((403, "text/html", b"nginx forbidden", "completed"),
                         (502, "text/html", b"bad gateway", "completed"),
                         (200, "text/html", b'<div id="app"></div>', "completed")):
            effects._http = lambda url, value=response: value
            self.assertFalse(effects.public_api()["healthy"])

    def test_public_api_accepts_json_auth_denial(self):
        effects = health.Effects()
        effects._http = lambda url: (403, "application/json", b'{"message":"Forbidden"}', "completed")
        self.assertTrue(effects.public_api()["healthy"])

    def test_web_requires_html_marker(self):
        effects = health.Effects()
        effects._http = lambda url: (200, "text/html", b'<div id="app"></div>', "completed")
        self.assertTrue(effects.web('<div id="app"></div>')["healthy"])
        effects._http = lambda url: (200, "application/json", b'<div id="app"></div>', "completed")
        self.assertFalse(effects.web('<div id="app"></div>')["healthy"])


class RecoveryCarrierHelperTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_fixed_own_cgroup_swappiness_write_and_readback(self):
        unit = carrier_module.scope_unit("I000056-1788792725", 2)
        root = os.path.join(self.tempdir, "memory")
        directory = os.path.join(root, "system.slice", unit)
        os.makedirs(directory)
        control = os.path.join(directory, "memory.swappiness")
        with open(control, "wb") as stream:
            stream.write(b"0\n")
        os.chmod(control, 0o644)
        proc_path = os.path.join(self.tempdir, "self.cgroup")
        with open(proc_path, "w") as stream:
            stream.write("4:memory:/system.slice/%s\n" % unit)

        carrier_module.configure_own_swappiness(unit, root, proc_path)

        with open(control, "rb") as stream:
            self.assertEqual(b"60", stream.read().strip())

    def test_foreign_cgroup_and_arbitrary_action_are_rejected(self):
        unit = carrier_module.scope_unit("I000056-1788792725", 2)
        root = os.path.join(self.tempdir, "memory")
        directory = os.path.join(root, "system.slice", unit)
        os.makedirs(directory)
        control = os.path.join(directory, "memory.swappiness")
        with open(control, "wb") as stream:
            stream.write(b"0\n")
        os.chmod(control, 0o644)
        proc_path = os.path.join(self.tempdir, "self.cgroup")
        with open(proc_path, "w") as stream:
            stream.write("4:memory:/system.slice/foreign.scope\n")
        with self.assertRaises(carrier_module.CarrierError):
            carrier_module.configure_own_swappiness(unit, root, proc_path)
        with self.assertRaises(carrier_module.CarrierError):
            carrier_module.run("stop", "I000056-1788792725", 2)

    def test_helper_fixed_environment_and_safe_marker_order(self):
        class Native(object):
            returncode = 1

            def wait(self):
                return self.returncode

        output = io.StringIO()
        with mock.patch.object(carrier_module, "configure_own_swappiness") as configure, \
                mock.patch.object(carrier_module, "validate_canonical") as validate, \
                mock.patch.object(carrier_module.subprocess, "Popen",
                                  return_value=Native()) as popen, \
                mock.patch.object(carrier_module.sys, "stdout", output):
            rc = carrier_module.run("start", "I000056-1788792725", 2)
        self.assertEqual(1, rc)
        configure.assert_called_once_with(
            "cyf-api-healthmon-i000056-1788792725-a2.scope")
        validate.assert_called_once_with()
        popen.assert_called_once_with(
            [carrier_module.CANONICAL, "start"],
            stdin=carrier_module.subprocess.DEVNULL,
            stdout=carrier_module.subprocess.DEVNULL,
            stderr=carrier_module.subprocess.DEVNULL, cwd="/",
            env=carrier_module.FIXED_RECOVERY_ENV, close_fds=True)
        self.assertEqual([carrier_module.MARKER_NATIVE_DISPATCH,
                          carrier_module.MARKER_NATIVE_INVOKED,
                          carrier_module.MARKER_NATIVE_RESULT + "1"],
                         output.getvalue().splitlines())
        self.assertEqual("0", carrier_module.FIXED_RECOVERY_ENV[
            "CYF_API_MIN_MEMORY_AVAILABLE_BYTES"])
        self.assertEqual("0", carrier_module.FIXED_RECOVERY_ENV[
            "CYF_API_MIN_DISK_AVAILABLE_BYTES"])

    def test_helper_preflight_failure_emits_no_dispatch_marker(self):
        output = io.StringIO()
        with mock.patch.object(
                carrier_module, "configure_own_swappiness",
                side_effect=carrier_module.CarrierError("preflight")), \
                mock.patch.object(carrier_module.subprocess, "Popen") as popen, \
                mock.patch.object(carrier_module.sys, "stdout", output):
            rc = carrier_module.main(["start", "I000056-1788792725", "2"])
        self.assertEqual(125, rc)
        popen.assert_not_called()
        self.assertEqual("", output.getvalue())


class StaticContractTests(unittest.TestCase):
    def test_fixed_recovery_and_mail_commands(self):
        with open(MODULE_PATH, "r") as stream:
            source = stream.read()
        self.assertIn('[CANONICAL, "status"]', source)
        self.assertIn('SYSTEMD_RUN, "--quiet", "--scope", "--slice=system.slice"', source)
        self.assertIn('MAIL_PYTHON, "-I", RECOVERY_CARRIER', source)
        self.assertNotIn("MemorySwappiness=60", source)
        self.assertNotIn("Type=oneshot", source)
        self.assertNotIn("KillMode=control-group", source)
        self.assertIn('[MAIL_PYTHON, "-I", MAIL_HELPER', source)
        self.assertIn("validate_trusted_executable(MAIL_PYTHON", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("/home/isp/bin", source)

        effects = health.Effects()
        with self.assertRaises(health.MonitorError):
            effects._run([health.MAIL_PYTHON, "-I", "/tmp/not-reviewed", "主题", "正文"],
                         1, mail=True)
        with self.assertRaises(health.MonitorError):
            effects._run([health.MAIL_PYTHON, "-I", health.MAIL_HELPER, "主题", "正文"], 1)
        with mock.patch.object(health, "validate_trusted_executable"), \
                mock.patch.object(health, "validate_regular"), \
                mock.patch.object(health, "sha256_file", return_value=health.MAIL_HELPER_SHA256), \
                mock.patch.object(effects, "_run", return_value={"returncode": 0}) as runner:
            self.assertEqual((True, "helper_accepted"), effects.send_email("主题", "正文"))
        runner.assert_called_once_with(
            [health.MAIL_PYTHON, "-I", health.MAIL_HELPER, "主题", "正文"],
            30, mail=True)

    def test_recovery_env_has_only_fixed_threshold_overrides_and_status_has_none(self):
        with mock.patch.dict(os.environ, {"CYF_SECRET_SHOULD_NOT_LEAK": "secret"}):
            status_env = health.command_environment(False)
            recovery_env = health.command_environment(True)
            mail_env = health.command_environment(mail=True)
        self.assertEqual(health.FIXED_ENV, status_env)
        self.assertNotIn("CYF_API_MIN_MEMORY_AVAILABLE_BYTES", status_env)
        self.assertNotIn("CYF_API_MIN_DISK_AVAILABLE_BYTES", status_env)
        self.assertEqual("0", recovery_env["CYF_API_MIN_MEMORY_AVAILABLE_BYTES"])
        self.assertEqual("0", recovery_env["CYF_API_MIN_DISK_AVAILABLE_BYTES"])
        self.assertEqual(set(health.FIXED_ENV) | set(health.RECOVERY_ENV_OVERRIDES),
                         set(recovery_env))
        self.assertNotIn("CYF_SECRET_SHOULD_NOT_LEAK", recovery_env)
        self.assertEqual("C.UTF-8", mail_env["LC_ALL"])
        self.assertEqual("C.UTF-8", mail_env["LANG"])
        self.assertEqual(set(health.FIXED_ENV), set(mail_env))
        self.assertNotIn("CYF_API_MIN_MEMORY_AVAILABLE_BYTES", mail_env)
        self.assertNotIn("CYF_API_MIN_DISK_AVAILABLE_BYTES", mail_env)
        self.assertNotIn("CYF_SECRET_SHOULD_NOT_LEAK", mail_env)
        self.assertEqual("C", status_env["LC_ALL"])
        self.assertEqual("C", recovery_env["LC_ALL"])
        with self.assertRaises(health.MonitorError):
            health.command_environment(recovery=True, mail=True)

        effects = health.Effects()
        incident_id = "I000056-1788792725"
        expected = [
            health.SYSTEMD_RUN, "--quiet", "--scope", "--slice=system.slice",
            "--unit=cyf-api-healthmon-i000056-1788792725-a2.scope",
            health.MAIL_PYTHON, "-I", health.RECOVERY_CARRIER,
            "start", incident_id, "2",
        ]
        with mock.patch.object(effects, "_trusted_canonical", return_value=True), \
                mock.patch.object(health, "validate_trusted_executable") as validator, \
                mock.patch.object(health, "validate_regular"), \
                mock.patch.object(health, "sha256_file",
                                  return_value=health.RECOVERY_CARRIER_SHA256), \
                mock.patch.object(effects, "_run", return_value={
                    "returncode": 0, "stdout": "CYF_HEALTHMON_CANONICAL=OK\n"}), \
                mock.patch.object(effects, "_run_recovery_carrier",
                                  return_value={
                                      "returncode": 1, "carrier_returncode": 1,
                                      "dispatch_confirmed": True,
                                      "native_invoked": True, "native_returncode": 1,
                                      "terminal_confirmed": True,
                                      "classification": "native_exit_1",
                                  }) as runner:
            result = effects.recover(
                "start", incident_id, 2, lambda: None, lambda: None)
        self.assertEqual("native_exit_1", result["classification"])
        self.assertEqual([mock.call(health.SYSTEMD_RUN, 0, True),
                          mock.call(health.MAIL_PYTHON, 0, True)],
                         validator.call_args_list)
        runner.assert_called_once_with(
            expected, "start", incident_id, 2, mock.ANY, mock.ANY)

    def test_recovery_scope_contract_rejects_arbitrary_inputs(self):
        incident_id = "I000056-1788792725"
        expected = health.recovery_carrier_argv("restart", incident_id, 3)
        self.assertEqual([
            health.SYSTEMD_RUN, "--quiet", "--scope", "--slice=system.slice",
            "--unit=cyf-api-healthmon-i000056-1788792725-a3.scope",
            health.MAIL_PYTHON, "-I", health.RECOVERY_CARRIER,
            "restart", incident_id, "3",
        ], expected)
        for action, incident, attempt in (
                ("stop", incident_id, 1),
                ("start", "../foreign.service", 1),
                ("start", incident_id, 0),
                ("start", incident_id, 4)):
            with self.subTest(action=action, incident=incident, attempt=attempt):
                with self.assertRaises(health.MonitorError):
                    health.recovery_carrier_argv(action, incident, attempt)

        effects = health.Effects()
        malicious = list(expected)
        malicious[3] = "--slice=foreign.slice"
        with self.assertRaises(health.MonitorError):
            effects._run_recovery_carrier(
                malicious, "restart", incident_id, 3,
                lambda: None, lambda: None)

    def test_carrier_protocol_distinguishes_launcher_failure_from_native_result(self):
        class Process(object):
            def __init__(self, output, returncode):
                self.stdout = io.StringIO(output)
                self.returncode = returncode

            def wait(self):
                return self.returncode

        effects = health.Effects()
        incident_id = "I000056-1788792725"
        argv = health.recovery_carrier_argv("start", incident_id, 2)
        callbacks = []
        with mock.patch.object(health.subprocess, "Popen",
                               side_effect=OSError("prelaunch")):
            prelaunch = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("unexpected-dispatch"),
                lambda: callbacks.append("unexpected-invoked"))
        self.assertFalse(prelaunch["dispatch_confirmed"])
        self.assertFalse(prelaunch["native_invoked"])
        self.assertTrue(prelaunch["terminal_confirmed"])
        self.assertEqual("carrier_prelaunch_failed", prelaunch["classification"])

        with mock.patch.object(health.subprocess, "Popen",
                               return_value=Process("", 1)):
            missing = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("dispatch"),
                lambda: callbacks.append("invoked"))
        self.assertIsNone(missing["dispatch_confirmed"])
        self.assertIsNone(missing["native_invoked"])
        self.assertIsNone(missing["native_returncode"])
        self.assertTrue(missing["terminal_confirmed"])
        self.assertEqual("carrier_output_missing_unknown", missing["classification"])
        self.assertEqual([], callbacks)

        with mock.patch.object(
                effects, "recovery_precondition",
                return_value={"permitted": False,
                              "classification": "known_preflight_failed"}):
            preflight = effects.recover(
                "start", incident_id, 2,
                lambda: callbacks.append("unexpected-dispatch"),
                lambda: callbacks.append("unexpected-invoked"))
        self.assertFalse(preflight["dispatch_confirmed"])
        self.assertFalse(preflight["native_invoked"])
        self.assertTrue(preflight["terminal_confirmed"])
        self.assertEqual("known_preflight_failed", preflight["classification"])

        output = ("CYF_HEALTHMON_NATIVE_DISPATCH=1\n"
                  "CYF_HEALTHMON_NATIVE_INVOKED=1\n"
                  "CYF_HEALTHMON_NATIVE_RESULT=1\n")
        with mock.patch.object(health.subprocess, "Popen",
                               return_value=Process(output, 1)):
            native = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("dispatch"),
                lambda: callbacks.append("invoked"))
        self.assertTrue(native["dispatch_confirmed"])
        self.assertTrue(native["native_invoked"])
        self.assertEqual(1, native["native_returncode"])
        self.assertEqual("native_exit_1", native["classification"])
        self.assertEqual(["dispatch", "invoked"], callbacks)

    def test_carrier_post_dispatch_missing_marker_and_stream_error_are_unknown(self):
        class StreamError(object):
            def __iter__(self):
                return self

            def __next__(self):
                raise OSError("synthetic stream failure")

            next = __next__

        class Process(object):
            def __init__(self, output, returncode=1):
                self.stdout = output
                self.returncode = returncode

            def wait(self):
                return self.returncode

        effects = health.Effects()
        incident_id = "I000056-1788792725"
        argv = health.recovery_carrier_argv("start", incident_id, 2)
        callbacks = []
        with mock.patch.object(
                health.subprocess, "Popen",
                return_value=Process(io.StringIO(
                    "CYF_HEALTHMON_NATIVE_DISPATCH=1\n"))):
            missing = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("dispatch"),
                lambda: callbacks.append("invoked"))
        self.assertTrue(missing["dispatch_confirmed"])
        self.assertIsNone(missing["native_invoked"])
        self.assertTrue(missing["terminal_confirmed"])
        self.assertEqual("native_result_unknown", missing["classification"])

        with mock.patch.object(
                health.subprocess, "Popen",
                return_value=Process(StreamError())):
            stream = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("unexpected-dispatch"),
                lambda: callbacks.append("unexpected-invoked"))
        self.assertIsNone(stream["dispatch_confirmed"])
        self.assertIsNone(stream["native_invoked"])
        self.assertTrue(stream["terminal_confirmed"])
        self.assertEqual("carrier_transport_unknown", stream["classification"])
        self.assertEqual(["dispatch"], callbacks)

        class WaitError(Process):
            def wait(self):
                raise OSError("synthetic wait failure")

        with mock.patch.object(
                health.subprocess, "Popen",
                return_value=WaitError(io.StringIO(
                    "CYF_HEALTHMON_NATIVE_DISPATCH=1\n"))):
            wait = effects._run_recovery_carrier(
                argv, "start", incident_id, 2,
                lambda: callbacks.append("wait-dispatch"),
                lambda: callbacks.append("unexpected-invoked"))
        self.assertTrue(wait["dispatch_confirmed"])
        self.assertIsNone(wait["native_invoked"])
        self.assertFalse(wait["terminal_confirmed"])
        self.assertIsNone(wait["carrier_returncode"])
        self.assertEqual("carrier_transport_unknown", wait["classification"])
        self.assertEqual(["dispatch", "wait-dispatch"], callbacks)

    def test_real_isolated_python36_flattens_all_bounded_subjects_without_folding(self):
        old_subject = "【聚义厅监控】“三次恢复失败即停止重试”策略已安装；持锁待查"
        subjects = [
            health.sanitize_mail_subject(old_subject),
            health.SUBJECT_DIGEST,
            health.SUBJECT_INCIDENT_CONFIRMED,
            health.SUBJECT_RESOLVED,
            health.SUBJECT_REMINDER,
            health.SUBJECT_RECOVERY_ATTEMPT % (1, 3),
            health.SUBJECT_RECOVERY_ATTEMPT % (3, 3),
            health.SUBJECT_RECOVERY_DEFERRED,
            health.SUBJECT_RECOVERY_RESULT % ("成功", 3, 3),
            health.SUBJECT_RECOVERY_RESULT % ("未成功", 3, 3),
            health.SUBJECT_RECOVERY_RESULT % ("未确认", 3, 3),
            health.SUBJECT_RECOVERY_EXHAUSTED,
            health.SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
            health.SUBJECT_NOTIFY_TEST,
        ]
        script = r"""from email import policy
from email.generator import BytesGenerator
from email.message import EmailMessage
from io import BytesIO
import json, sys
subjects=json.loads(sys.argv[1])
for subject in subjects:
    message=EmailMessage()
    message['From']='monitor@example.invalid'
    message['To']='ops@example.invalid'
    message['Subject']=subject
    message.set_content('中文正文：服务状态需继续排查。', charset='utf-8')
    output=BytesIO()
    BytesGenerator(output, policy=policy.SMTP).flatten(message, linesep='\r\n')
    headers=output.getvalue().split(b'\r\n\r\n',1)[0].split(b'\r\n')
    index=next(i for i,line in enumerate(headers) if line.startswith(b'Subject:'))
    assert index + 1 == len(headers) or not headers[index + 1].startswith((b' ',b'\t'))
print('MIME_SUBJECTS_OK:%d' % len(subjects))
"""
        process = subprocess.Popen(
            [health.MAIL_PYTHON, "-I", "-c", script,
             json.dumps(subjects, ensure_ascii=False)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd="/", env=health.command_environment(mail=True), universal_newlines=True)
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(0, process.returncode, stderr)
        self.assertEqual("MIME_SUBJECTS_OK:%d" % len(subjects), stdout.strip())
        self.assertLessEqual(len(subjects[0].encode("utf-8")),
                             health.MAIL_SUBJECT_MAX_BYTES)

    def test_cooldown_is_one_cron_interval_without_busy_loop(self):
        self.assertEqual(60, health.COOLDOWN_SECONDS)
        with open(os.path.join(HERE, "cyf-juyiting-health.cron"), "r") as stream:
            self.assertIn("* * * * * root", stream.read())

    def test_guard_logging_uses_fixed_sanitized_syslog_command(self):
        captured = []
        validated = []
        self.assertTrue(health.guard_log(
            "unsafe\npayload", validator=lambda *args: validated.append(args),
            executor=lambda argv: captured.append(argv)))
        self.assertEqual(health.LOGGER, validated[0][0])
        self.assertEqual([health.LOGGER, "-p", "daemon.err", "-t", "cyf-juyiting-health",
                          "fail_closed reason=unsafe_payload"], captured[0])

    def test_installer_trust_and_activation_contract(self):
        path = os.path.join(HERE, "install.sh")
        with open(path, "r") as stream:
            text = stream.read()
        self.assertIn("stat.S_ISLNK", text)
        self.assertIn("info.st_uid != 0 or info.st_gid != 0", text)
        self.assertIn("stat.S_IMODE(info.st_mode) & 0o022", text)
        self.assertIn("info.st_nlink != 1", text)
        self.assertIn("os.replace(temporary, target)", text)
        self.assertIn("os.fsync(directory_fd)", text)
        self.assertIn("install_monitor_atomically", text)
        monitor_digest = health.sha256_file(MODULE_PATH)
        carrier_digest = health.sha256_file(CARRIER_PATH)
        self.assertIn("CANDIDATE_MONITOR_SHA=" + monitor_digest, text)
        self.assertIn("CANDIDATE_CARRIER_SHA=" + carrier_digest, text)
        self.assertIn("installed monitor is not the reviewed candidate", text)
        self.assertIn("installed carrier is not the reviewed candidate", text)
        self.assertNotIn("CANONICAL_SHA=", text)
        self.assertIn("755:0:0:1", text)

    def test_cron_syntax_contract(self):
        path = os.path.join(HERE, "cyf-juyiting-health.cron")
        with open(path, "r") as stream:
            text = stream.read()
        command = "* * * * * root /usr/bin/python3 -I /usr/local/libexec/cyf-juyiting-health.py --check-once"
        self.assertIn(command, text)
        self.assertNotIn("systemd-run", text)
        self.assertNotIn("curl", text)
        with open(MODULE_PATH, "r") as stream:
            source = stream.read()
        self.assertEqual(2, source.count("guard_log(reason)"))


if __name__ == "__main__":
    unittest.main()
