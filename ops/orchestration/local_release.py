#!/usr/bin/env python3
"""Measured fixed-source Web+API local release using original host transactions.

Explicit --install authorizes these exact CLI source pins, not arbitrary source
changes. Warm tool/dependency caches are recorded, tests and final JAR are fresh.
Only build units receive a kill deadline: never place the production JVM inside
one of those units, or blindly kill a recoverable installation mid-cutover.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request

from build_storage import require_disk

ROOT = Path(__file__).resolve().parents[2]
API_BUILDER = ROOT / 'ops/orchestration/local_build.py'
WEB_BUILDER = ROOT / 'ops/orchestration/local_web_build.py'
API_HELPER = Path('/usr/local/sbin/cyf-api-flow-deploy')
WEB_HELPER = Path('/usr/local/sbin/cyf-web-flow-deploy')
API_JAR = Path('/home/isp/hosts/cyf/api/cyf-api-kit.jar')
API_RECORD = Path('/home/isp/state/cyf-api-flow/record.json')
WEB_RECORD = Path('/home/isp/state/cyf-web-flow/record.json')
WEB_SITE = Path('/home/isp/hosts/cyf/web/kit')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def fixed_source(path, expected):
    def git(*argv):
        return subprocess.check_output(['git', '-C', str(path)] + list(argv), text=True).strip()
    if (not path.is_absolute() or path.resolve() != path or git('rev-parse', '--show-toplevel') != str(path)
            or git('status', '--porcelain') or git('rev-parse', 'HEAD') != expected):
        raise ValueError('release requires an exact clean physical source root and commit')
    return dict(commit=expected, tree=git('rev-parse', 'HEAD^{tree}'))


def private_json(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def request(route):
    req = urllib.request.Request('http://127.0.0.1:10018' + route, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read(1048576)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(1048576)


def build_seconds(stages):
    """Only executed test/build/package units consume the user build budget."""
    return sum(stage.get('seconds', 0) for stage in stages if stage.get('build'))


def remaining_build_seconds(stages):
    value = 600 - build_seconds(stages)
    if value <= 0:
        raise RuntimeError('test/build/package budget exhausted; do not start another build')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['api-source', 'web-source', 'output', 'evidence-dir', 'cache-home', 'jdk']:
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ['task-id', 'batch-id', 'api-version', 'expected-api-commit', 'expected-web-commit']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--api-regression-arg', action='append', default=[])
    parser.add_argument('--web-regression-test', action='append', default=[])
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    start = time.monotonic()
    os.umask(0o077)
    if not args.install or os.geteuid() != 0:
        raise ValueError('root and explicit --install required; builders alone never deploy')
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_.-]{0,47}', args.batch_id):
        raise ValueError('invalid task-owned unit/build identifier')
    for path in (args.output, args.evidence_dir, args.jdk, args.cache_home):
        if not path.is_absolute() or path != path.resolve():
            raise ValueError('all paths must be physical and absolute')
    if args.output.exists() or args.evidence_dir.exists():
        raise ValueError('fresh output and evidence directories required')
    for forbidden in (args.api_source, args.web_source, Path('/home/isp/hosts'), Path('/opt/cyf/service')):
        if args.output == forbidden or forbidden in args.output.parents:
            raise ValueError('never build into source/production')
    for path in (args.api_source, args.web_source, args.output, args.evidence_dir, args.cache_home):
        require_disk(path)
    args.output.mkdir(mode=0o700, parents=True)
    args.evidence_dir.mkdir(mode=0o700, parents=True)
    result = dict(format='cyf-local-combined-release-v1', batchId=args.batch_id,
                  startedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  status='RUNNING', budgetSeconds=600, stages=[], cacheScope='warm verified tool/dependency/JavaCompile caches; no test/JAR evidence reuse')

    def save():
        result['wallSeconds'] = round(time.monotonic() - start, 3)
        result['buildSeconds'] = round(build_seconds(result['stages']), 3)
        result['under600Seconds'] = build_seconds(result['stages']) <= 600
        private_json(args.output / 'release.json', result)
        private_json(args.evidence_dir / 'release.json', result)

    env = os.environ.copy()
    for key in list(env):
        if key.startswith(('PIPELINE_', 'CI_COMMIT', 'CYF_FLOW_')) or key in ('CI', 'BUILD_NUMBER', 'CYF_API_STARTUP_DIAGNOSTICS', 'CYF_RELEASE_OFFLINE_TEST'):
            env.pop(key, None)

    def run(name, argv, build=False):
        if build:
            budget = remaining_build_seconds(result['stages'])
            argv = ['systemd-run', '--quiet', '--wait', '--pipe', '--collect',
                    '--unit=' + args.batch_id + '-' + name,
                    '--property=RuntimeMaxSec=' + str(int(budget)), '--property=KillMode=control-group'] + argv
        stage = dict(name=name, build=build, startedAfterSeconds=round(time.monotonic() - start, 3), argv=argv)
        result['stages'].append(stage)
        save()
        t = time.monotonic()
        rc = None
        try:
            with (args.evidence_dir / (name + '.log')).open('w') as log:
                rc = subprocess.call(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
        finally:
            stage.update(seconds=time.monotonic() - t, exitCode=rc)
            save()
        if rc:
            raise RuntimeError(name + ' exit ' + str(rc))
        if build and not result['under600Seconds']:
            raise RuntimeError('test/build/package exceeded600 seconds; retain evidence and request exception')

    try:
        result['source'] = dict(api=fixed_source(args.api_source, args.expected_api_commit),
                                web=fixed_source(args.web_source, args.expected_web_commit))
        result['tools'] = {str(p): sha(p) for p in (Path(__file__).resolve(), API_BUILDER, WEB_BUILDER,
                            ROOT / 'ops/orchestration/local-web-build.mjs', API_HELPER, WEB_HELPER, args.jdk / 'bin/java')}
        before_api = sha(API_JAR)
        previous_api = json.loads(API_RECORD.read_text())
        if previous_api['status'] != 'installed' or previous_api['candidate_sha256'] != before_api:
            raise ValueError('API predecessor must be fully installed and hash-bound')
        before_web_record = sha(WEB_RECORD)
        before_web_index = sha(WEB_SITE / 'index.html')
        run('preflight-api-status', ['/usr/local/sbin/cyf-api-kit', 'status'])
        # Match the installed helper shebang and its system CA store. The
        # controller's Python may have a different/missing OpenSSL trust path.
        run('preflight-web-tls', ['/usr/bin/python3', '-I', '-B', '-c',
            "import urllib.request; r=urllib.request.urlopen('https://kit.chaoyoufan.cn/',timeout=10); assert r.status == 200; r.close()"])
        web = args.output / 'web'
        web_command = [sys.executable, '-u', str(WEB_BUILDER), '--source', str(args.web_source),
                       '--output', str(web), '--batch-id', args.batch_id + '-web', '--expected-commit', args.expected_web_commit]
        for test in args.web_regression_test:
            web_command += ['--regression-test', test]
        run('web-build', web_command, build=True)
        web_result = json.loads((web / 'result.json').read_text())
        if web_result['status'] != 'BUILT' or not web_result['sourceUnchanged']:
            raise ValueError('Web build not publishable')
        api = args.output / 'api'
        api_command = [sys.executable, '-u', str(API_BUILDER), '--task-id', args.task_id,
                       '--source', str(args.api_source), '--output', str(api), '--cache-home', str(args.cache_home),
                       '--jdk', str(args.jdk), '--version', args.api_version, '--batch-id', args.batch_id + '-api', '--offline', '--package']
        for item in args.api_regression_arg:
            api_command += ['--regression-arg', item]
        run('api-build', api_command, build=True)
        api_result = json.loads((api / 'result.json').read_text())
        if api_result['status'] != 'BUILT' or api_result['exitCode'] != 0:
            raise ValueError('API build failed')
        p = api_result['package']
        if sha(API_JAR) != before_api or sha(WEB_RECORD) != before_web_record or sha(WEB_SITE / 'index.html') != before_web_index:
            raise ValueError('production changed during build; do not overwrite another owner')
        if any(sha(Path(path)) != digest for path, digest in result['tools'].items()):
            raise ValueError('release tools changed during build')
        descriptor = dict(schema_version=4, source_kind='LOCAL', source=p['identity'], package=p['package'],
                          receipt_sha256=p['receiptSha256'], jar_sha256=p['applicationJarSha256'],
                          expected_previous_sha256=before_api, consumed=False)
        private_json(api / 'install-descriptor.json', descriptor)
        # Outside both timed build cgroups: the new production JVM must survive
        # their teardown. Installer retains its existing durable rollback/health.
        run('api-install', [str(API_HELPER), '--source-local', str(api / 'install-descriptor.json')])
        run('api-status', ['/usr/local/sbin/cyf-api-kit', 'status'])
        status = (args.evidence_dir / 'api-status.log').read_text()
        if 'HEALTH=UP' not in status or 'ARTIFACT_ATTESTATION=MATCH' not in status:
            raise ValueError('API runtime health/attestation mismatch')
        pid = int(re.search(r'^PID=(\d+)$', status, re.M).group(1))
        cmdline = Path('/proc/' + str(pid) + '/cmdline').read_bytes().replace(b'\0', b' ')
        if b'--cyf.startup-tracing.enabled=true' in cmdline or b'=DEBUG' in cmdline or b'=TRACE' in cmdline:
            raise ValueError('temporary startup diagnostics leaked into production JVM')
        api_record = json.loads(API_RECORD.read_text())
        if (api_record['source_kind'] != 'LOCAL' or api_record['status'] != 'installed'
                or api_record['source'] != p['identity'] or sha(API_JAR) != p['applicationJarSha256']
                or sha(api_record['backup']) != before_api):
            raise ValueError('API installed source/artifact/backup mismatch')
        manifest = json.loads((web / 'manifest.json').read_text())
        artifact = web_result['artifact']
        web_descriptor = dict(schema_version=1, source_kind='LOCAL',
            source=dict(manifest['source'], version=manifest['version'], buildId=manifest['buildId']),
            package=dict(path=artifact['path'], size=Path(artifact['path']).stat().st_size, sha256=artifact['sha256']),
            previousIndexSha256=before_web_index, previousRecordSha256=before_web_record)
        private_json(web / 'install-descriptor.json', web_descriptor)
        # Installation uses the original helper recovery/transport limits, never
        # the remaining test/build/package budget. No alternate installer.
        run('web-install', ['/usr/bin/python3', '-I', '-B', '-c',
            "import runpy,sys; m=runpy.run_path('/usr/local/sbin/cyf-web-flow-deploy',run_name='cyf_local_release'); m['deploy_local'](sys.argv[1])",
            str(web / 'install-descriptor.json')])
        web_record = json.loads(WEB_RECORD.read_text())
        if (web_record['status'] != 'online_verified' or web_record['source_kind'] != 'LOCAL'
                or web_record['source'] != web_descriptor['source'] or web_record['artifact_sha256'] != artifact['sha256']):
            raise ValueError('Web source/online verification mismatch')
        t = time.monotonic()
        checks = []
        for route in ['/actuator/health', '/oauth2/jwks', '/agent/scenes/liangshan-hall/snapshot']:
            code, data = request(route)
            if route == '/actuator/health':
                if code != 200 or json.loads(data)['status']['code'] != 'UP':
                    raise ValueError('API health failed')
            elif route == '/oauth2/jwks':
                if code != 200 or not json.loads(data)['keys']:
                    raise ValueError('API signing readiness failed')
            elif code != 401:
                raise ValueError('protected scene accepted an unauthenticated request')
            checks.append(dict(path=route, status=code, bodySha256=hashlib.sha256(data).hexdigest()))
        if fixed_source(args.api_source, args.expected_api_commit) != result['source']['api'] or fixed_source(args.web_source, args.expected_web_commit) != result['source']['web']:
            raise ValueError('source changed during release')
        result['stages'].append(dict(name='final-smoke', seconds=round(time.monotonic() - t, 3)))
        result.update(apiBuild=api_result, webBuild=web_result, apiInstallRecord=api_record,
                      webInstallRecord=web_record, checks=checks, apiPid=pid, startupDiagnostics=False,
                      businessSmokeScope='real scene route auth refusal + signing readiness; no authenticated user mutation',
                      status='RELEASED', endedAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except BaseException as exc:
        result.update(status='FAIL', error=type(exc).__name__ + ': ' + str(exc), endedAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
        raise
    finally:
        # Preserve real inputs, logs, XML and proofs outside rebuildable packages.
        for component in ('api', 'web'):
            folder = args.output / component
            if not folder.exists():
                continue
            dest = args.evidence_dir / component
            dest.mkdir(exist_ok=True)
            for name in ('result.json', 'inputs.json', 'gradle.log', 'manifest.json', 'dependencies.log', 'tests.log', 'build.log'):
                if (folder / name).is_file():
                    shutil.copyfile(folder / name, dest / name)
            if component == 'api' and (folder / 'build').exists():
                for name in ('build-evidence.json', 'local-bootjar-proof.json', 'opencv-resolved.json'):
                    if (folder / 'build' / name).is_file():
                        shutil.copyfile(folder / 'build' / name, dest / name)
                for report in (folder / 'build' / 'jia').glob('*/test-results/*/TEST-*.xml'):
                    target = dest / report.relative_to(folder / 'build' / 'jia')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(report, target)
            if component == 'web' and (folder / 'test-reports/mochawesome.json').exists():
                shutil.copyfile(folder / 'test-reports/mochawesome.json', dest / 'test-report.json')
        save()
    print(json.dumps(dict(status=result['status'], wallSeconds=result['wallSeconds'],
                         buildSeconds=result['buildSeconds'], under600Seconds=result['under600Seconds'], evidence=str(args.evidence_dir / 'release.json')), indent=2))
    return 0 if result['under600Seconds'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
