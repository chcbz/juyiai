#!/usr/bin/env python3
"""Package this successful Flow build for the existing transactional installer.

Call only after the required Gradle command exits zero. ticket_sha256 is a
legacy wire-field for a deterministic run identity, not an approval ticket.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


REQUIRED_MAIL_RUNTIME_CLASSES = frozenset((
    'javax/mail/MessagingException.class',
    'javax/mail/Session.class',
    'javax/mail/Transport.class',
    'com/sun/mail/smtp/SMTPTransport.class',
    'javax/activation/DataHandler.class',
))


def verify_mail_runtime(jar):
    """Check the shipped bootJar, not the broader Gradle test classpath."""
    missing = set(REQUIRED_MAIL_RUNTIME_CLASSES)
    try:
        with zipfile.ZipFile(str(jar)) as boot:
            for member in boot.infolist():
                if not member.filename.startswith('BOOT-INF/lib/') or not member.filename.endswith('.jar'):
                    continue
                with zipfile.ZipFile(io.BytesIO(boot.read(member))) as dependency:
                    missing.difference_update(dependency.namelist())
                if not missing:
                    break
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise SystemExit('invalid bootJar runtime archive: ' + type(exc).__name__)
    if missing:
        raise SystemExit('bootJar missing required mail runtime classes: ' + ', '.join(sorted(missing)))
    return sorted(REQUIRED_MAIL_RUNTIME_CLASSES)


def main():
    root = Path.cwd()
    env = os.environ
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}']).decode().strip()
    if (env.get('PIPELINE_ID') != '5260799' or env.get('CI_COMMIT_REF_NAME') != 'develop'
            or commit != env.get('CI_COMMIT_SHA') or not re.fullmatch('[0-9a-f]{40,64}', commit)
            or not re.fullmatch('[1-9][0-9]*', env.get('BUILD_NUMBER', ''))):
        raise SystemExit('unexpected Flow source/run identity')
    # Both checks are enforced in the shell, before and after Gradle; repeat the
    # latter here. Untracked build outputs are not part of the tracked source.
    if env.get('CYF_SOURCE_CLEAN_BEFORE') != '1':
        raise SystemExit('missing successful pre-build source check')
    subprocess.check_call(['git', 'diff', '--exit-code', 'HEAD', '--'])
    build = root / '_cyf_flow_build'
    jars = [p for p in (build / 'jia/starter/libs').glob('*.jar') if not p.name.endswith('-plain.jar')]
    provenance = build / 'opencv-resolved.json'
    if len(jars) != 1 or any(p.is_symlink() or not p.is_file() for p in jars + [provenance]):
        raise SystemExit('expected one bootJar and OpenCV provenance')
    prov = json.loads(provenance.read_text())
    if (prov.get('jar_sha256') != '323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4'
            or prov.get('jar_size') != 722802):
        raise SystemExit('unexpected private OpenCV artifact')
    mail_runtime = verify_mail_runtime(jars[0])
    print('CYF_BOOTJAR_MAIL_RUNTIME ' + json.dumps(mail_runtime))
    out = root / '_cyf_api_flow_export'
    out.mkdir(mode=0o700)  # fail rather than reuse stale output
    flow = dict(organization_id='5fb7d76ee6f9d07f148529c7', pipeline_id='5260799',
                job_id='cloud_ci.api_ci', run_id=env['BUILD_NUMBER'], source_tip_sha=commit)
    source = dict(branch='develop', commit_sha=commit, tree_sha=tree, clean_before=True, clean_after=True)
    records = []
    for kind, src, name in [('application_jar', jars[0], 'application.jar'),
                             ('dependency_provenance', provenance, 'dependency.provenance.json')]:
        target = out / name
        shutil.copyfile(str(src), str(target))
        records.append(dict(kind=kind, path=name, sha256=digest(target), size=target.stat().st_size))
    identity = hashlib.sha256(canonical(dict(flow=flow, source=source))).hexdigest()
    receipt = dict(schema_version=1, status='success', gradle_exit_code=0, bridge_exit_code=0,
                   ticket_sha256=identity, flow=flow, source=source, files=records)
    data = canonical(receipt)
    (out / 'receipt.json').write_bytes(data)
    receipt_sha = hashlib.sha256(data).hexdigest()
    (out / 'application.metadata.json').write_bytes(canonical(dict(
        schema_version=1, receipt_sha256=receipt_sha, flow=flow, source=source,
        application_jar=records[0], dependency_provenance=records[1])))
    (out / 'application.sidecar.json').write_bytes(canonical(dict(
        schema_version=1, receipt_sha256=receipt_sha, flow=flow,
        sha256=records[0]['sha256'], size=records[0]['size'])))
    print('CYF_API_ARTIFACT ' + json.dumps(dict(flow=flow, source=source,
          jar_sha256=records[0]['sha256'], receipt_sha256=receipt_sha), sort_keys=True))


if __name__ == '__main__':
    main()
