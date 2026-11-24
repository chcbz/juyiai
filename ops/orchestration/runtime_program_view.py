"""Prepare the Runtime's canonical paths inside a fresh private mount namespace.

No production entry point. Caller supplies the locked instance identity and an
empty, protected disk skeleton; validates the release inside this same namespace
and must not hand execution back to systemd for a second pathname lookup.
"""
import os
from pathlib import Path
import stat
import subprocess


def protect_instance(instance, skeleton, *, device, inode, parent_ns):
    instance, skeleton = Path(instance), Path(skeleton)
    # Never mount in the invoking namespace. Require private propagation BEFORE touching mounts.
    ns = os.stat('/proc/self/ns/mnt')
    init_ns = os.stat('/proc/1/ns/mnt')
    if (ns.st_dev, ns.st_ino) in (parent_ns, (init_ns.st_dev, init_ns.st_ino)):
        raise ValueError('dedicated mount namespace required')
    propagation = subprocess.check_output(['/usr/bin/findmnt', '-n', '-T', instance.parent,
                                           '-o', 'PROPAGATION'], text=True).strip()
    if propagation != 'private':
        raise ValueError('private mount propagation required')
    if (not instance.is_absolute() or instance.resolve(strict=True) != instance or
            skeleton.resolve(strict=True) != skeleton or instance.parent in (skeleton, *skeleton.parents)
            or skeleton in instance.parents):
        raise ValueError('overlapping or aliased view')
    leaf = skeleton / instance.name
    for directory in {leaf, *leaf.parents, *instance.parent.parents}:
        s = directory.lstat()
        if not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o022:
            raise ValueError('untrusted view skeleton or ancestor')
    if list(skeleton.iterdir()) != [leaf] or any(leaf.iterdir()):
        raise ValueError('view skeleton must contain only the empty instance slot')
    fd = os.open(instance, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_PATH)
    try:
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) != (device, inode) or st.st_uid != 0 or st.st_mode & 0o022:
            raise ValueError('instance identity changed')
        subprocess.run(['/usr/bin/mount', '--bind', skeleton, instance.parent], check=True)
        # Do not resolve the original public path again. Keep nested state mounts and its contents.
        subprocess.run(['/usr/bin/mount', '--no-canonicalize', '--rbind', f'/proc/self/fd/{fd}', instance],
                       pass_fds=(fd,), check=True)
        after = instance.stat()
        if (after.st_dev, after.st_ino) != (device, inode):
            raise ValueError('instance view mismatch')
    finally:
        os.close(fd)


def activate_unified(instance, skeleton, *, authority, config, parent_ns):
    """Run from a dedicated worker/manager child; success replaces this PID.

    The release protocol must stop/drain the prior process before another swap.
    No lock reacquisition: the installer may already hold it across service start.
    """
    from runtime_start_admission import verify
    instance, config = Path(instance), Path(config)
    permit = authority.read_allowed()
    protect_instance(instance, skeleton, device=permit['device'], inode=permit['inode'], parent_ns=parent_ns)
    app = instance / 'app'
    verify(app, instance / 'release-records', **permit['pins'])
    os.chdir(app)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    subprocess.run(['/bin/bash', app / 'runtime/validate.sh', '--root', app, '--config', config], env=env, check=True)
    if authority.read_allowed() != permit:
        raise ValueError('activation generation changed during validation')
    node = app / 'node/bin/node'
    os.execve(node, [node, app / 'runtime/agent-runtime.mjs', 'run', '--config', config], env)
