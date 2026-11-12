#!/usr/bin/env python3
"""Render the existing develop CI template. No cloud calls, builds or deployments."""
import argparse
import base64
import gzip
import hashlib
import json
import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASE = ROOT / 'ops/ci/aliyun-flow'
TOOL_FILES = {
    'ops/orchestration/cyf_orchestrator.py': ROOT / 'ops/orchestration/cyf_orchestrator.py',
    'ops/ci/aliyun-flow/backend-ci-policy.json': BASE / 'backend-ci-policy.json',
    'flow-compile-cache.init.gradle': BASE / 'flow-compile-cache.init.gradle',
    'prepare-backend-jdk.py': BASE / 'prepare-backend-jdk.py',
}


def render(template, shell):
    files = {name: path.read_text() for name, path in TOOL_FILES.items()}
    # No human task/owner snapshot or fixed application source is embedded.
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as archive:
        archive.write(json.dumps(files, sort_keys=True).encode())
    raw = buffer.getvalue()
    replacements = {'@CYF_TOOL_BUNDLE_BASE64@': base64.b64encode(raw).decode(),
                    '@CYF_TOOL_BUNDLE_SHA256@': hashlib.sha256(raw).hexdigest()}
    for name, value in replacements.items():
        if shell.count(name) != 1:
            raise ValueError('expected exactly one tool placeholder: ' + name)
        shell = shell.replace(name, value)
    prefix, remaining = template.split('              run: |-\n', 1)
    _, suffix = remaining.split('          upload_artifact:', 1)
    result = prefix + '              run: |-\n' + ''.join(
        ('                ' + line if line else '') + '\n' for line in shell.splitlines())
    result += '          upload_artifact:' + suffix
    if '\n  deploy:' in result or 'VMDeploy' in result:
        raise ValueError('develop default must not deploy')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    template = (BASE / 'templates/backend-develop-release.yaml').read_text()
    value = render(template, (BASE / 'backend-ci-run.sh').read_text())
    args.output.write_text(value)
    print(hashlib.sha256(value.encode()).hexdigest())


if __name__ == '__main__':
    main()
