#!/usr/bin/python3
"""Bounded, fail-closed Juyi Hall service health monitor (Python 3.6 stdlib)."""

import argparse
import copy
import datetime
import errno
import fcntl
import hashlib
import json
import os
import re
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import time
from urllib import error as urlerror
from urllib import request as urlrequest

SCHEMA_VERSION = 1
CONFIG_PATH = "/etc/cyf-juyiting-health.json"
STATE_DIR = "/home/isp/state/cyf-juyiting-health"
STATE_PATH = STATE_DIR + "/state.json"
LOCK_PATH = STATE_DIR + "/monitor.lock"
MAINTENANCE_PATH = STATE_DIR + "/maintenance"
CANONICAL = "/usr/local/sbin/cyf-api-kit"
SYSTEMD_RUN = "/usr/bin/systemd-run"
RECOVERY_CARRIER = "/usr/local/libexec/cyf-juyiting-recovery-carrier.py"
RECOVERY_CARRIER_SHA256 = "e907c33796a28dbf913bba1214e2691d84e3852bb9968809135ae80b4f14964f"
MAIL_PYTHON = "/usr/bin/python3"
MAIL_HELPER = "/root/.local/bin/cyf-task-email"
MAIL_HELPER_SHA256 = "ddc540f1d450880af5bb707751cf6cd68b6492e58cb702436b19580867d3ae99"
MAIL_ENV = "/root/.config/cyf-task-monitor/email.env"
LOGGER = "/usr/bin/logger"
WEB_URL = "https://kit.chaoyoufan.cn/juyiting"
API_URL = "https://api.chaoyoufan.cn/agent/map"
USER_AGENT = "cyf-juyiting-health/1.0"
EXPECTED_RUNTIME_IDENTITY = "cyf-api(987:1000)"
FAILURE_THRESHOLD = 3
HEALTHY_RESET_THRESHOLD = 3
MAX_RECOVERY_ATTEMPTS = 3
COOLDOWN_SECONDS = 60
STARTUP_GRACE_SECONDS = 25 * 60
MIN_MEMORY_BYTES = 1024 * 1024 * 1024
MIN_DISK_BYTES = 5 * 1024 * 1024 * 1024
MAX_STATE_BYTES = 128 * 1024
MAX_HTTP_BODY = 256 * 1024
MAX_OUTBOX = 24
MAX_PRIORITY_OUTBOX = 32
MAX_NOTICE_IDS = 64
MAIL_SUBJECT_MAX_BYTES = 40
SUBJECT_DIGEST = "【监控】待处理摘要"
SUBJECT_INCIDENT_CONFIRMED = "【监控】持续故障已确认"
SUBJECT_RESOLVED = "【监控】故障已恢复"
SUBJECT_REMINDER = "【监控】故障仍未解除"
SUBJECT_RECOVERY_ATTEMPT = "【监控】准备恢复（%d/%d）"
SUBJECT_RECOVERY_DEFERRED = "【监控】恢复已跳过"
SUBJECT_RECOVERY_RESULT = "【监控】恢复%s（%d/%d）"
SUBJECT_RECOVERY_EXHAUSTED = "【紧急】恢复失败（3/3）"
SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN = "【紧急】终态未知（3/3）"
SUBJECT_NOTIFY_TEST = "【监控】人工通知测试"
COMPONENTS = ("local_api", "web", "public_api", "mysql", "redis", "agent")
FIXED_ENV = {
    "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
    "HOME": "/root",
    "LC_ALL": "C",
    "LANG": "C",
    "USER": "root",
    "LOGNAME": "root",
}
RECOVERY_ENV_OVERRIDES = {
    "CYF_API_MIN_MEMORY_AVAILABLE_BYTES": "0",
    "CYF_API_MIN_DISK_AVAILABLE_BYTES": "0",
}
MAIL_ENV_OVERRIDES = {
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
}


def recovery_scope_unit(incident_id, attempt):
    if not isinstance(incident_id, str) \
            or not re.match(r"^I[0-9]{6,12}-[0-9]{1,20}$", incident_id):
        raise MonitorError("recovery_incident_invalid")
    if not _is_int(attempt, 1) or attempt > MAX_RECOVERY_ATTEMPTS:
        raise MonitorError("recovery_attempt_invalid")
    return "cyf-api-healthmon-%s-a%d.scope" % (incident_id.lower(), attempt)


def recovery_carrier_argv(action, incident_id, attempt):
    if action not in ("start", "restart"):
        raise MonitorError("recovery_action_invalid")
    return [
        SYSTEMD_RUN, "--quiet", "--scope", "--slice=system.slice",
        "--unit=" + recovery_scope_unit(incident_id, attempt),
        MAIL_PYTHON, "-I", RECOVERY_CARRIER, action, incident_id, str(attempt),
    ]


def command_environment(recovery=False, mail=False):
    if recovery and mail:
        raise MonitorError("command_environment_mode_invalid")
    env = dict(FIXED_ENV)
    if recovery:
        env.update(RECOVERY_ENV_OVERRIDES)
    if mail:
        env.update(MAIL_ENV_OVERRIDES)
    return env


class MonitorError(Exception):
    """A bounded, user-safe monitor failure."""


class BusyError(MonitorError):
    """Another monitor process holds the singleton lock."""


def utc_text(epoch):
    return datetime.datetime.utcfromtimestamp(int(epoch)).strftime("%Y-%m-%dT%H:%M:%SZ")


def asia_shanghai_text(epoch):
    local = datetime.datetime.utcfromtimestamp(int(epoch)) + datetime.timedelta(hours=8)
    return local.strftime("%Y-%m-%d %H:%M:%S Asia/Shanghai")


def safe_label(value, fallback="error"):
    text = str(value or fallback).lower()
    text = re.sub(r"[^a-z0-9_.:-]+", "_", text).strip("_")
    return (text or fallback)[:80]


def sanitize_mail_subject(value):
    text = re.sub(r"[\x00-\x20\x7f]+", " ", str(value or "")).strip()
    # Python 3.6's header folding can stall on long UTF-8 encoded words. Bound
    # the serialized input by bytes, without splitting a UTF-8 code point.
    encoded = text.encode("utf-8", "ignore")[:MAIL_SUBJECT_MAX_BYTES]
    return encoded.decode("utf-8", "ignore")


def sanitize_mail_body(value):
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(char for char in text if char in ("\n", "\t") or
                   (ord(char) >= 0x20 and ord(char) != 0x7f and
                    not 0x80 <= ord(char) <= 0x9f))
    return text[:2000]


def sanitize_notice_id(value):
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(value or "notice")).strip("_")
    return (text or "notice")[:128]


def json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MonitorError("duplicate_json_key")
        result[key] = value
    return result


def read_json_fd(fd, maximum):
    chunks = []
    total = 0
    while True:
        data = os.read(fd, min(65536, maximum + 1 - total))
        if not data:
            break
        chunks.append(data)
        total += len(data)
        if total > maximum:
            raise MonitorError("file_too_large")
    try:
        return json.loads(b"".join(chunks).decode("utf-8"), object_pairs_hook=json_no_duplicates)
    except MonitorError:
        raise
    except (UnicodeDecodeError, ValueError):
        raise MonitorError("invalid_json")


def validate_parent_chain(path, expected_uid=0):
    current = os.path.abspath(os.path.dirname(path))
    while True:
        try:
            info = os.lstat(current)
        except OSError:
            raise MonitorError("missing_parent")
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise MonitorError("unsafe_parent_type")
        if info.st_uid != expected_uid or stat.S_IMODE(info.st_mode) & 0o022:
            raise MonitorError("unsafe_parent_permissions")
        if current == "/":
            break
        current = os.path.dirname(current)


def validate_regular(path, expected_mode=None, expected_uid=0, maximum=None,
                     validate_parents=True, require_executable=False):
    if validate_parents:
        validate_parent_chain(path, expected_uid)
    try:
        info = os.lstat(path)
    except OSError:
        raise MonitorError("missing_file")
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise MonitorError("unsafe_file_type")
    if info.st_uid != expected_uid or info.st_nlink != 1:
        raise MonitorError("unsafe_file_identity")
    mode = stat.S_IMODE(info.st_mode)
    if expected_mode is not None and mode != expected_mode:
        raise MonitorError("unsafe_file_mode")
    if mode & 0o022:
        raise MonitorError("writable_trusted_file")
    if maximum is not None and info.st_size > maximum:
        raise MonitorError("file_too_large")
    if require_executable and not mode & 0o100:
        raise MonitorError("file_not_executable")
    return info


def validate_trusted_executable(path, expected_uid=0, validate_parents=True, maximum=128 * 1024 * 1024):
    current = os.path.abspath(path)
    visited = set()
    for _ in range(9):
        if current in visited:
            raise MonitorError("executable_symlink_cycle")
        visited.add(current)
        if validate_parents:
            validate_parent_chain(current, expected_uid)
        try:
            info = os.lstat(current)
        except OSError:
            raise MonitorError("missing_executable")
        if info.st_uid != expected_uid:
            raise MonitorError("unsafe_executable_owner")
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(current)
            current = os.path.normpath(target if os.path.isabs(target)
                                       else os.path.join(os.path.dirname(current), target))
            if not os.path.isabs(current):
                raise MonitorError("unsafe_executable_target")
            continue
        mode = stat.S_IMODE(info.st_mode)
        if not stat.S_ISREG(info.st_mode) or mode & 0o022 or not mode & 0o100 \
                or info.st_size > maximum:
            raise MonitorError("unsafe_executable_target")
        return current
    raise MonitorError("executable_symlink_depth")


def validate_directory(path, expected_mode=0o700, expected_uid=0, validate_parents=True):
    if validate_parents:
        validate_parent_chain(path, expected_uid)
    try:
        info = os.lstat(path)
    except OSError:
        raise MonitorError("missing_directory")
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise MonitorError("unsafe_directory_type")
    if info.st_uid != expected_uid or stat.S_IMODE(info.st_mode) != expected_mode:
        raise MonitorError("unsafe_directory_permissions")
    return info


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path=CONFIG_PATH, expected_uid=0, validate_parents=True):
    validate_regular(path, expected_mode=0o600, expected_uid=expected_uid,
                     maximum=8192, validate_parents=validate_parents)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError:
        raise MonitorError("config_open_failed")
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != expected_uid \
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            raise MonitorError("config_identity_changed")
        config = read_json_fd(fd, 8192)
    finally:
        os.close(fd)
    if not isinstance(config, dict):
        raise MonitorError("config_not_object")
    allowed = {"schema_version", "web_marker", "email_enabled", "reminder_interval_seconds"}
    if set(config) != allowed:
        raise MonitorError("config_keys_invalid")
    if config.get("schema_version") != SCHEMA_VERSION:
        raise MonitorError("config_schema_invalid")
    marker = config.get("web_marker")
    if not isinstance(marker, str) or not 1 <= len(marker) <= 128 \
            or any(ord(char) < 0x20 for char in marker):
        raise MonitorError("web_marker_invalid")
    if not isinstance(config.get("email_enabled"), bool):
        raise MonitorError("email_enabled_invalid")
    reminder = config.get("reminder_interval_seconds")
    if isinstance(reminder, bool) or not isinstance(reminder, int) \
            or reminder < 21600 or reminder > 604800:
        raise MonitorError("reminder_interval_invalid")
    return config


def initial_state(now):
    return {
        "schema_version": SCHEMA_VERSION,
        "initialized_at": int(now),
        "updated_at": int(now),
        "sequence": 0,
        "component_streaks": {name: 0 for name in COMPONENTS},
        "all_healthy_streak": 0,
        "api_healthy_streak": 0,
        "incident": None,
        "recovery": {
            "attempts": 0,
            "circuit_latched": False,
            "last_attempt_at": None,
            "in_flight": None,
            "last_result": None,
            "last_success_at": None,
        },
        "outbox": [],
        "notice_ids": [],
        "last_snapshot": None,
    }


def _is_int(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def validate_state(data):
    expected = {
        "schema_version", "initialized_at", "updated_at", "sequence",
        "component_streaks", "all_healthy_streak", "api_healthy_streak",
        "incident", "recovery", "outbox", "notice_ids", "last_snapshot",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise MonitorError("state_keys_invalid")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise MonitorError("state_schema_invalid")
    for key in ("initialized_at", "updated_at", "sequence", "all_healthy_streak", "api_healthy_streak"):
        if not _is_int(data.get(key)):
            raise MonitorError("state_counter_invalid")
    streaks = data.get("component_streaks")
    if not isinstance(streaks, dict) or set(streaks) != set(COMPONENTS):
        raise MonitorError("state_streaks_invalid")
    if any(not _is_int(value) for value in streaks.values()):
        raise MonitorError("state_streak_invalid")
    incident = data.get("incident")
    if incident is not None:
        if not isinstance(incident, dict) or set(incident) != {"id", "opened_at", "components", "last_reminder_slot"}:
            raise MonitorError("state_incident_invalid")
        if not isinstance(incident["id"], str) or len(incident["id"]) > 80 \
                or not _is_int(incident["opened_at"]) \
                or not isinstance(incident["components"], list) \
                or any(item not in COMPONENTS for item in incident["components"]) \
                or not _is_int(incident["last_reminder_slot"]):
            raise MonitorError("state_incident_fields_invalid")
    recovery = data.get("recovery")
    recovery_keys = {"attempts", "circuit_latched", "last_attempt_at", "in_flight",
                     "last_result", "last_success_at"}
    if not isinstance(recovery, dict) or set(recovery) != recovery_keys:
        raise MonitorError("state_recovery_invalid")
    if not _is_int(recovery["attempts"]) or recovery["attempts"] > MAX_RECOVERY_ATTEMPTS \
            or not isinstance(recovery["circuit_latched"], bool):
        raise MonitorError("state_recovery_fields_invalid")
    for key in ("last_attempt_at", "last_success_at"):
        if recovery[key] is not None and not _is_int(recovery[key]):
            raise MonitorError("state_recovery_time_invalid")
    if recovery["in_flight"] is not None:
        flight = recovery["in_flight"]
        flight_keys = {"action", "attempt", "at"}
        if not isinstance(flight, dict) or not flight_keys.issubset(set(flight)) \
                or set(flight) - (flight_keys | {"dispatch_at", "native_invoked_at"}) \
                or flight["action"] not in ("start", "restart") \
                or not _is_int(flight["attempt"], 1) \
                or flight["attempt"] > MAX_RECOVERY_ATTEMPTS or not _is_int(flight["at"]) \
                or ("dispatch_at" in flight and not _is_int(flight["dispatch_at"])) \
                or ("native_invoked_at" in flight \
                    and not _is_int(flight["native_invoked_at"])):
            raise MonitorError("state_in_flight_invalid")
    if recovery["last_result"] is not None:
        result = recovery["last_result"]
        result_keys = {"at", "action", "attempt", "classification"}
        optional_result_keys = {
            "dispatch_confirmed", "native_invoked", "native_returncode",
            "carrier_returncode", "terminal_confirmed",
        }
        if not isinstance(result, dict) or not result_keys.issubset(set(result)) \
                or set(result) - (result_keys | optional_result_keys) \
                or result["action"] not in ("start", "restart") \
                or not _is_int(result["at"]) or not _is_int(result["attempt"], 1) \
                or result["attempt"] > MAX_RECOVERY_ATTEMPTS \
                or not isinstance(result["classification"], str) or len(result["classification"]) > 80 \
                or ("dispatch_confirmed" in result \
                    and result["dispatch_confirmed"] is not None \
                    and not isinstance(result["dispatch_confirmed"], bool)) \
                or ("native_invoked" in result and result["native_invoked"] is not None \
                    and not isinstance(result["native_invoked"], bool)) \
                or ("native_returncode" in result and result["native_returncode"] is not None \
                    and (not isinstance(result["native_returncode"], int) \
                         or isinstance(result["native_returncode"], bool))) \
                or ("carrier_returncode" in result and result["carrier_returncode"] is not None \
                    and (not isinstance(result["carrier_returncode"], int) \
                         or isinstance(result["carrier_returncode"], bool))) \
                or ("terminal_confirmed" in result \
                    and not isinstance(result["terminal_confirmed"], bool)):
            raise MonitorError("state_recovery_result_invalid")
        if "dispatch_confirmed" in result \
                and result.get("native_invoked") is True \
                and result.get("dispatch_confirmed") is not True:
            raise MonitorError("state_recovery_result_order_invalid")
        if result.get("native_returncode") is not None \
                and result.get("native_invoked") is not True:
            raise MonitorError("state_recovery_result_native_invalid")
        if result.get("dispatch_confirmed") is False \
                and (result.get("native_invoked") is not False \
                     or result.get("terminal_confirmed") is not True):
            raise MonitorError("state_recovery_result_prelaunch_invalid")
        if result.get("terminal_confirmed") is False \
                and result.get("carrier_returncode") is not None:
            raise MonitorError("state_recovery_result_terminal_invalid")
    outbox = data.get("outbox")
    if not isinstance(outbox, list) or len(outbox) > MAX_PRIORITY_OUTBOX:
        raise MonitorError("state_outbox_invalid")
    notice_keys = {"id", "event", "subject", "body", "created_at", "attempts", "next_attempt_at", "last_error"}
    for item in outbox:
        if not isinstance(item, dict) or set(item) != notice_keys:
            raise MonitorError("state_notice_invalid")
        if any(not isinstance(item[key], str) or len(item[key]) > limit for key, limit in
               (("id", 128), ("event", 40), ("subject", 160), ("body", 2000), ("last_error", 80))):
            raise MonitorError("state_notice_text_invalid")
        if not _is_int(item["created_at"]) or not _is_int(item["attempts"]) \
                or not _is_int(item["next_attempt_at"]):
            raise MonitorError("state_notice_counter_invalid")
    ids = data.get("notice_ids")
    if not isinstance(ids, list) or len(ids) > MAX_NOTICE_IDS \
            or any(not isinstance(item, str) or len(item) > 128 for item in ids):
        raise MonitorError("state_notice_ids_invalid")
    snapshot = data["last_snapshot"]
    if snapshot is not None:
        if not isinstance(snapshot, dict) or set(snapshot) != {"at", "maintenance", "overall_healthy", "checks", "recovery"}:
            raise MonitorError("state_snapshot_invalid")
        if not _is_int(snapshot["at"]) or not isinstance(snapshot["maintenance"], bool) \
                or not isinstance(snapshot["overall_healthy"], bool):
            raise MonitorError("state_snapshot_fields_invalid")
        checks = snapshot["checks"]
        allowed_checks = set(COMPONENTS) | {
            "resource_observation", "maintenance_revalidation",
            "mysql_revalidation", "redis_revalidation",
            "local_api_revalidation", "local_api_post_recovery",
        }
        if not isinstance(checks, dict) or not set(COMPONENTS).issubset(set(checks)) \
                or not set(checks).issubset(allowed_checks):
            raise MonitorError("state_snapshot_checks_invalid")
        allowed_result = {"healthy", "classification", "http_status", "pid", "elapsed_seconds",
                          "returncode", "content_type", "observed_at"}
        for result in checks.values():
            if not isinstance(result, dict) or not {"healthy", "classification"}.issubset(set(result)) \
                    or not set(result).issubset(allowed_result) \
                    or not isinstance(result["healthy"], bool) \
                    or not isinstance(result["classification"], str) \
                    or len(result["classification"]) > 80:
                raise MonitorError("state_snapshot_result_invalid")
            for key in ("http_status", "pid", "elapsed_seconds", "returncode"):
                if key in result and (not isinstance(result[key], int) or isinstance(result[key], bool)):
                    raise MonitorError("state_snapshot_number_invalid")
            if "observed_at" in result and not _is_int(result["observed_at"]):
                raise MonitorError("state_snapshot_observed_at_invalid")
            if "content_type" in result and (not isinstance(result["content_type"], str)
                                             or len(result["content_type"]) > 80):
                raise MonitorError("state_snapshot_content_type_invalid")
        recovery_snapshot = snapshot["recovery"]
        # resource_preflight is retained for already-installed schema-v1 state.
        # New snapshots use resource_observation because capacity is warning-only.
        allowed_recovery = {"decision", "result", "resource_preflight", "resource_observation",
                            "native_result"}
        if not isinstance(recovery_snapshot, dict) or set(recovery_snapshot) - allowed_recovery \
                or not {"decision", "result"}.issubset(set(recovery_snapshot)) \
                or any(not isinstance(value, str) or len(value) > 80
                       for value in recovery_snapshot.values()):
            raise MonitorError("state_snapshot_recovery_invalid")
    return data


class StateStore(object):
    def __init__(self, state_dir=STATE_DIR, expected_uid=0, validate_parents=True):
        self.state_dir = state_dir
        self.state_path = os.path.join(state_dir, "state.json")
        self.lock_path = os.path.join(state_dir, "monitor.lock")
        self.maintenance_path = os.path.join(state_dir, "maintenance")
        self.expected_uid = expected_uid
        self.validate_parents = validate_parents
        self.lock_fd = None

    def prepare_init(self):
        if self.validate_parents:
            validate_parent_chain(self.state_dir, self.expected_uid)
        try:
            os.mkdir(self.state_dir, 0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise MonitorError("state_directory_create_failed")
        validate_directory(self.state_dir, 0o700, self.expected_uid, self.validate_parents)
        if os.path.lexists(self.lock_path):
            validate_regular(self.lock_path, 0o600, self.expected_uid, 4096, False)
        else:
            flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self.lock_path, flags, 0o600)
            try:
                os.fchmod(fd, 0o600)
            finally:
                os.close(fd)
            validate_regular(self.lock_path, 0o600, self.expected_uid, 4096, False)

    def acquire(self):
        validate_directory(self.state_dir, 0o700, self.expected_uid, self.validate_parents)
        validate_regular(self.lock_path, 0o600, self.expected_uid, 4096, False)
        flags = os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        self.lock_fd = os.open(self.lock_path, flags)
        info = os.fstat(self.lock_fd)
        path_info = os.lstat(self.lock_path)
        if (info.st_dev, info.st_ino) != (path_info.st_dev, path_info.st_ino) \
                or info.st_uid != self.expected_uid or info.st_nlink != 1 \
                or stat.S_IMODE(info.st_mode) != 0o600:
            self.release()
            raise MonitorError("lock_identity_changed")
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as exc:
            self.release()
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                raise BusyError("monitor_lock_busy")
            raise MonitorError("monitor_lock_failed")

    def release(self):
        if self.lock_fd is not None:
            try:
                os.close(self.lock_fd)
            finally:
                self.lock_fd = None

    def read(self):
        validate_regular(self.state_path, 0o600, self.expected_uid, MAX_STATE_BYTES, False)
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.state_path, flags)
        except OSError:
            raise MonitorError("state_open_failed")
        try:
            info = os.fstat(fd)
            if info.st_uid != self.expected_uid or info.st_nlink != 1 \
                    or stat.S_IMODE(info.st_mode) != 0o600 or not stat.S_ISREG(info.st_mode):
                raise MonitorError("state_identity_changed")
            data = read_json_fd(fd, MAX_STATE_BYTES)
        finally:
            os.close(fd)
        return validate_state(data)

    def write(self, data):
        validate_directory(self.state_dir, 0o700, self.expected_uid, self.validate_parents)
        validate_state(data)
        payload = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if len(payload) > MAX_STATE_BYTES:
            raise MonitorError("state_serialized_too_large")
        fd = None
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".state.", dir=self.state_dir)
            os.fchmod(fd, 0o600)
            if os.geteuid() == 0:
                os.fchown(fd, self.expected_uid, -1)
            written = 0
            while written < len(payload):
                written += os.write(fd, payload[written:])
            os.fsync(fd)
            os.close(fd)
            fd = None
            os.replace(temporary, self.state_path)
            temporary = None
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if fd is not None:
                os.close(fd)
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def maintenance(self):
        if not os.path.lexists(self.maintenance_path):
            return False
        validate_regular(self.maintenance_path, 0o600, self.expected_uid, 4096, False)
        return True

    def pause(self, now):
        if os.path.lexists(self.maintenance_path):
            validate_regular(self.maintenance_path, 0o600, self.expected_uid, 4096, False)
            return
        payload = ("maintenance paused at %s\n" % utc_text(now)).encode("ascii")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(self.maintenance_path, flags, 0o600)
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        directory_fd = os.open(self.state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def resume(self):
        if not os.path.lexists(self.maintenance_path):
            return
        validate_regular(self.maintenance_path, 0o600, self.expected_uid, 4096, False)
        os.unlink(self.maintenance_path)
        directory_fd = os.open(self.state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


class NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_elapsed(value):
    if not isinstance(value, str) or not re.match(r"^(?:\d+-)?\d{1,2}:\d{2}(?::\d{2})?$", value):
        return None
    days = 0
    rest = value
    if "-" in rest:
        day_text, rest = rest.split("-", 1)
        days = int(day_text)
    parts = [int(item) for item in rest.split(":")]
    if len(parts) == 2:
        hours, minutes, seconds = 0, parts[0], parts[1]
    else:
        hours, minutes, seconds = parts
    if minutes >= 60 or seconds >= 60:
        return None
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def parse_canonical_status(returncode, stdout):
    if not isinstance(stdout, str) or len(stdout) > 65536:
        return {"healthy": False, "classification": "canonical_output_invalid", "recovery_safe": False}
    fields = {}
    for line in stdout.splitlines():
        if re.match(r"^[A-Z0-9_]+=", line):
            key, value = line.split("=", 1)
            if key in fields or len(key) > 64 or len(value) > 256:
                return {"healthy": False, "classification": "canonical_output_invalid", "recovery_safe": False}
            fields[key] = value
    pid = fields.get("PID")
    pid_value = int(pid) if pid and pid.isdigit() and int(pid) > 1 else None
    elapsed = None
    if pid_value is not None:
        pattern = r"^\s*%d\s+\d+\s+\S+\s+\S+\s+\d+\s+\S+\s+\d{4}\s+(\S+)\s+" % pid_value
        for line in stdout.splitlines():
            match = re.match(pattern, line)
            if match:
                elapsed = parse_elapsed(match.group(1))
                break
    common = {
        "pid": pid_value,
        "elapsed_seconds": elapsed,
        "returncode": int(returncode),
        "recovery_safe": False,
    }
    if returncode == 0:
        trusted = fields.get("STATUS") == "RUNNING" \
            and fields.get("ARTIFACT_ATTESTATION") == "MATCH" \
            and fields.get("PORT_10018") == "LISTENING_BY_PID" \
            and fields.get("RUNTIME_IDENTITY") == EXPECTED_RUNTIME_IDENTITY \
            and fields.get("HEALTH") == "UP" and pid_value is not None
        common.update({"healthy": trusted,
                       "classification": "up" if trusted else "canonical_up_invalid"})
        return common
    if returncode == 3:
        stopped = fields.get("STATUS") == "STOPPED" and fields.get("PORT_10018") == "NOT_LISTENING"
        common.update({"healthy": False,
                       "classification": "stopped" if stopped else "stopped_transient_or_invalid",
                       "recovery_safe": stopped})
        return common
    if returncode == 4:
        trusted_not_ready = fields.get("STATUS") == "RUNNING" \
            and fields.get("ARTIFACT_ATTESTATION") == "MATCH" \
            and fields.get("PORT_10018") == "LISTENING_BY_PID" \
            and fields.get("RUNTIME_IDENTITY") == EXPECTED_RUNTIME_IDENTITY \
            and fields.get("HEALTH") == "NOT_READY" \
            and pid_value is not None and elapsed is not None
        common.update({"healthy": False,
                       "classification": "not_ready_trusted" if trusted_not_ready else "not_ready_identity_incomplete",
                       "recovery_safe": trusted_not_ready})
        return common
    if returncode == 1:
        common.update({"healthy": False, "classification": "canonical_busy_or_error"})
        return common
    if returncode == 5:
        common.update({"healthy": False, "classification": "canonical_unsafe_identity_or_listener"})
        return common
    common.update({"healthy": False, "classification": "canonical_returncode_unknown"})
    return common


class Effects(object):
    def _run(self, argv, timeout, mail=False):
        mail_prefix = [MAIL_PYTHON, "-I", MAIL_HELPER]
        is_mail_command = len(argv) >= len(mail_prefix) \
            and argv[:len(mail_prefix)] == mail_prefix
        if mail:
            if len(argv) != 5 or not is_mail_command \
                    or argv[3] != sanitize_mail_subject(argv[3]) \
                    or argv[4] != sanitize_mail_body(argv[4]):
                raise MonitorError("mail_env_command_invalid")
        elif is_mail_command:
            raise MonitorError("mail_command_without_mail_env")
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, cwd="/",
                                   env=command_environment(mail=mail),
                                   universal_newlines=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            return {"returncode": 124, "classification": "timeout", "stdout": "", "stderr": ""}
        return {"returncode": process.returncode, "classification": "completed",
                "stdout": stdout[:65537], "stderr": stderr[:4097]}

    def _trusted_canonical(self):
        try:
            validate_regular(CANONICAL, 0o755, 0, 1024 * 1024, True, True)
            # Root ownership, non-symlink, single-link and non-writable metadata are
            # the executable identity contract.  Do not turn a stale point-in-time
            # content pin into a synthetic outage or cancel a healthy status probe.
            return True
        except (MonitorError, OSError):
            return False

    def canonical_status(self):
        if not self._trusted_canonical():
            return {"healthy": False, "classification": "canonical_file_untrusted",
                    "recovery_safe": False, "returncode": None, "pid": None,
                    "elapsed_seconds": None}
        # Status is observational: wait for its real outcome rather than killing it
        # at an unmeasured performance deadline.
        result = self._run([CANONICAL, "status"], None)
        if result["classification"] == "timeout":
            return {"healthy": False, "classification": "canonical_status_timeout",
                    "recovery_safe": False, "returncode": 124, "pid": None,
                    "elapsed_seconds": None}
        return parse_canonical_status(result["returncode"], result["stdout"])

    def recovery_precondition(self, action, incident_id, attempt):
        try:
            recovery_carrier_argv(action, incident_id, attempt)
            if not self._trusted_canonical():
                return {"permitted": False, "classification": "canonical_file_untrusted"}
            validate_trusted_executable(SYSTEMD_RUN, 0, True)
            validate_trusted_executable(MAIL_PYTHON, 0, True)
            validate_regular(RECOVERY_CARRIER, 0o755, 0, 1024 * 1024, True, True)
            if sha256_file(RECOVERY_CARRIER) != RECOVERY_CARRIER_SHA256:
                return {"permitted": False,
                        "classification": "recovery_carrier_hash_mismatch"}
            checked = self._run([MAIL_PYTHON, "-I", RECOVERY_CARRIER, "--check"], None)
            if checked["returncode"] != 0:
                match = re.fullmatch(
                    r"CYF_HEALTHMON_CHECK_ERROR=(canonical_hash_mismatch|"
                    r"canonical_identity_invalid|canonical_unavailable)\n?",
                    checked.get("stderr", ""))
                reason = match.group(1) if match else "canonical_preflight_failed"
                return {"permitted": False, "classification": reason}
            if checked.get("stdout", "").strip() != "CYF_HEALTHMON_CANONICAL=OK":
                return {"permitted": False, "classification": "canonical_preflight_invalid"}
            return {"permitted": True,
                    "classification": "recovery_carrier_files_ready"}
        except (MonitorError, OSError) as exc:
            return {"permitted": False,
                    "classification": "recovery_carrier_%s" % safe_label(str(exc))}

    @staticmethod
    def _carrier_result(classification, carrier_returncode=None,
                        dispatch_confirmed=None, native_invoked=None,
                        native_returncode=None, terminal_confirmed=False):
        return {
            "returncode": native_returncode if native_returncode is not None else 126,
            "carrier_returncode": carrier_returncode,
            "dispatch_confirmed": dispatch_confirmed,
            "native_invoked": native_invoked,
            "native_returncode": native_returncode,
            "terminal_confirmed": terminal_confirmed,
            "classification": classification,
        }

    def _run_recovery_carrier(self, argv, action, incident_id, attempt,
                              dispatch_callback, native_invoked_callback):
        expected = recovery_carrier_argv(action, incident_id, attempt)
        if argv != expected:
            raise MonitorError("recovery_env_command_invalid")
        try:
            process = subprocess.Popen(
                argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, cwd="/", env=command_environment(recovery=True),
                universal_newlines=True)
        except (OSError, subprocess.SubprocessError):
            return self._carrier_result(
                "carrier_prelaunch_failed", carrier_returncode=126,
                dispatch_confirmed=False, native_invoked=False,
                terminal_confirmed=True)
        dispatch_confirmed = False
        native_invoked = False
        native_returncode = None
        protocol_invalid = False
        dispatch_persist_failed = False
        invocation_persist_failed = False

        def record_dispatch():
            nonlocal dispatch_confirmed, dispatch_persist_failed
            if dispatch_confirmed:
                return
            dispatch_confirmed = True
            try:
                dispatch_callback()
            except Exception:
                dispatch_persist_failed = True

        def record_invocation():
            nonlocal native_invoked, invocation_persist_failed
            record_dispatch()
            if native_invoked:
                return
            native_invoked = True
            try:
                native_invoked_callback()
            except Exception:
                invocation_persist_failed = True

        stream_failed = False
        try:
            for line in process.stdout:
                marker = line.rstrip("\n")
                if marker == "CYF_HEALTHMON_NATIVE_DISPATCH=1":
                    if dispatch_confirmed or native_invoked or native_returncode is not None:
                        protocol_invalid = True
                        continue
                    record_dispatch()
                elif marker == "CYF_HEALTHMON_NATIVE_INVOKED=1":
                    if native_invoked or native_returncode is not None:
                        protocol_invalid = True
                        continue
                    if not dispatch_confirmed:
                        protocol_invalid = True
                    record_invocation()
                elif re.match(r"^CYF_HEALTHMON_NATIVE_RESULT=-?[0-9]+$", marker):
                    if not native_invoked or native_returncode is not None:
                        protocol_invalid = True
                        record_invocation()
                    native_returncode = int(marker.split("=", 1)[1])
                elif marker:
                    protocol_invalid = True
        except (OSError, ValueError, UnicodeError):
            stream_failed = True
        try:
            carrier_returncode = int(process.wait())
            terminal_confirmed = True
        except (OSError, ValueError, subprocess.SubprocessError):
            carrier_returncode = None
            terminal_confirmed = False
        if stream_failed or not terminal_confirmed:
            return self._carrier_result(
                "carrier_transport_unknown", carrier_returncode=carrier_returncode,
                dispatch_confirmed=True if dispatch_confirmed else None,
                native_invoked=True if native_invoked else None,
                native_returncode=None, terminal_confirmed=terminal_confirmed)
        if protocol_invalid:
            return self._carrier_result(
                "carrier_protocol_unknown", carrier_returncode=carrier_returncode,
                dispatch_confirmed=True if dispatch_confirmed else None,
                native_invoked=True if native_invoked else None,
                native_returncode=None, terminal_confirmed=True)
        if not dispatch_confirmed:
            return self._carrier_result(
                "carrier_output_missing_unknown",
                carrier_returncode=carrier_returncode,
                dispatch_confirmed=None, native_invoked=None,
                terminal_confirmed=True)
        if not native_invoked or native_returncode is None:
            return self._carrier_result(
                "native_result_unknown", carrier_returncode=carrier_returncode,
                dispatch_confirmed=True, native_invoked=None,
                terminal_confirmed=True)
        classification = "native_exit_%d" % native_returncode
        if dispatch_persist_failed or invocation_persist_failed:
            classification += "_fence_persist_deferred"
        return self._carrier_result(
            classification, carrier_returncode=carrier_returncode,
            dispatch_confirmed=True, native_invoked=True,
            native_returncode=native_returncode, terminal_confirmed=True)

    def recover(self, action, incident_id, attempt, dispatch_callback,
                native_invoked_callback):
        precondition = self.recovery_precondition(action, incident_id, attempt)
        if not precondition.get("permitted"):
            return {
                "returncode": 126, "carrier_returncode": 126,
                "dispatch_confirmed": False, "native_invoked": False,
                "native_returncode": None, "terminal_confirmed": True,
                "classification": safe_label(precondition.get("classification")),
            }
        argv = recovery_carrier_argv(action, incident_id, attempt)
        try:
            return self._run_recovery_carrier(
                argv, action, incident_id, attempt,
                dispatch_callback, native_invoked_callback)
        except Exception as exc:
            return {
                "returncode": 126, "carrier_returncode": None,
                "dispatch_confirmed": None, "native_invoked": None,
                "native_returncode": None, "terminal_confirmed": False,
                "classification": "carrier_transport_%s" %
                safe_label(type(exc).__name__),
            }

    def _http(self, url):
        req = urlrequest.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json",
            "Accept-Encoding": "identity",
            "Cache-Control": "no-cache",
        })
        opener = urlrequest.build_opener(NoRedirect(), urlrequest.HTTPSHandler(context=ssl.create_default_context()))
        try:
            response = opener.open(req, timeout=8)
        except urlerror.HTTPError as exc:
            response = exc
        try:
            status_code = int(response.getcode())
            content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            body = response.read(MAX_HTTP_BODY + 1)
            if len(body) > MAX_HTTP_BODY:
                return status_code, content_type, None, "body_too_large"
            return status_code, content_type, body, "completed"
        finally:
            response.close()

    def web(self, marker):
        try:
            status_code, content_type, body, classification = self._http(WEB_URL)
            healthy = classification == "completed" and status_code == 200 \
                and content_type == "text/html" and marker.encode("utf-8") in body
            return {"healthy": healthy, "classification": "web_ok" if healthy else "web_invalid",
                    "http_status": status_code, "content_type": content_type[:80]}
        except Exception as exc:
            return {"healthy": False, "classification": "web_%s" % safe_label(type(exc).__name__)}

    def public_api(self):
        try:
            status_code, content_type, body, classification = self._http(API_URL)
            valid_empty_401 = classification == "completed" and status_code == 401 \
                and content_type == "" and body == b""
            valid_json_denial = False
            if classification == "completed" and status_code in (401, 403) \
                    and content_type in ("application/json", "application/problem+json"):
                try:
                    payload = json.loads(body.decode("utf-8"), object_pairs_hook=json_no_duplicates)
                except (UnicodeDecodeError, ValueError, MonitorError):
                    payload = None
                if isinstance(payload, dict):
                    values = []
                    for key in ("code", "status", "error", "message", "msg", "detail"):
                        if key in payload and isinstance(payload[key], (str, int)) and not isinstance(payload[key], bool):
                            values.append(str(payload[key]).lower())
                    joined = " ".join(values)
                    markers = ("401", "403", "unauthorized", "forbidden", "authentication",
                               "access denied", "未认证", "未授权", "登录", "token")
                    valid_json_denial = any(marker in joined for marker in markers)
            valid = valid_empty_401 or valid_json_denial
            classification_label = "auth_boundary_empty_401" if valid_empty_401 else \
                ("auth_boundary_json_denial" if valid_json_denial else "auth_boundary_invalid")
            return {"healthy": valid,
                    "classification": classification_label,
                    "http_status": status_code, "content_type": content_type[:80]}
        except Exception as exc:
            return {"healthy": False, "classification": "public_api_%s" % safe_label(type(exc).__name__)}

    def mysql(self):
        try:
            sock = socket.create_connection(("127.0.0.1", 3306), timeout=3)
            try:
                sock.settimeout(3)
                data = sock.recv(64)
            finally:
                sock.close()
            healthy = bool(data)
            return {"healthy": healthy, "classification": "mysql_reachable" if healthy else "mysql_no_handshake"}
        except Exception as exc:
            return {"healthy": False, "classification": "mysql_%s" % safe_label(type(exc).__name__)}

    def redis(self):
        try:
            sock = socket.create_connection(("127.0.0.1", 6379), timeout=3)
            try:
                sock.settimeout(3)
                sock.sendall(b"PING\r\n")
                data = sock.recv(128)
            finally:
                sock.close()
            healthy = data.startswith((b"+PONG", b"-NOAUTH", b"-NOPERM"))
            return {"healthy": healthy,
                    "classification": "redis_reachable" if healthy else "redis_unexpected_reply"}
        except Exception as exc:
            return {"healthy": False, "classification": "redis_%s" % safe_label(type(exc).__name__)}

    def agent(self):
        try:
            result = self._run(["/usr/bin/systemctl", "is-active", "cyf-agent-runtime-v1@unified.service"], 5)
            active = result["returncode"] == 0 and result["stdout"].strip() == "active"
            return {"healthy": active, "classification": "agent_active" if active else "agent_inactive"}
        except Exception as exc:
            return {"healthy": False, "classification": "agent_%s" % safe_label(type(exc).__name__)}

    def resources(self):
        try:
            available = None
            with open("/proc/meminfo", "r") as stream:
                for line in stream:
                    if line.startswith("MemAvailable:"):
                        available = int(line.split()[1]) * 1024
                        break
            disk = os.statvfs("/home/isp/hosts/cyf/api").f_bavail * os.statvfs("/home/isp/hosts/cyf/api").f_frsize
            healthy = available is not None and available >= MIN_MEMORY_BYTES and disk >= MIN_DISK_BYTES
            return {"healthy": healthy,
                    "classification": "resources_ok" if healthy else "resources_below_canonical_minimum"}
        except Exception as exc:
            return {"healthy": False, "classification": "resources_%s" % safe_label(type(exc).__name__)}

    def send_email(self, subject, body):
        try:
            validate_trusted_executable(MAIL_PYTHON, 0, True)
            validate_regular(MAIL_HELPER, 0o700, 0, 1024 * 1024, True, False)
            validate_regular(MAIL_ENV, 0o600, 0, 8192, True, False)
            if sha256_file(MAIL_HELPER) != MAIL_HELPER_SHA256:
                return False, "mail_helper_hash_mismatch"
            result = self._run([MAIL_PYTHON, "-I", MAIL_HELPER,
                                sanitize_mail_subject(subject), sanitize_mail_body(body)],
                               30, mail=True)
            if result["returncode"] == 0:
                return True, "helper_accepted"
            # Preserve only the SMTP status, never the traceback, address or
            # provider text. The former generic label concealed broken auth.
            match = re.search(r"SMTPAuthenticationError: \(([0-9]{3}),", result.get("stderr", ""))
            classification = "smtp_authentication_failed_%s" % match.group(1) if match else "helper_failed"
            guard_log(classification)
            return False, classification
        except Exception as exc:
            return False, "mail_%s" % safe_label(type(exc).__name__)


def _guard_logger_exec(argv):
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, cwd="/", env=dict(FIXED_ENV))
    try:
        return process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return 124


def guard_log(reason, validator=None, executor=None):
    validate = validator or validate_trusted_executable
    execute = executor or _guard_logger_exec
    try:
        validate(LOGGER, 0, True)
        execute([LOGGER, "-p", "daemon.err", "-t", "cyf-juyiting-health",
                 "fail_closed reason=%s" % safe_label(reason)])
        return True
    except Exception:
        return False


def sanitized_result(result, observed_at=None):
    clean = {
        "healthy": bool(result.get("healthy")),
        "classification": safe_label(result.get("classification")),
    }
    for key in ("http_status", "pid", "elapsed_seconds", "returncode"):
        value = result.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            clean[key] = value
    if isinstance(result.get("content_type"), str):
        clean["content_type"] = safe_label(result["content_type"], "unknown")
    if _is_int(observed_at):
        clean["observed_at"] = int(observed_at)
    return clean


COMPONENT_NAMES_ZH = {
    "local_api": "本机 API",
    "web": "聚义厅网页",
    "public_api": "公网 API 鉴权边界",
    "mysql": "MySQL",
    "redis": "Redis",
    "agent": "Agent 服务",
}
ACTION_NAMES_ZH = {"start": "启动", "restart": "重启"}


def component_text_zh(components):
    return "、".join(COMPONENT_NAMES_ZH.get(item, safe_label(item))
                    for item in sorted(components)) if components else "无"


def notice_body(event, now, incident_id, components, extra=""):
    component_text = component_text_zh(components)
    content = {
        "incident_confirmed": (
            "检测到持续故障，请尽快确认服务影响。",
            "建议：先核对本机 API 规范状态和依赖可达性；不要绕过身份、锁或制品校验。"),
        "resolved_after_three_healthy_checks": (
            "连续三次检查均正常，本次故障已自动标记为恢复。",
            "建议：无需操作；如用户仍受影响，请按新的故障单独排查。"),
        "restrained_reminder": (
            "故障仍未解除，请继续跟进。",
            "建议：查看最近一次受控状态摘要；不要依据本邮件执行盲目重启。"),
        "recovery_attempt_selected": (
            "已选择一次受控 API 恢复，执行前仍会重新校验身份和状态。",
            "建议：如正在人工恢复，请保持维护模式，避免与自动恢复并发。"),
        "recovery_deferred_revalidation": (
            "恢复执行前的重新校验未通过，本次没有调用生命周期命令。",
            "建议：确认当前 PID、监听归属和规范状态后再处理。"),
        "recovery_result": (
            "一次受控 API 恢复已结束，请根据恢复后健康结果决定后续动作。",
            "建议：仅在规范健康明确为 UP 时视为恢复成功。"),
        "recovery_unknown": (
            "一次受控 API 恢复的调度或终态未能确认，已保留本次预算与执行围栏。",
            "建议：先核对规范健康和受控收据；不要并发启动第二个恢复执行。"),
        "explicit_notify_test": (
            "这是聚义厅健康监控的人工通知测试。",
            "建议：无需处理生产服务；仅确认通知链路配置。"),
    }
    summary, action = content.get(event, (
        "聚义厅健康监控产生了一条受控通知。",
        "建议：按事件编号核对状态，不要依据邮件执行未授权操作。"))
    lines = [summary, action]
    if extra:
        lines.append(sanitize_mail_body(extra)[:700])
    lines.extend([
        "",
        "时间（Asia/Shanghai）：%s" % asia_shanghai_text(now),
        "事件：%s" % safe_label(event),
        "故障编号：%s" % (incident_id or "无"),
        "涉及组件：%s" % component_text,
        "邮件状态说明：本机邮件助手接受请求不代表收件箱已送达。",
    ])
    return sanitize_mail_body("\n".join(lines))


def recovery_exhausted_body(now, incident_id, action, attempt, command_result,
                            initial_status, fresh_status, results, resource_observation):
    return sanitize_mail_body("\n".join([
        "恢复失败，已停止自动重试（3/3）。",
        "服务影响：聚义厅 API 尚未确认恢复，相关页面和接口请求可能失败。",
        "下一步：请人工核对受控生命周期收据与服务健康；查明原因后，按审批流程同步次数并解除熔断。",
        "已确认：初始规范状态=%s；MySQL=%s；Redis=%s；资源观测=%s。" % (
            safe_label(initial_status.get("classification")),
            safe_label(results["mysql"].get("classification")),
            safe_label(results["redis"].get("classification")),
            safe_label(resource_observation)),
        "未知原因：监控未读取或转发原始日志，具体失败根因仍未知。",
        "本次结果：尝试=%d/%d；动作=%s；返回码=%d；恢复后健康=%s（%s）。" % (
            attempt, MAX_RECOVERY_ATTEMPTS, ACTION_NAMES_ZH.get(action, "未知"),
            command_result.get("returncode"),
            "UP" if fresh_status.get("healthy") else "未确认",
            safe_label(fresh_status.get("classification"))),
        "资源说明：仅恢复命令固定传入 CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0 和 "
        "CYF_API_MIN_DISK_AVAILABLE_BYTES=0；资源观测只告警、不阻止恢复，status 不带这些覆盖。",
        "",
        "时间（Asia/Shanghai）：%s" % asia_shanghai_text(now),
        "故障编号：%s" % (incident_id or "无"),
        "事件：recovery_exhausted",
        "邮件状态说明：本机邮件助手接受请求不代表收件箱已送达。",
    ]))


def interrupted_recovery_exhausted_body(now, incident_id, flight, current_status, results):
    current_health = "UP" if current_status.get("healthy") else "未确认"
    return sanitize_mail_body("\n".join([
        "第3次恢复没有可信终态，结果为 UNKNOWN；已停止自动重试（3/3）。",
        "服务影响：当前聚义厅 API 健康=%s（%s）；在人工确认前不得启动第4次自动恢复。" % (
            current_health, safe_label(current_status.get("classification"))),
        "下一步：请人工核对受控生命周期收据和当前规范健康；确认结果后按审批流程处理熔断。",
        "已确认：尝试=%d/%d；动作=%s；开始时间=%s；MySQL=%s；Redis=%s。" % (
            flight["attempt"], MAX_RECOVERY_ATTEMPTS,
            ACTION_NAMES_ZH.get(flight["action"], "未知"),
            asia_shanghai_text(flight["at"]),
            safe_label(results["mysql"].get("classification")),
            safe_label(results["redis"].get("classification"))),
        "未知终态：监控中断后没有可信返回码或紧邻调用完成时的健康结果；"
        "本通知不把中断推断为已确认命令失败或成功。",
        "资源说明：恢复命令仅允许固定传入 CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0 和 "
        "CYF_API_MIN_DISK_AVAILABLE_BYTES=0；本次收口未重新执行生命周期命令。",
        "",
        "检测时间（Asia/Shanghai）：%s" % asia_shanghai_text(now),
        "故障编号：%s" % (incident_id or "无"),
        "事件：recovery_exhausted_unknown",
        "邮件状态说明：本机邮件助手接受请求不代表收件箱已送达。",
    ]))


def uncertain_recovery_exhausted_body(now, incident_id, action, attempt,
                                      command_result, current_status, results):
    return sanitize_mail_body("\n".join([
        "第3次恢复的调度或返回终态不完整，结果为 UNKNOWN；已停止自动重试（3/3）。",
        "服务影响：当前聚义厅 API 健康=%s（%s）；在人工确认前不得启动第4次自动恢复。" % (
            "UP" if current_status.get("healthy") else "未确认",
            safe_label(current_status.get("classification"))),
        "下一步：请人工核对受控 carrier、规范生命周期收据和当前健康，再按审批流程处理熔断。",
        "已确认：尝试=%d/%d；动作=%s；调度围栏=%s；carrier终态=%s；MySQL=%s；Redis=%s。" % (
            attempt, MAX_RECOVERY_ATTEMPTS, ACTION_NAMES_ZH.get(action, "未知"),
            "已确认" if command_result.get("dispatch_confirmed") is True else "未知",
            "已确认" if command_result.get("terminal_confirmed") is True else "未知",
            safe_label(results["mysql"].get("classification")),
            safe_label(results["redis"].get("classification"))),
        "未知终态：未取得可信规范返回码；本通知不推断命令失败或成功。",
        "资源说明：恢复命令仅允许固定传入 CYF_API_MIN_MEMORY_AVAILABLE_BYTES=0 和 "
        "CYF_API_MIN_DISK_AVAILABLE_BYTES=0；资源观测只告警、不阻止恢复。",
        "",
        "检测时间（Asia/Shanghai）：%s" % asia_shanghai_text(now),
        "故障编号：%s" % (incident_id or "无"),
        "事件：recovery_exhausted_unknown",
        "邮件状态说明：本机邮件助手接受请求不代表收件箱已送达。",
    ]))


def _coalesced_notice_count(item):
    if item.get("event") != "digest":
        return 1
    match = re.search(r"coalesced_count=(\d+)", item.get("body", ""))
    return int(match.group(1)) if match else 1


def _remember_notice_id(state, stored_id):
    state["notice_ids"].append(stored_id)
    state["notice_ids"] = state["notice_ids"][-MAX_NOTICE_IDS:]


def enqueue_notice(state, notice_id, event, subject, body, now):
    stored_id = sanitize_notice_id(notice_id)
    if notice_id in state["notice_ids"] or stored_id in state["notice_ids"]:
        return False
    item = {
        "id": stored_id, "event": safe_label(event)[:40],
        "subject": sanitize_mail_subject(subject), "body": sanitize_mail_body(body),
        "created_at": int(now), "attempts": 0,
        "next_attempt_at": int(now), "last_error": "",
    }
    if len(state["outbox"]) >= MAX_OUTBOX and event in ("recovery_attempted", "recovery_exhausted"):
        digest = next((pending for pending in state["outbox"]
                       if pending["event"] == "digest"), None)
        if digest is None:
            victim_indices = [index for index, pending in enumerate(state["outbox"])
                              if pending["event"] != "recovery_exhausted"][:2]
            if len(victim_indices) < 2:
                if not victim_indices:
                    if len(state["outbox"]) < MAX_PRIORITY_OUTBOX:
                        state["outbox"].append(item)
                        _remember_notice_id(state, stored_id)
                        return True
                    return False
                # Preserve every exhausted alert. If only one lower-priority item
                # exists, discard that item rather than manufacturing room by
                # evicting a critical alert merely to add a digest.
                state["outbox"].pop(victim_indices[0])
                state["outbox"].append(item)
                _remember_notice_id(state, stored_id)
                return True
            replaced = [state["outbox"][index] for index in victim_indices]
            for index in reversed(victim_indices):
                state["outbox"].pop(index)
            count = sum(_coalesced_notice_count(pending) for pending in replaced)
            digest = {
                "id": "outbox-digest", "event": "digest",
                "subject": SUBJECT_DIGEST,
                "body": "较早通知已合并，请优先处理当前恢复事件。\n\n"
                        "时间（Asia/Shanghai）：%s\ncoalesced_count=%d\n最新事件=%s" %
                        (asia_shanghai_text(now), count, replaced[-1]["event"][:40]),
                "created_at": int(now), "attempts": 0, "next_attempt_at": int(now),
                "last_error": "",
            }
            state["outbox"].insert(0, digest)
        else:
            digest_index = state["outbox"].index(digest)
            victim_index = next((index for index, pending in enumerate(state["outbox"])
                                 if index != digest_index and pending["event"] not in
                                 ("digest", "recovery_exhausted")), None)
            if victim_index is None:
                if len(state["outbox"]) < MAX_PRIORITY_OUTBOX:
                    state["outbox"].append(item)
                    _remember_notice_id(state, stored_id)
                    return True
                return False
            replaced = state["outbox"].pop(victim_index)
            count = _coalesced_notice_count(digest) + _coalesced_notice_count(replaced)
            digest["body"] = ("较早通知已合并，请优先处理当前恢复事件。\n\n"
                              "时间（Asia/Shanghai）：%s\ncoalesced_count=%d\n最新事件=%s" %
                              (asia_shanghai_text(now), count, replaced["event"][:40]))
            digest["next_attempt_at"] = min(digest["next_attempt_at"], int(now))
        state["outbox"].append(item)
        _remember_notice_id(state, stored_id)
        return True
    if len(state["outbox"]) >= MAX_OUTBOX:
        for index, pending in enumerate(state["outbox"]):
            if pending["event"] == "reminder":
                state["outbox"].pop(index)
                break
    if len(state["outbox"]) >= MAX_OUTBOX:
        digest = next((pending for pending in state["outbox"] if pending["event"] == "digest"), None)
        if digest is None:
            victim_index = next((index for index, pending in enumerate(state["outbox"])
                                 if pending["event"] != "recovery_exhausted"), None)
            if victim_index is None:
                return False
            replaced = state["outbox"].pop(victim_index)
            digest = {
                "id": "outbox-digest", "event": "digest",
                "subject": SUBJECT_DIGEST,
                "body": "较早通知已合并，请查看当前状态。\n\n"
                        "时间（Asia/Shanghai）：%s\ncoalesced_count=2\n最新事件=%s,%s" %
                        (asia_shanghai_text(now), replaced["event"], safe_label(event)),
                "created_at": int(now), "attempts": 0, "next_attempt_at": int(now),
                "last_error": "",
            }
            state["outbox"].insert(0, digest)
        else:
            match = re.search(r"coalesced_count=(\d+)", digest["body"])
            count = int(match.group(1)) + 1 if match else 2
            digest["body"] = ("较早通知已合并，请查看当前状态。\n\n"
                              "时间（Asia/Shanghai）：%s\ncoalesced_count=%d\n最新事件=%s" %
                              (asia_shanghai_text(now), count, safe_label(event)))
            digest["next_attempt_at"] = min(digest["next_attempt_at"], int(now))
        _remember_notice_id(state, stored_id)
        return True
    state["outbox"].append(item)
    _remember_notice_id(state, stored_id)
    return True


def flush_outbox(state, effects, config, now, limit=2, preferred_id=None):
    if not config["email_enabled"]:
        return 0
    if preferred_id is None:
        priority = next((item for item in state["outbox"]
                         if item["event"] == "recovery_exhausted"), None)
        preferred_id = priority["id"] if priority is not None else None
    if preferred_id is not None:
        for index, item in enumerate(state["outbox"]):
            if item["id"] == preferred_id:
                state["outbox"].insert(0, state["outbox"].pop(index))
                break
    delivered = 0
    examined = 0
    index = 0
    while index < len(state["outbox"]) and examined < limit:
        item = state["outbox"][index]
        if item["next_attempt_at"] > now:
            index += 1
            continue
        examined += 1
        # Re-sanitize at delivery time so pre-upgrade queued subjects also use
        # the bounded Python 3.6-safe representation.
        item["subject"] = sanitize_mail_subject(item["subject"])
        item["body"] = sanitize_mail_body(item["body"])
        accepted, classification = effects.send_email(item["subject"], item["body"])
        if accepted:
            state["outbox"].pop(index)
            delivered += 1
            continue
        item["attempts"] += 1
        delay = min(21600, 300 * (2 ** min(item["attempts"], 6)))
        item["next_attempt_at"] = int(now + delay)
        item["last_error"] = safe_label(classification)
        index += 1
    return delivered


class Monitor(object):
    def __init__(self, effects, persist, clock=None, maintenance_check=None):
        self.effects = effects
        self.persist = persist
        self.clock = clock or time.time
        self.maintenance_check = maintenance_check

    def _probe(self, function, fallback):
        try:
            result = function()
            if not isinstance(result, dict) or "healthy" not in result or "classification" not in result:
                raise MonitorError("probe_shape_invalid")
            return result
        except Exception as exc:
            return {"healthy": False, "classification": "%s_%s" % (fallback, safe_label(type(exc).__name__))}

    def _probe_with_time(self, function, fallback):
        result = self._probe(function, fallback)
        return result, int(self.clock())

    def _maintenance_observation(self):
        try:
            if self.maintenance_check is None:
                raise MonitorError("maintenance_revalidation_unavailable")
            active = self.maintenance_check()
            if not isinstance(active, bool):
                raise MonitorError("maintenance_revalidation_invalid")
            result = {
                "healthy": not active,
                "classification": "maintenance_absent" if not active else "maintenance_enabled",
            }
        except Exception as exc:
            result = {"healthy": False,
                      "classification": "maintenance_%s" % safe_label(type(exc).__name__)}
        return result, int(self.clock())

    def _finalize_interrupted_exhaustion(self, state, incident_id, status, results, now):
        recovery = state["recovery"]
        flight = recovery.get("in_flight")
        if flight is None or recovery["attempts"] != MAX_RECOVERY_ATTEMPTS \
                or flight.get("attempt") != MAX_RECOVERY_ATTEMPTS:
            return None
        recovery["circuit_latched"] = True
        recovery["in_flight"] = None
        recovery["last_result"] = {
            "at": int(now), "action": flight["action"], "attempt": flight["attempt"],
            "classification": "unknown_interrupted_no_terminal_receipt",
        }
        state["last_snapshot"]["recovery"]["decision"] = "circuit_latched"
        state["last_snapshot"]["recovery"]["result"] = \
            "unknown_interrupted_no_terminal_receipt"
        notice_id = "incident:%s:recovery-exhausted" % incident_id
        queued = enqueue_notice(
            state, notice_id, "recovery_exhausted",
            SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN,
            interrupted_recovery_exhausted_body(
                now, incident_id, flight, status, results), now)
        if not queued and notice_id not in state["notice_ids"]:
            raise MonitorError("recovery_exhausted_notice_not_durable")
        state["updated_at"] = int(now)
        self.persist(state)
        return sanitize_notice_id(notice_id)

    def check_once(self, state, config, maintenance=False):
        now = int(self.clock())
        results = {}
        observed_at = {}
        results["local_api"], observed_at["local_api"] = self._probe_with_time(
            self.effects.canonical_status, "canonical")
        status = results["local_api"]
        results["web"], observed_at["web"] = self._probe_with_time(
            lambda: self.effects.web(config["web_marker"]), "web")
        results["public_api"], observed_at["public_api"] = self._probe_with_time(
            self.effects.public_api, "public_api")
        results["mysql"], observed_at["mysql"] = self._probe_with_time(
            self.effects.mysql, "mysql")
        results["redis"], observed_at["redis"] = self._probe_with_time(
            self.effects.redis, "redis")
        results["agent"], observed_at["agent"] = self._probe_with_time(
            self.effects.agent, "agent")
        recovery_incident_id = state["incident"]["id"] if state["incident"] else "unconfirmed"
        for name in COMPONENTS:
            if results[name]["healthy"]:
                state["component_streaks"][name] = 0
            else:
                state["component_streaks"][name] += 1
        all_healthy = all(results[name]["healthy"] for name in COMPONENTS)
        state["all_healthy_streak"] = state["all_healthy_streak"] + 1 if all_healthy else 0
        if status["healthy"]:
            state["api_healthy_streak"] += 1
        else:
            state["api_healthy_streak"] = 0
        flight = state["recovery"]["in_flight"]
        early_interruption = flight is not None \
            and flight["attempt"] < MAX_RECOVERY_ATTEMPTS
        if state["api_healthy_streak"] >= HEALTHY_RESET_THRESHOLD \
                and (flight is None or early_interruption):
            state["recovery"].update({
                "attempts": 0, "circuit_latched": False, "last_attempt_at": None,
                "in_flight": None, "last_result": None,
            })
        confirmed = sorted(name for name in COMPONENTS
                           if state["component_streaks"][name] >= FAILURE_THRESHOLD)
        if state["incident"] is None and confirmed:
            state["sequence"] += 1
            incident_id = "I%06d-%d" % (state["sequence"], now)
            state["incident"] = {"id": incident_id, "opened_at": now,
                                 "components": confirmed, "last_reminder_slot": 0}
            enqueue_notice(state, "incident:%s:confirmed" % incident_id, "incident_confirmed",
                           SUBJECT_INCIDENT_CONFIRMED,
                           notice_body("incident_confirmed", now, incident_id, confirmed), now)
        elif state["incident"] is not None:
            state["incident"]["components"] = confirmed or state["incident"]["components"]
            if state["all_healthy_streak"] >= HEALTHY_RESET_THRESHOLD:
                incident = state["incident"]
                enqueue_notice(state, "incident:%s:resolved" % incident["id"], "resolved",
                               SUBJECT_RESOLVED,
                               notice_body("resolved_after_three_healthy_checks", now,
                                           incident["id"], incident["components"]), now)
                state["incident"] = None
            else:
                incident = state["incident"]
                slot = max(0, (now - incident["opened_at"]) // config["reminder_interval_seconds"])
                if slot > incident["last_reminder_slot"]:
                    incident["last_reminder_slot"] = slot
                    enqueue_notice(state, "incident:%s:reminder:%d" % (incident["id"], slot),
                                   "reminder", SUBJECT_REMINDER,
                                   notice_body("restrained_reminder", now, incident["id"],
                                               incident["components"]), now)
        state["last_snapshot"] = {
            "at": now, "maintenance": bool(maintenance), "overall_healthy": all_healthy,
            "checks": {name: sanitized_result(results[name], observed_at[name])
                       for name in COMPONENTS},
            "recovery": {"decision": "none", "result": "not_attempted"},
        }
        latest_observation_at = max(observed_at.values())
        state["updated_at"] = latest_observation_at
        self.persist(state)

        interrupted_notice_id = self._finalize_interrupted_exhaustion(
            state, recovery_incident_id, status, results, latest_observation_at)

        decision = self._recovery_decision(state, status, results, maintenance, now)
        state["last_snapshot"]["recovery"]["decision"] = decision["classification"]
        action = decision.get("action")
        pre_recovery_mail_accepted = 0
        resource_observation = "not_observed"
        if action:
            resources, resources_at = self._probe_with_time(self.effects.resources, "resources")
            resource_observation = "%s:%s" % (
                "ok" if resources["healthy"] else "warning",
                safe_label(resources["classification"]))
            state["last_snapshot"]["recovery"]["resource_observation"] = resource_observation
            state["last_snapshot"]["checks"]["resource_observation"] = \
                sanitized_result(resources, resources_at)
        if action:
            recovery = state["recovery"]
            attempt = recovery["attempts"] + 1
            incident_id = state["incident"]["id"] if state["incident"] else "unconfirmed"
            attempt_notice_id = "incident:%s:recovery:%d:attempted:%d" % \
                (incident_id, attempt, now)
            attempt_notice_queued = enqueue_notice(
                state, attempt_notice_id, "recovery_attempted",
                SUBJECT_RECOVERY_ATTEMPT %
                (attempt, MAX_RECOVERY_ATTEMPTS),
                notice_body("recovery_attempt_selected", now, incident_id, ["local_api"],
                            "本次：动作=%s；尝试=%d/%d；资源观测=%s；身份重新校验待完成。" %
                            (ACTION_NAMES_ZH[action], attempt, MAX_RECOVERY_ATTEMPTS,
                             safe_label(resource_observation))), now)
            if not attempt_notice_queued:
                state["last_snapshot"]["recovery"]["decision"] = \
                    "recovery_notice_queue_protected"
                state["last_snapshot"]["recovery"]["result"] = "not_attempted"
                state["updated_at"] = int(self.clock())
                self.persist(state)
                action = None
        if action:
            state["updated_at"] = max(state["updated_at"], resources_at)
            self.persist(state)  # current attempt notice is durable before priority delivery
            pre_recovery_mail_accepted = flush_outbox(
                state, self.effects, config, now, 1, preferred_id=attempt_notice_id)
            self.persist(state)  # failed priority delivery remains durable before revalidation

            maintenance_result, maintenance_at = self._maintenance_observation()
            mysql_rechecked, mysql_at = self._probe_with_time(
                self.effects.mysql, "mysql_pre_recovery")
            redis_rechecked, redis_at = self._probe_with_time(
                self.effects.redis, "redis_pre_recovery")
            rechecked, rechecked_at = self._probe_with_time(
                self.effects.canonical_status, "canonical_pre_recovery")
            state["last_snapshot"]["checks"]["maintenance_revalidation"] = \
                sanitized_result(maintenance_result, maintenance_at)
            state["last_snapshot"]["checks"]["mysql_revalidation"] = \
                sanitized_result(mysql_rechecked, mysql_at)
            state["last_snapshot"]["checks"]["redis_revalidation"] = \
                sanitized_result(redis_rechecked, redis_at)
            state["last_snapshot"]["checks"]["local_api_revalidation"] = \
                sanitized_result(rechecked, rechecked_at)
            state["last_snapshot"]["maintenance"] = not maintenance_result["healthy"]
            if not maintenance_result["healthy"]:
                revalidation = {"permitted": False,
                                "classification": "revalidation_maintenance_active_or_unknown"}
            elif not mysql_rechecked["healthy"] or not redis_rechecked["healthy"]:
                revalidation = {"permitted": False,
                                "classification": "revalidation_dependencies_unreachable"}
            else:
                revalidation = self._revalidate_recovery(action, status, rechecked)
            if not revalidation.get("permitted"):
                classification = revalidation["classification"]
                revalidation_at = max(maintenance_at, mysql_at, redis_at, rechecked_at)
                state["last_snapshot"]["recovery"]["decision"] = classification
                state["last_snapshot"]["recovery"]["result"] = "not_attempted_after_revalidation"
                enqueue_notice(state,
                               "incident:%s:recovery:%d:revalidation:%s" %
                               (incident_id, attempt, classification),
                               "recovery_deferred", SUBJECT_RECOVERY_DEFERRED,
                               notice_body("recovery_deferred_revalidation", revalidation_at, incident_id,
                                           ["local_api"], "本次：动作=%s；原因=%s；尝试次数未增加。" %
                                           (ACTION_NAMES_ZH[action], safe_label(classification))),
                               revalidation_at)
                state["updated_at"] = revalidation_at
                self.persist(state)
                action = None
            else:
                try:
                    carrier = self.effects.recovery_precondition(
                        action, incident_id, attempt)
                    if not isinstance(carrier, dict) \
                            or not isinstance(carrier.get("permitted"), bool) \
                            or not isinstance(carrier.get("classification"), str):
                        raise MonitorError("recovery_carrier_precondition_invalid")
                except Exception as exc:
                    carrier = {
                        "permitted": False,
                        "classification": "recovery_carrier_%s" %
                        safe_label(type(exc).__name__),
                    }
                if not carrier["permitted"]:
                    classification = safe_label(carrier["classification"])
                    carrier_at = int(self.clock())
                    state["last_snapshot"]["recovery"]["decision"] = classification
                    state["last_snapshot"]["recovery"]["result"] = \
                        "not_attempted_after_carrier_precondition"
                    enqueue_notice(
                        state,
                        "incident:%s:recovery:%d:carrier:%s" %
                        (incident_id, attempt, classification),
                        "recovery_deferred", SUBJECT_RECOVERY_DEFERRED,
                        notice_body(
                            "recovery_deferred_revalidation", carrier_at,
                            incident_id, ["local_api"],
                            "本次：动作=%s；原因=%s；尝试次数未增加。" %
                            (ACTION_NAMES_ZH[action], classification)),
                        carrier_at)
                    state["updated_at"] = carrier_at
                    self.persist(state)
                    action = None
            if action:
                previous_attempts = recovery["attempts"]
                previous_last_attempt_at = recovery["last_attempt_at"]
                attempt_started_at = max(
                    int(self.clock()), maintenance_at, mysql_at, redis_at, rechecked_at)
                recovery["attempts"] = attempt
                recovery["last_attempt_at"] = attempt_started_at
                recovery["in_flight"] = {
                    "action": action, "attempt": attempt, "at": attempt_started_at}
                state["last_snapshot"]["recovery"]["decision"] = revalidation["classification"]
                state["updated_at"] = attempt_started_at
                self.persist(state)  # durable reservation immediately before carrier execution

                def record_dispatch():
                    flight = recovery.get("in_flight")
                    if not isinstance(flight, dict) \
                            or flight.get("action") != action \
                            or flight.get("attempt") != attempt:
                        raise MonitorError("native_dispatch_fence_changed")
                    dispatched_at = max(int(self.clock()), attempt_started_at)
                    flight["dispatch_at"] = dispatched_at
                    state["updated_at"] = dispatched_at
                    self.persist(state)

                def record_native_invocation():
                    flight = recovery.get("in_flight")
                    if not isinstance(flight, dict) \
                            or flight.get("action") != action \
                            or flight.get("attempt") != attempt \
                            or "dispatch_at" not in flight:
                        raise MonitorError("native_invocation_fence_changed")
                    invoked_at = max(int(self.clock()), attempt_started_at)
                    flight["native_invoked_at"] = invoked_at
                    state["updated_at"] = invoked_at
                    self.persist(state)

                try:
                    command_result = self.effects.recover(
                        action, incident_id, attempt,
                        record_dispatch, record_native_invocation)
                    if not isinstance(command_result, dict) \
                            or not isinstance(command_result.get("returncode"), int) \
                            or isinstance(command_result.get("returncode"), bool) \
                            or (command_result.get("carrier_returncode") is not None \
                                and (not isinstance(command_result.get("carrier_returncode"), int) \
                                     or isinstance(command_result.get("carrier_returncode"), bool))) \
                            or (command_result.get("dispatch_confirmed") is not None \
                                and not isinstance(command_result.get("dispatch_confirmed"), bool)) \
                            or (command_result.get("native_invoked") is not None \
                                and not isinstance(command_result.get("native_invoked"), bool)) \
                            or (command_result.get("native_returncode") is not None \
                                and (not isinstance(command_result.get("native_returncode"), int) \
                                     or isinstance(command_result.get("native_returncode"), bool))) \
                            or not isinstance(command_result.get("terminal_confirmed"), bool) \
                            or (command_result.get("dispatch_confirmed") is False \
                                and (command_result.get("native_invoked") is not False \
                                     or not command_result.get("terminal_confirmed"))) \
                            or (command_result.get("native_invoked") is True \
                                and command_result.get("dispatch_confirmed") is not True) \
                            or (command_result.get("native_returncode") is not None \
                                and command_result.get("native_invoked") is not True):
                        raise MonitorError("recovery_result_invalid")
                except Exception as exc:
                    command_result = {
                        "returncode": 126, "carrier_returncode": None,
                        "dispatch_confirmed": None, "native_invoked": None,
                        "native_returncode": None, "terminal_confirmed": False,
                        "classification": "recovery_%s" % safe_label(type(exc).__name__),
                    }

                definitive_prelaunch_failure = \
                    command_result.get("dispatch_confirmed") is False \
                    and command_result.get("native_invoked") is False \
                    and command_result.get("terminal_confirmed") is True
                if definitive_prelaunch_failure:
                    completed_at = max(int(self.clock()), attempt_started_at)
                    recovery["attempts"] = previous_attempts
                    recovery["last_attempt_at"] = previous_last_attempt_at
                    recovery["in_flight"] = None
                    recovery["last_result"] = {
                        "at": completed_at, "action": action, "attempt": attempt,
                        "classification": "carrier_failed_not_invoked",
                        "dispatch_confirmed": False,
                        "native_invoked": False, "native_returncode": None,
                        "carrier_returncode": command_result["carrier_returncode"],
                        "terminal_confirmed": True,
                    }
                    state["last_snapshot"]["recovery"]["decision"] = \
                        "carrier_failed_not_invoked"
                    state["last_snapshot"]["recovery"]["result"] = \
                        "not_attempted_carrier_failed"
                    state["last_snapshot"]["recovery"]["native_result"] = safe_label(
                        command_result.get("classification"))
                    enqueue_notice(
                        state,
                        "incident:%s:recovery:%d:carrier-terminal:%s" %
                        (incident_id, attempt,
                         safe_label(command_result.get("classification"))),
                        "recovery_deferred", SUBJECT_RECOVERY_DEFERRED,
                        notice_body(
                            "recovery_deferred_revalidation", completed_at,
                            incident_id, ["local_api"],
                            "本次：carrier 未启动规范 API；原因=%s；实际恢复次数未增加。" %
                            safe_label(command_result.get("classification"))),
                        completed_at)
                    state["updated_at"] = completed_at
                    self.persist(state)
                else:
                    fresh, completed_at = self._probe_with_time(
                        self.effects.canonical_status, "canonical_post_recovery")
                    completed_at = max(completed_at, attempt_started_at)
                    native_returncode = command_result.get("native_returncode")
                    unknown_terminal = command_result.get("native_invoked") is not True \
                        or native_returncode is None
                    success = command_result.get("native_invoked") is True \
                        and native_returncode == 0 and fresh.get("healthy") is True
                    if success:
                        classification = "success_health_up"
                    elif unknown_terminal:
                        classification = "unknown_dispatch_or_terminal"
                    else:
                        classification = "failed_fresh_health_not_up"
                    if command_result.get("terminal_confirmed") \
                            or attempt >= MAX_RECOVERY_ATTEMPTS:
                        recovery["in_flight"] = None
                    recovery["last_result"] = {
                        "at": completed_at, "action": action, "attempt": attempt,
                        "classification": classification,
                        "dispatch_confirmed": command_result.get("dispatch_confirmed"),
                        "native_invoked": command_result.get("native_invoked"),
                        "native_returncode": native_returncode,
                        "carrier_returncode": command_result.get("carrier_returncode"),
                        "terminal_confirmed": command_result.get("terminal_confirmed"),
                    }
                    if success:
                        recovery["last_success_at"] = completed_at
                        state["api_healthy_streak"] = 1
                        state["component_streaks"]["local_api"] = 0
                    if not success and recovery["attempts"] >= MAX_RECOVERY_ATTEMPTS:
                        recovery["circuit_latched"] = True
                    state["last_snapshot"]["checks"]["local_api_post_recovery"] = \
                        sanitized_result(fresh, completed_at)
                    state["last_snapshot"]["recovery"]["result"] = classification
                    state["last_snapshot"]["recovery"]["native_result"] = safe_label(
                        command_result.get("classification"))
                    state["updated_at"] = completed_at
                    if recovery["circuit_latched"]:
                        exhausted_notice_id = "incident:%s:recovery-exhausted" % incident_id
                        exhausted_unknown = unknown_terminal
                        enqueue_notice(
                            state, exhausted_notice_id, "recovery_exhausted",
                            SUBJECT_RECOVERY_EXHAUSTED_UNKNOWN if exhausted_unknown else
                            SUBJECT_RECOVERY_EXHAUSTED,
                            uncertain_recovery_exhausted_body(
                                completed_at, incident_id, action, attempt,
                                command_result, fresh, results) if exhausted_unknown else
                            recovery_exhausted_body(
                                completed_at, incident_id, action, attempt, command_result,
                                status, fresh, results, resource_observation),
                            completed_at)
                        self.persist(state)  # latch and urgent notice are durable before delivery
                        pre_recovery_mail_accepted += flush_outbox(
                            state, self.effects, config, completed_at, 1,
                            preferred_id=exhausted_notice_id)
                        self.persist(state)  # mail failure never clears the circuit or notice
                    else:
                        notice_unknown = unknown_terminal
                        enqueue_notice(
                            state, "incident:%s:recovery:%d:result" % (incident_id, attempt),
                            "recovery_unknown" if notice_unknown else "recovery_result",
                            SUBJECT_RECOVERY_RESULT %
                            ("成功" if success else
                             ("未确认" if notice_unknown else "未成功"),
                             attempt, MAX_RECOVERY_ATTEMPTS),
                            notice_body(
                                "recovery_unknown" if notice_unknown else "recovery_result",
                                completed_at, incident_id, ["local_api"],
                                "本次：动作=%s；尝试=%d/%d；规范返回码=%s；恢复后健康=%s（%s）。" %
                                (ACTION_NAMES_ZH[action], attempt, MAX_RECOVERY_ATTEMPTS,
                                 str(native_returncode) if native_returncode is not None else "UNKNOWN",
                                 "UP" if fresh.get("healthy") else "未确认",
                                 safe_label(fresh.get("classification")))), completed_at)
                        state["updated_at"] = completed_at
                        self.persist(state)
        finish_now = int(self.clock())
        preferred_id = interrupted_notice_id
        delivered = pre_recovery_mail_accepted + flush_outbox(
            state, self.effects, config, finish_now, 2, preferred_id=preferred_id)
        state["updated_at"] = finish_now
        self.persist(state)
        return {"healthy": all_healthy,
                "maintenance": bool(state["last_snapshot"]["maintenance"]),
                "recovery": state["last_snapshot"]["recovery"],
                "mail_accepted": delivered, "mail_pending": len(state["outbox"])}

    def _revalidate_recovery(self, action, initial, current):
        if current.get("healthy"):
            return {"permitted": False, "classification": "revalidation_became_healthy"}
        if action == "start":
            permitted = current.get("classification") == "stopped" and current.get("recovery_safe") is True
            return {"permitted": permitted,
                    "classification": "start_revalidated" if permitted else "revalidation_start_state_changed"}
        if action == "restart":
            if current.get("classification") != "not_ready_trusted" \
                    or current.get("recovery_safe") is not True:
                return {"permitted": False, "classification": "revalidation_restart_identity_incomplete"}
            if initial.get("pid") is None or current.get("pid") != initial.get("pid"):
                return {"permitted": False, "classification": "revalidation_restart_pid_changed"}
            age = current.get("elapsed_seconds")
            if age is None or age < STARTUP_GRACE_SECONDS:
                return {"permitted": False, "classification": "revalidation_startup_grace"}
            return {"permitted": True, "classification": "restart_revalidated"}
        return {"permitted": False, "classification": "revalidation_action_invalid"}

    def _recovery_decision(self, state, status, results, maintenance, now):
        if maintenance:
            return {"classification": "maintenance_paused"}
        if status.get("healthy"):
            return {"classification": "local_api_up"}
        if state["component_streaks"]["local_api"] < FAILURE_THRESHOLD:
            return {"classification": "failure_threshold_not_met"}
        if not results["mysql"]["healthy"] or not results["redis"]["healthy"]:
            return {"classification": "dependencies_unreachable"}
        recovery = state["recovery"]
        if recovery["in_flight"] is not None:
            return {"classification": "recovery_in_flight"}
        if recovery["circuit_latched"] or recovery["attempts"] >= MAX_RECOVERY_ATTEMPTS:
            recovery["circuit_latched"] = True
            return {"classification": "circuit_latched"}
        if recovery["last_attempt_at"] is not None \
                and now - recovery["last_attempt_at"] < COOLDOWN_SECONDS:
            return {"classification": "cooldown"}
        if status.get("classification") == "stopped" and status.get("recovery_safe"):
            return {"classification": "start_permitted", "action": "start"}
        if status.get("classification") == "not_ready_trusted" and status.get("recovery_safe"):
            age = status.get("elapsed_seconds")
            if age is None and recovery["last_attempt_at"] is not None:
                age = now - recovery["last_attempt_at"]
            if age is not None and age >= STARTUP_GRACE_SECONDS:
                return {"classification": "restart_permitted", "action": "restart"}
            return {"classification": "startup_grace"}
        return {"classification": "identity_or_status_not_recovery_safe"}


def public_status(state, maintenance):
    recovery = state["recovery"]
    return {
        "initialized_at": utc_text(state["initialized_at"]),
        "updated_at": utc_text(state["updated_at"]),
        "maintenance": bool(maintenance),
        "incident": copy.deepcopy(state["incident"]),
        "recovery": {
            "attempts": recovery["attempts"],
            "circuit_latched": recovery["circuit_latched"],
            "last_attempt_at": utc_text(recovery["last_attempt_at"]) if recovery["last_attempt_at"] is not None else None,
            "in_flight": copy.deepcopy(recovery["in_flight"]),
            "last_result": copy.deepcopy(recovery["last_result"]),
        },
        "mail_pending": len(state["outbox"]),
        "last_snapshot": copy.deepcopy(state["last_snapshot"]),
    }


def require_root():
    if os.geteuid() != 0:
        raise MonitorError("root_required")


def parser():
    result = argparse.ArgumentParser(
        description="Bounded Juyi Hall service health monitor; cron uses --check-once.",
        epilog=("Examples: --init (explicit first state); --check-once (probe/write/recover); "
                "--status (stored snapshot only); --pause/--resume; --reset-circuit; "
                "--notify-test (explicit helper delivery test)."))
    actions = result.add_mutually_exclusive_group(required=True)
    actions.add_argument("--init", action="store_true", help="initialize absent state only; no probes/recovery/mail")
    actions.add_argument("--check-once", action="store_true", help="run one bounded check and optional API-only recovery")
    actions.add_argument("--status", action="store_true", help="read stored snapshot only; never repair or probe")
    actions.add_argument("--pause", action="store_true", help="create the trusted maintenance marker")
    actions.add_argument("--resume", action="store_true", help="remove a trusted maintenance marker")
    actions.add_argument("--reset-circuit", action="store_true", help="explicitly reset API attempt/circuit fence")
    actions.add_argument("--notify-test", action="store_true", help="explicitly enqueue and try one test email; no probes")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    os.umask(0o077)
    store = StateStore()
    try:
        require_root()
        config = load_config()
        if args.init:
            store.prepare_init()
        store.acquire()
        if args.init:
            if os.path.lexists(store.state_path):
                raise MonitorError("state_already_initialized")
            state = initial_state(time.time())
            store.write(state)
            print(json.dumps({"status": "initialized", "state": store.state_path}, sort_keys=True))
            return 0
        state = store.read()
        maintenance = store.maintenance()
        now = int(time.time())
        if args.status:
            print(json.dumps(public_status(state, maintenance), sort_keys=True, separators=(",", ":")))
            return 0
        if args.pause:
            store.pause(now)
            print(json.dumps({"status": "maintenance_paused"}, sort_keys=True))
            return 0
        if args.resume:
            store.resume()
            print(json.dumps({"status": "maintenance_resumed"}, sort_keys=True))
            return 0
        if args.reset_circuit:
            state["recovery"].update({"attempts": 0, "circuit_latched": False,
                                      "last_attempt_at": None, "in_flight": None,
                                      "last_result": None})
            state["updated_at"] = now
            store.write(state)
            print(json.dumps({"status": "circuit_reset"}, sort_keys=True))
            return 0
        effects = Effects()
        if args.notify_test:
            notice_id = "notify-test:%d" % now
            enqueue_notice(state, notice_id, "notify_test", SUBJECT_NOTIFY_TEST,
                           notice_body("explicit_notify_test", now, None, []), now)
            store.write(state)
            accepted = flush_outbox(state, effects, config, now, 1)
            state["updated_at"] = now
            store.write(state)
            print(json.dumps({"status": "notify_test_processed", "helper_accepted": accepted,
                              "mail_pending": len(state["outbox"])}, sort_keys=True))
            return 0 if accepted else 1
        monitor = Monitor(effects, store.write, maintenance_check=store.maintenance)
        summary = monitor.check_once(state, config, maintenance)
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        return 0 if summary["healthy"] else 1
    except BusyError:
        print(json.dumps({"status": "deferred", "reason": "monitor_lock_busy"}, sort_keys=True))
        return 75
    except MonitorError as exc:
        reason = safe_label(str(exc))
        guard_log(reason)
        print(json.dumps({"status": "fail_closed", "reason": reason}, sort_keys=True),
              file=sys.stderr)
        return 2
    except Exception as exc:
        reason = "unexpected_%s" % safe_label(type(exc).__name__)
        guard_log(reason)
        print(json.dumps({"status": "fail_closed", "reason": reason}, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        store.release()


if __name__ == "__main__":
    sys.exit(main())
