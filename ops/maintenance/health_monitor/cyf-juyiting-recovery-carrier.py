#!/usr/bin/python3
"""Fixed recovery carrier for a host-owned systemd scope (Python 3.6 stdlib)."""

import hashlib
import os
import re
import stat
import subprocess
import sys

CANONICAL = "/usr/local/sbin/cyf-api-kit"
CANONICAL_SHA256 = "94de2c8af2745d25a9cec82276d54e52c85a63ae7349f4204b36ba5f5f5b930f"
MEMORY_CGROUP_ROOT = "/sys/fs/cgroup/memory"
PROC_SELF_CGROUP = "/proc/self/cgroup"
MAX_CANONICAL_BYTES = 1024 * 1024
FIXED_RECOVERY_ENV = {
    "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
    "HOME": "/root",
    "LC_ALL": "C",
    "LANG": "C",
    "USER": "root",
    "LOGNAME": "root",
    "CYF_API_MIN_MEMORY_AVAILABLE_BYTES": "0",
    "CYF_API_MIN_DISK_AVAILABLE_BYTES": "0",
}
MARKER_NATIVE_DISPATCH = "CYF_HEALTHMON_NATIVE_DISPATCH=1"
MARKER_NATIVE_INVOKED = "CYF_HEALTHMON_NATIVE_INVOKED=1"
MARKER_NATIVE_RESULT = "CYF_HEALTHMON_NATIVE_RESULT="


class CarrierError(Exception):
    pass


def scope_unit(incident_id, attempt):
    if not isinstance(incident_id, str) \
            or not re.match(r"^I[0-9]{6,12}-[0-9]{1,20}$", incident_id):
        raise CarrierError("incident_invalid")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1 or attempt > 3:
        raise CarrierError("attempt_invalid")
    return "cyf-api-healthmon-%s-a%d.scope" % (incident_id.lower(), attempt)


def sha256_fd(fd):
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        digest.update(chunk)
    return digest.hexdigest()


def validate_canonical():
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(CANONICAL, flags)
    try:
        info = os.fstat(fd)
        mode = stat.S_IMODE(info.st_mode)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 \
                or mode != 0o755 or info.st_size > MAX_CANONICAL_BYTES:
            raise CarrierError("canonical_identity_invalid")
        if sha256_fd(fd) != CANONICAL_SHA256:
            raise CarrierError("canonical_hash_mismatch")
    finally:
        os.close(fd)


def memory_cgroup(path=PROC_SELF_CGROUP):
    with open(path, "r") as stream:
        for line in stream:
            fields = line.rstrip("\n").split(":", 2)
            if len(fields) == 3 and "memory" in fields[1].split(","):
                return fields[2]
    raise CarrierError("memory_cgroup_missing")


def validate_cgroup_node(path, directory):
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or info.st_uid != 0:
        raise CarrierError("cgroup_node_identity_invalid")
    if directory:
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o022:
            raise CarrierError("cgroup_directory_invalid")
    elif not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o022:
        raise CarrierError("cgroup_control_invalid")
    return info


def configure_own_swappiness(unit, root=MEMORY_CGROUP_ROOT, proc_path=PROC_SELF_CGROUP):
    expected_relative = "/system.slice/" + unit
    if memory_cgroup(proc_path) != expected_relative:
        raise CarrierError("scope_cgroup_mismatch")
    root = os.path.abspath(root)
    directory = root + expected_relative
    if os.path.realpath(directory) != directory or not directory.startswith(root + "/system.slice/"):
        raise CarrierError("scope_path_invalid")
    validate_cgroup_node(root, True)
    validate_cgroup_node(os.path.join(root, "system.slice"), True)
    validate_cgroup_node(directory, True)
    control = os.path.join(directory, "memory.swappiness")
    expected = validate_cgroup_node(control, False)
    flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(control, flags)
    try:
        actual = os.fstat(fd)
        if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino) \
                or actual.st_uid != 0 or not stat.S_ISREG(actual.st_mode):
            raise CarrierError("cgroup_control_changed")
        if os.write(fd, b"60\n") != 3:
            raise CarrierError("swappiness_write_incomplete")
    finally:
        os.close(fd)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(control, flags)
    try:
        actual = os.fstat(fd)
        if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino) \
                or actual.st_uid != 0 or not stat.S_ISREG(actual.st_mode):
            raise CarrierError("cgroup_control_changed")
        if os.read(fd, 16).strip() != b"60":
            raise CarrierError("swappiness_readback_invalid")
    finally:
        os.close(fd)


def emit(value):
    sys.stdout.write(value + "\n")
    sys.stdout.flush()


def run(action, incident_id, attempt):
    if action not in ("start", "restart"):
        raise CarrierError("action_invalid")
    unit = scope_unit(incident_id, attempt)
    configure_own_swappiness(unit)
    validate_canonical()
    # Once this marker is flushed the parent must retain the reserved attempt:
    # canonical dispatch is imminent and a later transport failure is ambiguous.
    emit(MARKER_NATIVE_DISPATCH)
    process = subprocess.Popen(
        [CANONICAL, action], stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd="/", env=dict(FIXED_RECOVERY_ENV), close_fds=True)
    emit(MARKER_NATIVE_INVOKED)
    returncode = process.wait()
    emit(MARKER_NATIVE_RESULT + str(int(returncode)))
    return int(returncode) if 0 <= int(returncode) <= 125 else 125


def main(argv=None):
    values = list(sys.argv[1:] if argv is None else argv)
    # A read-only preflight exposes stale trust pins before reserving an
    # automatic recovery attempt. It never creates a scope or starts Java.
    if values == ["--check"]:
        try:
            validate_canonical()
        except CarrierError as exc:
            sys.stderr.write("CYF_HEALTHMON_CHECK_ERROR=%s\n" % str(exc))
            return 125
        except OSError:
            sys.stderr.write("CYF_HEALTHMON_CHECK_ERROR=canonical_unavailable\n")
            return 125
        emit("CYF_HEALTHMON_CANONICAL=OK")
        return 0
    if len(values) != 3 or not values[2].isdigit():
        return 125
    try:
        return run(values[0], values[1], int(values[2]))
    except (CarrierError, OSError, ValueError, subprocess.SubprocessError):
        return 125


if __name__ == "__main__":
    sys.exit(main())
