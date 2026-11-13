#!/usr/bin/env python3
"""Fixed-source local API build using the existing Gradle orchestrator.

Fast release baseline, NOT an all-feature regression certificate or installer.
Change-specific regressions remain explicit inputs; no failed run is reusable.
Run in a task-owned systemd unit with RuntimeMaxSec=600 / KillMode=control-group
so a deadline stops only this build and its own Gradle/test descendants.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

from build_storage import require_disk, build_environment

ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = ROOT / 'ops/orchestration/cyf_orchestrator.py'
LOCAL_INIT = Path(__file__).with_name('local-build.init.gradle')
METADATA_INIT = ROOT / 'ops/ci/aliyun-flow/local-release-metadata.init.gradle'
PRODUCER = ROOT / 'ops/ci/aliyun-flow/auto/package-api-local.py'
GRADLE = Path('/home/isp/apps/gradle/9.3.1/bin/gradle')
# Packaging boundaries and real HTTP security must not disappear from fast builds.
BASELINE = [
    ':agent:jia-agent-service:localReleaseBaseline', '--tests',
    'cn.jia.agent.security.AgentRuntimeSecurityIntegrationTest',
    ':starter:localReleaseBaseline',
    '--tests', 'cn.jia.diagnostics.StartupTimelineBootTest',
    '--tests', 'cn.jia.starter.AuthFormTransportTest',
    '--tests', 'cn.jia.config.ApiPerformanceMetricsConfigTest',
    '--tests', 'cn.jia.config.SmsEmailRuntimeClasspathTest',
    '--tests', 'cn.jia.config.ElasticsearchProductionHealthIsolationTest',
    ':starter:publicArtifactVerifierTest',
    ':starter:poiProductionRuntimeClasspathTest',
    ':validateLayering', ':starter:bootJar',
]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source)] + list(args),
                                   universal_newlines=True).strip()


def fixed_source(source):
    source = Path(source)
    if not source.is_absolute() or source != source.resolve():
        raise ValueError('source must be an absolute physical path')
    if git(source, 'rev-parse', '--show-toplevel') != str(source):
        raise ValueError('source must be the exact repository root')
    if git(source, 'status', '--porcelain'):
        raise ValueError('dirty source is not a release candidate')
    return {'commit': git(source, 'rev-parse', 'HEAD'),
            'tree': git(source, 'rev-parse', 'HEAD^{tree}')}


def build_command(source, output, home, jdk, identity, task_id, regressions=(), offline=False):
    gradle = [str(GRADLE), '--no-daemon', '--max-workers=2', '--parallel', '--build-cache',
              '--console=plain', '--stacktrace',
              '-Dorg.gradle.jvmargs=-Xmx768m -XX:MaxMetaspaceSize=384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1',
              '--init-script', str(LOCAL_INIT), '--init-script', str(METADATA_INIT),
              '--project-cache-dir', str(home / 'project-cache')]
    if offline:
        gradle.append('--offline')
    # Fail fast, no --continue; keep the exact same regression argv in the evidence.
    gradle += list(regressions) + BASELINE
    return [sys.executable, '-u', str(ORCHESTRATOR), 'gradle', '--heavy',
            '--cwd', str(source), '--tree-sha', identity['tree'],
            '--selector', 'local-fast-baseline-v2-source-slice', '--fixture-digest', 'FIXTURE_DIGEST',
            '--dependency-cache-home', str(home), '--artifact', str(output / 'gradle.log'),
            task_id, '--'] + gradle


def save(path, record):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    os.replace(str(temporary), str(path))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def export_package(args, command, identity, fixture):
    """Reuse the original producer, preserving exact tests/proof/provenance."""
    spec = importlib.util.spec_from_file_location('cyf_local_producer', PRODUCER)
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    build = args.output / 'build'
    proof_path = build / 'local-bootjar-proof.json'
    proof = json.loads(proof_path.read_text())
    clean = {'commit': identity['commit'], 'tree': identity['tree'], 'clean': True}
    tasks = {':agent:jia-agent-service:localReleaseBaseline': ('agent__jia-agent-service', 'localReleaseBaseline'),
             ':starter:localReleaseBaseline': ('starter', 'localReleaseBaseline'),
             ':starter:publicArtifactVerifierTest': ('starter', 'publicArtifactVerifierTest'),
             ':starter:poiProductionRuntimeClasspathTest': ('starter', 'poiProductionRuntimeClasspathTest')}
    # Additional requested Test tasks must also have fresh XML; never drop them.
    raw_argv = command[command.index('--') + 1:]
    for item in args.regression_arg:
        if item.startswith(':') and item not in tasks and not item.startswith(':validate'):
            parts = item.strip(':').split(':')
            tasks[item] = ('__'.join(parts[:-1]), parts[-1])
    tests = []
    for task, (project, name) in tasks.items():
        reports = sorted((build / 'jia' / project / 'test-results' / name).glob('TEST-*.xml'))
        if not reports:
            raise ValueError('missing fresh XML for ' + task)
        tests.append({'task': task, 'selector': 'local-fast-baseline-v2-source-slice',
                      'fixtureSha256': fixture, 'reports': [producer.record(p) for p in reports]})
    inputs = [args.source / 'settings.gradle', args.source / 'starter/build.gradle',
              LOCAL_INIT, METADATA_INIT, Path(__file__).resolve()]
    log = build / 'gradle-execution.log'
    # Evidence records must live below the build root, not point at an external
    # mutable console. Preserve original bytes exactly (including task timings).
    log.write_bytes((args.output / 'gradle.log').read_bytes())
    evidence = {'format': 'cyf-api-local-build-evidence-v1', 'identity': proof['identity'],
        'sourceRoot': str(args.source), 'buildRoot': str(build),
        'sourceBefore': clean, 'sourceAfter': clean,
        'invocation': {'argv': raw_argv, 'exitCode': 0, 'cacheHit': False,
            'log': producer.record(log), 'selector': 'local-fast-baseline-v2-source-slice',
            'fixtureSha256': fixture, 'inputs': [producer.record(p) for p in inputs]},
        'tests': tests, 'validateLayering': {'task': ':validateLayering'},
        'bootJar': {'task': ':starter:bootJar', 'proof': producer.record(proof_path)},
        'opencv': producer.record(build / 'opencv-resolved.json')}
    evidence_path = build / 'build-evidence.json'
    evidence_path.write_bytes(producer.canonical(evidence))
    output = args.output / 'package'
    output.mkdir(mode=0o700)
    values = argparse.Namespace(opt_in=True, version=args.version, build_id=args.batch_id,
        commit=identity['commit'], tree=identity['tree'], source_root=str(args.source),
        build_root=str(build), evidence=str(evidence_path),
        evidence_sha256=digest(evidence_path), output=str(output / 'api.tar'))
    return producer.produce(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache-home', type=Path, required=True)
    parser.add_argument('--jdk', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--batch-id', required=True)
    parser.add_argument('--regression-arg', action='append', default=[])
    parser.add_argument('--package', action='store_true', help='export the original five-member LOCAL package after all verification succeeds')
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--offline', action='store_true', help='use only already resolved verified dependency cache; missing dependencies fail, never silently fetch')
    args = parser.parse_args()
    start = time.monotonic()
    for path in (args.source, args.output, args.cache_home):
        require_disk(path)
    identity = fixed_source(args.source)
    for path in (args.output, args.cache_home, args.jdk):
        if not path.is_absolute() or path != path.resolve():
            raise ValueError('output/cache/JDK must be physical absolute paths')
    forbidden = [Path('/home/isp/hosts'), Path('/home/isp/apps/cyf-agent-runtime-v1'),
                 Path('/opt/cyf/service')]
    if any(args.output == p or p in args.output.parents for p in forbidden):
        raise ValueError('never build inside a production installation tree')
    if args.output == args.source or args.source in args.output.parents:
        raise ValueError('outputs must be outside the source tree')
    if args.output.exists():
        raise ValueError('fresh per-batch output is required')
    if args.output == args.cache_home or args.cache_home in args.output.parents:
        raise ValueError('output must be independent of the dependency home')
    # Read actual build files before any Gradle invocation, preserving their binding.
    builds = {str(p.relative_to(args.source)): digest(p)
              for p in args.source.rglob('build.gradle') if '.git' not in p.parts}
    java = subprocess.check_output([str(args.jdk / 'bin/java'), '-version'],
                                   stderr=subprocess.STDOUT, universal_newlines=True)
    if '21.0.11' not in java or 'Dragonwell' not in java:
        raise ValueError('use the verified Flow Dragonwell 21 toolchain')
    command = build_command(args.source, args.output, args.cache_home, args.jdk,
                            identity, args.task_id, args.regression_arg, args.offline)
    binding = {'format': 'cyf-local-fast-build-input-v1', 'source': identity,
               'batchId': args.batch_id, 'version': args.version,
               'javaVersion': java, 'javaSha256': digest(args.jdk / 'bin/java'),
               'buildFiles': builds, 'command': command,
               'tools': {str(p): digest(p) for p in
                         (Path(__file__).resolve(), Path(__file__).with_name('build_storage.py'), LOCAL_INIT, METADATA_INIT, ORCHESTRATOR, PRODUCER)},
               'cacheHome': str(args.cache_home),
               'scope': 'fast release baseline plus supplied regressions; not full suite; not deployment'}
    if args.plan_only:
        print(json.dumps(binding, ensure_ascii=False, indent=2))
        return 0
    args.output.mkdir(mode=0o700, parents=True)
    build_root = args.output / 'build'
    build_root.mkdir(mode=0o700)
    save(args.output / 'inputs.json', binding)
    fixture = digest(args.output / 'inputs.json')
    command[command.index('FIXTURE_DIGEST')] = fixture
    env = build_environment(args.output)
    for key in list(env):
        if key.startswith(('PIPELINE_', 'CI_COMMIT', 'CYF_FLOW_')) or key in (
                'CI', 'BUILD_NUMBER', 'GRADLE_USER_HOME'):
            env.pop(key, None)
    spec = importlib.util.spec_from_file_location('cyf_history',
             ROOT / 'ops/orchestration/execution_history_check.py')
    history = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(history)
    env.update(history.credentials(type('Credentials', (),
               {'credentials_init': Path('/root/.gradle/init.gradle')})()))
    env.update(JAVA_HOME=str(args.jdk),
               PATH=str(args.jdk / 'bin') + ':/home/isp/apps/node/bin:' + env.get('PATH', ''),
               CYF_LOCAL_GRADLE_ACTIVE='1', CYF_LOCAL_RELEASE_OPT_IN='1',
               CYF_LOCAL_BUILD_ROOT=str(build_root),
               CYF_LOCAL_RELEASE_SOURCE_ROOT=str(args.source),
               CYF_LOCAL_RELEASE_BUILD_ROOT=str(build_root),
               CYF_LOCAL_RELEASE_VERSION=args.version,
               CYF_LOCAL_RELEASE_BUILD_ID=args.batch_id,
               CYF_LOCAL_RELEASE_COMMIT=identity['commit'],
               CYF_LOCAL_RELEASE_TREE=identity['tree'])
    result = {'startedAt': now(), 'status': 'RUNNING', 'source': identity,
              'fixtureDigest': fixture, 'command': command, 'publishable': False}
    save(args.output / 'result.json', result)
    def stopped(signum, frame):
        result.update(status='STOPPED_BEFORE_COMPLETION', endedAt=now(),
                      wallSeconds=round(time.monotonic() - start, 3),
                      signal=signum, publishable=False)
        save(args.output / 'result.json', result)
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, stopped)
    signal.signal(signal.SIGINT, stopped)
    with (args.output / 'gradle.log').open('w') as log:
        rc = subprocess.call(command, cwd=str(args.source), env=env,
                             stdout=log, stderr=subprocess.STDOUT)
    unchanged = fixed_source(args.source) == identity
    proof = build_root / 'local-bootjar-proof.json'
    result.update(endedAt=now(), wallSeconds=round(time.monotonic() - start, 3),
                  exitCode=rc, sourceUnchanged=unchanged,
                  status='BUILT' if rc == 0 and unchanged and proof.is_file() else 'FAIL')
    if proof.is_file():
        record = json.loads(proof.read_text())
        jar = Path(record['jar']['path'])
        actual = digest(jar)
        result['artifact'] = {'path': str(jar), 'sha256': actual,
                              'proofSha256': digest(proof)}
        if actual != record['jar']['sha256']:
            result['status'] = 'FAIL_DIGEST'
    if result['status'] == 'BUILT' and args.package:
        try:
            package_start = time.monotonic()
            result['package'] = export_package(args, command, identity, fixture)
            result['packageSeconds'] = round(time.monotonic() - package_start, 3)
        except Exception as exc:
            result.update(status='FAIL_PACKAGING', packagingError=type(exc).__name__ + ': ' + str(exc))
        result.update(endedAt=now(), wallSeconds=round(time.monotonic() - start, 3))
    save(args.output / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'BUILT' else 1


if __name__ == '__main__':
    raise SystemExit(main())
