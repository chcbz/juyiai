#!/usr/bin/env python3
"""Pinned Flow JDK archive bootstrap; no package manager or cached executables.

Only the archive is persisted. Every invocation rehashes it and extracts into a
new private directory. Runtime failure is fatal, never an implicit yum fallback.
"""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request

VERSION = '21.0.11.0.11'
SHA256 = '12c642f8d6c6e0930b9b4e673d47822227ea46e7559c7b7b6b4c0331ace0580f'
# Official Dragonwell wiki mirror; identical digest to the GitHub release.
URL = 'https://dragonwell.oss-cn-shanghai.aliyuncs.com/21.0.11.0.11%2B10/Alibaba_Dragonwell_Extended_21.0.11.0.11.10_x64_linux.tar.gz'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def physical(path):
    if path.absolute() != path.resolve():
        raise ValueError('symlink path rejected')
    return path


def verified_archive(cache, expected, url, opener=urllib.request.urlopen):
    physical(cache)
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    if cache.stat().st_uid != os.geteuid() or cache.stat().st_mode & 0o022:
        raise ValueError('unsafe cache owner/mode')
    target = cache / ('jdk-' + expected + '.tar.gz')
    if os.path.lexists(str(target)):
        physical(target)
        if not target.is_file() or target.stat().st_nlink != 1 or digest(target) != expected:
            raise ValueError('cached archive integrity failure')
        return target, True
    fd, name = tempfile.mkstemp(prefix='.jdk-download-', dir=str(cache))
    temporary = pathlib.Path(name)
    try:
        with os.fdopen(fd, 'wb') as out, opener(url, timeout=60) as response:
            if not response.geturl().startswith('https://'):
                raise ValueError('non-TLS redirect rejected')
            shutil.copyfileobj(response, out, 1024 * 1024)
        if digest(temporary) != expected:
            raise ValueError('downloaded archive integrity failure')
        os.replace(str(temporary), str(target))
    finally:
        if temporary.exists():
            temporary.unlink()
    return target, False


def extract_fresh(archive, destination):
    physical(destination)
    destination.mkdir(mode=0o700)  # no reuse of extracted executable state
    with tarfile.open(str(archive), 'r:gz') as bundle:
        members = bundle.getmembers()
        names = set()
        for member in members:
            path = pathlib.PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts:
                raise ValueError('unsafe archive member')
            name = str(path)
            if name in names:
                raise ValueError('duplicate archive member')
            names.add(name)
            if not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError('unsupported archive member')
            if member.mode & 0o7000:
                raise ValueError('special archive permission rejected')
            if member.issym():
                target = pathlib.PurePosixPath(member.linkname)
                if target.is_absolute():
                    raise ValueError('absolute archive symlink')
                resolved = (destination / path.parent / target).resolve()
                if destination.resolve() not in resolved.parents:
                    raise ValueError('escaping archive symlink')
        # Never write through a symlink, even an internal one. Create links last.
        links = {str(pathlib.PurePosixPath(x.name)) for x in members if x.issym()}
        for member in members:
            p = pathlib.PurePosixPath(member.name)
            if any(str(parent) in links for parent in p.parents):
                raise ValueError('member beneath archive symlink')
        for member in members:
            if member.issym():
                continue
            target = destination / member.name
            if member.isdir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with bundle.extractfile(member) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                target.chmod(0o700 if member.mode & 0o111 else 0o600)
        for member in members:
            if member.issym():
                target = destination / member.name
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                target.symlink_to(member.linkname)
                # Also detect chained links escaping the fresh extraction root.
        for member in members:
            if member.issym():
                if destination.resolve() not in (destination / member.name).resolve().parents:
                    raise ValueError('escaping chained archive symlink')
    homes = [p.parent.parent for p in destination.glob('*/bin/javac')]
    if len(homes) != 1:
        raise ValueError('expected exactly one JDK')
    return homes[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=pathlib.Path, required=True)
    parser.add_argument('--destination', type=pathlib.Path, required=True)
    args = parser.parse_args()
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise SystemExit('only Linux x86_64 is supported')
    started = time.monotonic()
    archive, hit = verified_archive(args.cache, SHA256, URL)
    ready = time.monotonic()
    home = extract_fresh(archive, args.destination)
    for command in ('java', 'javac'):
        result = subprocess.run([str(home / 'bin' / command), '-version'],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, check=True)
        if VERSION not in result.stdout:
            raise ValueError('JDK version mismatch')
    print('CYF_JDK_TIMING ' + json.dumps({'archive_sha256': SHA256, 'cache_hit': hit,
          'archive_seconds': round(ready - started, 3),
          'total_seconds': round(time.monotonic() - started, 3), 'version': VERSION}), flush=True)
    print(str(home.resolve()))


if __name__ == '__main__':
    main()
