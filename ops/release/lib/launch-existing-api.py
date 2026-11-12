#!/usr/bin/env python3
"""Validate and exec the existing production API launch profile without printing it.

The profile is read from the SHA-pinned legacy start script. Only three literal
assignments are consumed: JAVA_HOME, JVM_OPTS, and APP_OPTS. No other shell code
is evaluated.
"""

import argparse
import hashlib
import os
from pathlib import Path
import pwd
import re
import shlex
import stat
import sys

EXPECTED_JAVA_HOME = "/home/isp/apps/jdk21"
EXPECTED_LOG_DIR = Path("/home/isp/hosts/cyf/api/logs")
EXPECTED_APPLICATION_LOG = EXPECTED_LOG_DIR / "root.log"
RECOVERY_LOG_PATTERN = re.compile(r"^recovery-existing-old-[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9]+\.log$")


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def open_physical(path, label):
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise SystemExit(f"{label} must be an openable physical file") from None
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(fd)
        raise SystemExit(f"{label} must be a regular physical file")
    return fd, metadata


def hash_physical(path, label, capture=False):
    fd, metadata = open_physical(path, label)
    digest = hashlib.sha256()
    chunks = []
    try:
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            if capture:
                chunks.append(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest(), identity(metadata), b"".join(chunks) if capture else None


def identity_unchanged(path, expected):
    try:
        metadata = os.lstat(str(path))
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and identity(metadata) == expected


def prepare_log_files(application_log, recovery_log, runtime_identity):
    app_path = Path(application_log)
    recovery_path = Path(recovery_log)
    if app_path != EXPECTED_APPLICATION_LOG:
        raise SystemExit("production API application log path mismatch")
    if recovery_path.parent != EXPECTED_LOG_DIR or not RECOVERY_LOG_PATTERN.fullmatch(recovery_path.name):
        raise SystemExit("production API recovery log path mismatch")
    try:
        directory_fd = os.open(str(EXPECTED_LOG_DIR), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        raise SystemExit("production API log directory must be a physical directory") from None
    app_fd = recovery_fd = None
    try:
        app_fd = os.open(
            app_path.name,
            os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
            0o640,
            dir_fd=directory_fd,
        )
        if not stat.S_ISREG(os.fstat(app_fd).st_mode):
            raise SystemExit("production API application log must be a regular file")
        os.fchown(app_fd, runtime_identity.pw_uid, runtime_identity.pw_gid)
        os.fchmod(app_fd, 0o640)
        recovery_fd = os.open(
            recovery_path.name,
            os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        if not stat.S_ISREG(os.fstat(recovery_fd).st_mode):
            raise SystemExit("production API recovery log must be a regular file")
        os.fchown(recovery_fd, runtime_identity.pw_uid, runtime_identity.pw_gid)
        os.fchmod(recovery_fd, 0o600)
        os.dup2(recovery_fd, 1, inheritable=True)
        os.dup2(recovery_fd, 2, inheritable=True)
    except OSError:
        raise SystemExit("production API log preparation failed") from None
    finally:
        if app_fd is not None:
            os.close(app_fd)
        if recovery_fd is not None and recovery_fd not in (1, 2):
            os.close(recovery_fd)
        os.close(directory_fd)


def close_inherited_fds():
    """Keep only stdio across the final Java exec.

    The recovery shell intentionally holds deploy/recovery flock descriptors
    while it validates and commits the new PID.  Those descriptors must remain
    owned by the recovery shell only; inheriting one into the long-lived JVM
    would permanently pin the operational lock after the shell exits.
    """
    try:
        inherited = [int(name) for name in os.listdir("/proc/self/fd") if name.isdigit()]
    except OSError:
        raise SystemExit("cannot enumerate inherited file descriptors") from None
    for fd in inherited:
        if fd <= 2:
            continue
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        candidates = [int(name) for name in os.listdir("/proc/self/fd") if name.isdigit() and int(name) > 2]
    except OSError:
        raise SystemExit("cannot verify inherited file descriptor closure") from None
    remaining = []
    for fd in candidates:
        try:
            os.fstat(fd)
        except OSError:
            continue
        remaining.append(fd)
    if remaining:
        raise SystemExit("unexpected inherited file descriptor remains before Java exec")


def literal_assignment(script, name):
    matches = []
    pattern = re.compile(rf"^{re.escape(name)}=(.*)$")
    for line in script.splitlines():
        match = pattern.fullmatch(line)
        if match:
            matches.append(match.group(1))
    if len(matches) != 1:
        raise SystemExit(f"legacy start script must define exactly one {name} assignment")
    rhs = matches[0]
    if any(marker in rhs for marker in ("$(`", "$(", "`", ";", "\n", "\r")):
        raise SystemExit(f"legacy start script {name} must be a static shell literal")
    try:
        values = shlex.split(rhs, posix=True)
    except ValueError:
        raise SystemExit(f"legacy start script {name} is not a valid shell literal") from None
    if len(values) != 1:
        raise SystemExit(f"legacy start script {name} must resolve to one literal string")
    return values[0]


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--start-script", required=True)
    parser.add_argument("--expected-start-script-sha256", required=True)
    parser.add_argument("--jar", required=True)
    parser.add_argument("--expected-jar-sha256", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--expected-runtime-user", required=True)
    parser.add_argument("--application-log")
    parser.add_argument("--recovery-log")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--validate-runtime-identity-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    start_script = Path(args.start_script)
    jar = Path(args.jar)
    work_dir = Path(args.work_dir)
    start_sha, start_identity, start_bytes = hash_physical(start_script, "legacy start script", capture=True)
    jar_sha, jar_identity, _ = hash_physical(jar, "existing production JAR")
    if start_sha != args.expected_start_script_sha256:
        raise SystemExit("legacy start script SHA-256 mismatch")
    if jar_sha != args.expected_jar_sha256:
        raise SystemExit("existing production JAR SHA-256 mismatch")
    if work_dir.is_symlink() or not work_dir.is_dir():
        raise SystemExit("production API work directory must be a physical directory")

    try:
        script = start_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("legacy start script is not UTF-8") from None
    java_home = literal_assignment(script, "JAVA_HOME")
    jvm_literal = literal_assignment(script, "JVM_OPTS")
    # The pinned legacy shell expands its sole unbound $t_ reference to empty.
    # Reproduce that byte-for-byte behavior without evaluating arbitrary shell variables.
    if jvm_literal.count("$t_") != 1 or "$" in jvm_literal.replace("$t_", ""):
        raise SystemExit("legacy JVM options contain unsupported shell expansion")
    jvm_options = shlex.split(jvm_literal.replace("$t_", ""), posix=True)
    app_literal = literal_assignment(script, "APP_OPTS")
    if "$" in app_literal:
        raise SystemExit("legacy APP_OPTS contain unsupported shell expansion")
    app_options = shlex.split(app_literal, posix=True)

    if java_home != EXPECTED_JAVA_HOME:
        raise SystemExit("legacy start script JAVA_HOME mismatch")
    if "-jar" in jvm_options or any(option.startswith("@") for option in jvm_options):
        raise SystemExit("legacy JVM options contain a forbidden launcher override")
    if "--server.port=10018" not in app_options:
        raise SystemExit("legacy APP_OPTS do not bind server.port=10018")
    if "--spring.profiles.active=prod" not in app_options:
        raise SystemExit("legacy APP_OPTS do not bind the prod profile")
    if sum(option.startswith("--jasypt.encryptor.password=") for option in app_options) != 1:
        raise SystemExit("legacy APP_OPTS do not contain exactly one encryption password option")
    if any(option.startswith("@") for option in app_options):
        raise SystemExit("legacy APP_OPTS contain a forbidden argument-file override")

    java = Path(java_home) / "bin" / "java"
    if java.is_symlink() or not java.is_file() or not os.access(java, os.X_OK):
        raise SystemExit("legacy Java executable is not an executable physical file")
    try:
        runtime_identity = pwd.getpwnam(args.expected_runtime_user)
    except KeyError:
        raise SystemExit("expected runtime user does not exist") from None

    if args.validate_only:
        print("LEGACY_LAUNCH_PROFILE=PASS")
        print(f"JAVA_EXECUTABLE={java}")
        print("SERVER_PORT=10018")
        print("SPRING_PROFILE=prod")
        print(f"RUNTIME_USER={args.expected_runtime_user}")
        print(f"RUNTIME_UID={runtime_identity.pw_uid}")
        print(f"RUNTIME_GID={runtime_identity.pw_gid}")
        print("LEGACY_UNBOUND_T_EXPANSION=NORMALIZED")
        print("SENSITIVE_OPTIONS=VALIDATED_NOT_EMITTED")
        return 0

    if not args.validate_runtime_identity_only:
        if not args.application_log or not args.recovery_log:
            raise SystemExit("production API launch requires explicit log paths")
        prepare_log_files(args.application_log, args.recovery_log, runtime_identity)
        close_inherited_fds()
    if os.geteuid() == 0:
        os.initgroups(args.expected_runtime_user, runtime_identity.pw_gid)
        os.setgid(runtime_identity.pw_gid)
        os.setuid(runtime_identity.pw_uid)
    if os.geteuid() != runtime_identity.pw_uid or os.getegid() != runtime_identity.pw_gid:
        raise SystemExit("recovery launcher runtime identity mismatch")
    if args.validate_runtime_identity_only:
        print("RUNTIME_IDENTITY_DROP=PASS")
        print(f"RUNTIME_USER={args.expected_runtime_user}")
        print(f"RUNTIME_UID={os.geteuid()}")
        print(f"RUNTIME_GID={os.getegid()}")
        print("PRODUCTION_PROCESS_START=NOT_PERFORMED")
        return 0

    if not identity_unchanged(start_script, start_identity):
        raise SystemExit("legacy start script identity changed after validation")
    if not identity_unchanged(jar, jar_identity):
        raise SystemExit("existing production JAR identity changed after validation")
    os.chdir(work_dir)
    os.setsid()
    os.execv(str(java), [str(java), *jvm_options, "-jar", str(jar), *app_options])
    return 127


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1) from None
