#!/usr/bin/env python3
"""One scoped history check; no task claiming, release, installation or retry loop.

Python 3.6+ / standard library. Uses the existing orchestrator for all Gradle,
locks, evidence and failure attribution. --check-only never writes evidence.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ':agent:jia-agent-service:executionHistoryHttp validateLayering'
FIXTURE_DIR = 'specs/juyiting-execution-recovery/contract-pilot'
TEST_NAME = 'cn.jia.agent.contract.ExecutionHistoryHttpContractTest'
LIMITS = ['No production OAuth/full security configuration', 'No rendered browser UI',
          'No formal frontend Flow, production build or deployment',
          'Installed frontend packages fingerprinted, not a clean-install/provenance attestation']


class CheckError(Exception):
    pass


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest_json(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def tree_digest(root):
    """Hash package/distribution bytes; no timestamps, worktree or run paths in key."""
    entries = {}
    for directory, dirs, files in os.walk(str(root), followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in ('node_modules', '.git'))
        for name in sorted(files):
            path = Path(directory) / name
            entries[str(path.relative_to(root))] = digest_file(path)
        if any((Path(directory) / d).is_symlink() for d in dirs):
            raise CheckError('Unsupported linked subdirectory in fingerprinted input: ' + str(root))
    if not entries:
        raise CheckError('Empty dependency/tool distribution: ' + str(root))
    return digest_json(entries)


def clean_env():
    # Do not inherit Node/Java injection flags, stale CYF_* inputs or Flow identity.
    env = {key: os.environ[key] for key in
           ('HOME', 'USER', 'LOGNAME', 'PATH', 'LANG', 'LC_ALL', 'TZ', 'TMPDIR') if key in os.environ}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1')
    return env


def capture(command, data=None):
    result = subprocess.run([str(x) for x in command], input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=clean_env())
    if result.returncode:
        # Raw tools' stderr belongs in logs, not in an uncontrolled console dump.
        text = (result.stderr or result.stdout).decode('utf-8', errors='replace')
        raise CheckError(first_failure(text))
    return result.stdout.decode('utf-8').strip()


def git(repo, *args):
    return capture(['git', '-c', 'core.fsmonitor=false', '-C', repo] + list(args))


def source_identity(repo):
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise CheckError('Supply the repository/worktree root: ' + str(repo))
    if git(repo, 'status', '--porcelain', '--untracked-files=normal'):
        raise CheckError('Dirty source; preserve edits and choose a clean fixed worktree: ' + str(repo))
    return {'commit': git(repo, 'rev-parse', 'HEAD'), 'tree': git(repo, 'rev-parse', 'HEAD^{tree}')}


def installed_packages(web, browser=False):
    """The pinned pilot imports Vue and consola; include their dependency closure."""
    def resolve_package(start, name):
        if not re.match(r'^(?:@[\w.-]+/)?[\w.-]+$', name):
            raise CheckError('Invalid dependency name')
        for parent in [start] + list(start.parents):
            candidate = parent / 'node_modules' / name
            if (candidate / 'package.json').is_file():
                return candidate.resolve()
        raise CheckError('Missing installed frontend dependency: ' + name + '; no auto-install')
    pending = [resolve_package(web, name) for name in (('vue', 'consola', 'vite', '@vitejs/plugin-vue', 'ws') if browser else ('vue', 'consola'))]
    seen, packages = set(), []
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        package = json.loads((path / 'package.json').read_text())
        packages.append({'name': package['name'], 'version': package['version'], 'sha256': tree_digest(path)})
        for name in sorted(package.get('dependencies', {})):
            pending.append(resolve_package(path, name))
        if browser:
            for name in sorted(package.get('optionalDependencies', {})):
                try:
                    pending.append(resolve_package(path, name))
                except CheckError:
                    pass  # Platform-specific optional packages may be absent.
    return sorted(packages, key=lambda p: (p['name'], p['version'], p['sha256']))


def local_init(api):
    text = (api / 'ops/ci/aliyun-flow/cold-init.gradle').read_text()
    for old, new in [('CYF_FLOW_GRADLE_ACTIVE', 'CYF_LOCAL_GRADLE_ACTIVE'),
                     ('CYF_FLOW_BUILD_ROOT', 'CYF_LOCAL_BUILD_ROOT'),
                     ('must be set by flow_remote', 'must be set by local verifier')]:
        if old not in text:
            raise CheckError('Local init source changed; review adaptation before running')
        text = text.replace(old, new)
    # Keep dependency integrity/auth/child secret stripping unchanged. Bind external
    # tool/dependency inputs and output receipt so Gradle cannot skip a missing run.
    return text + '''\ngradle.beforeProject { project ->
    project.tasks.withType(org.gradle.api.tasks.testing.Test).configureEach { test ->
        if (test.name == 'executionHistoryHttp') {
            test.inputs.property('cyfHistoryInputDigest', System.getenv('CYF_HISTORY_INPUT_DIGEST'))
            test.outputs.file(System.getenv('CYF_HISTORY_RESULT'))
        }
    }
}
'''


def load_orchestrator(path):
    spec = importlib.util.spec_from_file_location('history_check_orchestrator', str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def precheck(args, orchestrator):
    api, web = source_identity(args.api), source_identity(args.web)
    item = orchestrator.task(orchestrator.load_ledger(), args.task_id)
    if item['exact_sha_tree'] != {'commit_sha': api['commit'], 'tree_sha': api['tree']}:
        raise CheckError('Task/API commit/tree mismatch; confirm baseline explicitly, no automatic ledger change')
    browser = getattr(args, 'browser', False)
    files = {name: (args.fixtures / name).read_bytes() for name in
             (('execution-history.json', 'check-http.mjs', 'check-consumer.mjs', 'check-browser.mjs', 'browser-entry.js') if browser else ('execution-history.json', 'check-http.mjs', 'check-consumer.mjs'))}
    fixture = json.loads(files['execution-history.json'].decode())
    if fixture.get('schemaVersion') != 2 or fixture.get('source', {}).get('webCommit') != web['commit']:
        raise CheckError('Shared contract schema/Web commit mismatch')
    cases = {c['id'] for c in fixture['cases']}
    if cases != {'empty', 'first-page', 'last-page', 'unpaired-cursor', 'unavailable'}:
        raise CheckError('Shared contract cases changed; update scoped verifier explicitly')
    for name in (n for n in files if n.endswith(('.mjs', '.js'))):
        capture([args.node, '--input-type=module', '--check'], files[name])
    for name in ('build.gradle', 'agent/jia-agent-service/build.gradle'):
        content = (args.api / name).read_text()  # Read current build definition before Gradle.
        if name.startswith('agent/') and "tasks.register('executionHistoryHttp', Test)" not in content:
            raise CheckError('API candidate lacks the dedicated executionHistoryHttp Test task')
    init = local_init(args.api)
    for tool in (args.node, args.mysqld, args.gradle, args.java_home / 'bin/java'):
        if not tool.is_file() or not os.access(str(tool), os.X_OK):
            raise CheckError('Missing approved executable: ' + str(tool))
    gradle_home = args.gradle.resolve().parents[1]
    config = {}
    for path in [args.gradle_user_home / 'gradle.properties', args.gradle_user_home / 'init.gradle',
                 args.gradle_user_home / 'init.gradle.kts'] + sorted((args.gradle_user_home / 'init.d').glob('*')):
        if path.is_file():
            config[str(path.relative_to(args.gradle_user_home))] = digest_file(path)
    identity = {'schema': 1, 'apiTree': api['tree'], 'web': web, 'selector': SELECTOR,
                'fixtures': {name: digest_bytes(data) for name, data in files.items()},
                'runner': digest_file(Path(__file__)), 'orchestrator': digest_file(args.orchestrator),
                'localInit': digest_bytes(init.encode()), 'installedPackages': installed_packages(args.web, True) if browser else installed_packages(args.web),
                'toolchain': {'node': digest_file(args.node), 'mysqld': digest_file(args.mysqld),
                              'java': digest_file(args.java_home / 'bin/java'),
                              'javaModules': digest_file(args.java_home / 'lib/modules'),
                              'javaRelease': digest_file(args.java_home / 'release'),
                              'gradleLauncher': digest_file(args.gradle),
                              'gradleLibraries': tree_digest(gradle_home / 'lib')},
                'gradleUserConfig': config}
    if browser:
        if not args.chrome.is_file():
            raise CheckError('Missing explicit browser executable; no auto-install')
        identity['browser'] = {'executable': digest_file(args.chrome), 'distribution': tree_digest(args.chrome.parent)}
    baseline = {'ref': args.baseline, 'freshness': 'local_ref_only_no_fetch'}
    try:
        base = git(args.api, 'rev-parse', '--verify', '--end-of-options', args.baseline + '^{commit}')
        counts = git(args.api, 'rev-list', '--left-right', '--count', base + '...' + api['commit']).split()
        baseline.update(commit=base, baselineOnly=int(counts[0]), candidateOnly=int(counts[1]))
    except CheckError:
        baseline['status'] = 'unavailable; inspect baseline before integration'
    return {'api': api, 'web': web, 'identity': identity, 'fixtureDigest': digest_json(identity),
            'baseline': baseline, 'files': files, 'init': init}


def first_failure(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for marker in ('SyntaxError:', 'error:', 'AssertionFailedError:', 'Caused by:',
                   'Execution failed for task', 'What went wrong:', 'denied:', 'FAILURE:'):
        for index, line in enumerate(lines):
            if marker in line:
                if marker == 'What went wrong:' and index + 1 < len(lines):
                    line = lines[index + 1]
                return line[:600]
    return (lines[-1] if lines else 'Process failed without diagnostic output')[:600]


def validate_result(result, junit, prepared):
    frontend = result.get('frontendOutput', {})
    if isinstance(frontend, str):
        frontend = json.loads(frontend)
    expected = prepared['identity']['fixtures']['execution-history.json']
    if (result.get('status') != 'PASS' or result.get('fixtureSha256') != expected or
            result.get('productionTouched') is not False or result.get('forbiddenCalls') != 0 or
            result.get('rowSnapshotUnchanged') is not True or result.get('realMapperQueries', 0) <= 0 or
            frontend.get('status') != 'PASS' or frontend.get('webCommit') != prepared['web']['commit'] or
            frontend.get('fixtureSha256') != expected or frontend.get('assertions', 0) < 17 or
            frontend.get('requests', 0) < 8):
        raise CheckError('Incomplete or mismatched real HTTP/SQL/frontend result; exit zero is not acceptance')
    if 'browser' in prepared['identity']:
        browser = frontend.get('browser') or {}
        if browser.get('status') != 'PASS' or len(browser.get('checks', [])) < 29 or len(browser.get('requests', [])) < 15:
            raise CheckError('Missing complete rendered browser evidence')
        expected_images = {'browser-desktop.png', 'browser-mobile.png', 'browser-landscape.png'}
        if set(browser.get('screenshots', {})) != expected_images:
            raise CheckError('Missing browser viewport evidence')
        for name, sha in browser['screenshots'].items():
            if digest_file(Path(junit).parent / name) != sha:
                raise CheckError('Browser screenshot digest mismatch')
    suite = ET.parse(str(junit)).getroot()
    if (suite.get('name') != TEST_NAME or suite.get('tests') != '1' or
            any(suite.get(name) != '0' for name in ('failures', 'errors', 'skipped'))):
        raise CheckError('Missing/passing-only JUnit contract not satisfied')
    return frontend


def cached_summary(orchestrator, key, prepared):
    record = orchestrator.load_json(orchestrator.EVIDENCE_PATH, {'records': {}}).get('records', {}).get(key)
    if not record or record.get('result') != 'accepted':
        return None
    try:
        path = Path(record['artifact'])
        summary = json.loads(path.read_text())
        if (record['fixture_digest'] != prepared['fixtureDigest'] or record['tree_sha'] != prepared['api']['tree'] or
                record['selector'] != SELECTOR or summary['status'] != 'PASS' or
                summary['fixtureDigest'] != prepared['fixtureDigest'] or
                summary['identity'] != prepared['identity']):
            raise ValueError('identity mismatch')
        required = {'result.json', 'junit.xml', 'gradle.log', 'consumer.log', 'manifest.json'}
        if 'browser' in prepared['identity']:
            required |= {'browser-desktop.png', 'browser-mobile.png', 'browser-landscape.png'}
        if set(summary['artifacts']) != required:
            raise ValueError('missing evidence artifacts')
        for name, digest in summary['artifacts'].items():
            if digest_file(path.parent / name) != digest:
                raise ValueError('artifact changed')
        validate_result(json.loads((path.parent / 'result.json').read_text()), path.parent / 'junit.xml', prepared)
        return dict(summary, status='REUSED', reusedFrom=str(path), currentApi=prepared['api'])
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, CheckError):
        raise CheckError('Accepted evidence missing/tampered/incomplete; restore the original bundle or explicitly invalidate it through orchestrator before rerunning')


def credentials(args):
    values = {key: os.environ.get(key, '') for key in ('CYF_MAVEN_USERNAME', 'CYF_MAVEN_PASSWORD')}
    if all(values.values()):
        return values
    if not args.credentials_init:
        raise CheckError('Set CYF_MAVEN_USERNAME/PASSWORD, or explicitly select --credentials-init; no automatic global credential read')
    content = args.credentials_init.read_text()
    for key in ('username', 'password'):
        matches = re.findall(r'\b' + key + r'\s*(?:=\s*)?[\'"]([^\'"]+)[\'"]', content)
        if not matches or len(set(matches)) != 1:
            raise CheckError('Credential init is not unambiguous; use environment variables instead')
        values['CYF_MAVEN_' + key.upper()] = matches[0]
    return values


def guard(args, orchestrator, prepared):
    item = orchestrator.gradle_guard(orchestrator.load_ledger(), argparse.Namespace(
        task_id=args.task_id, tree_sha=prepared['api']['tree']))
    orchestrator.verify_exact_worktree(args.api, item, prepared['api']['tree'])
    return item


def attribute_failure(args, orchestrator, prepared, log, cause):
    # Never overwrite a task that changed owner, gate, or candidate during a run.
    current = orchestrator.task(orchestrator.load_ledger(), args.task_id)
    if current != prepared['taskAtStart']:
        return
    with log.open('a') as stream, redirect_stdout(stream), redirect_stderr(stream):
        orchestrator.cmd_fail(argparse.Namespace(task_id=args.task_id, category='history_verification',
            summary='Scoped verifier failed; no automatic retry', evidence=str(log),
            root_cause='First diagnostic (Owner must confirm): ' + cause,
            remediation='Inspect the evidence, correct inputs/cause, then use orchestrator transition or authorize-remediation; rerun only after attribution'))


def execute(args, orchestrator, prepared, started):
    key = orchestrator.evidence_key(prepared['api']['tree'], SELECTOR, prepared['fixtureDigest'])
    if source_identity(args.api) != prepared['api'] or source_identity(args.web) != prepared['web']:
        raise CheckError('Source changed during precheck; no cached result or Gradle execution')
    cached = cached_summary(orchestrator, key, prepared)
    if cached:
        cached['elapsedSeconds'] = round(time.monotonic() - started, 3)
        return cached
    prepared['taskAtStart'] = json.loads(json.dumps(guard(args, orchestrator, prepared)))
    secrets = credentials(args)  # Only a cache miss needs credentials.
    args.evidence_root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='run-', dir=str(args.evidence_root)))
    log = run / 'gradle.log'
    manifest = {key: prepared[key] for key in ('api', 'web', 'identity', 'fixtureDigest', 'baseline')}
    orchestrator.atomic_write(run / 'manifest.json', manifest, default_mode=0o600)
    for name, data in prepared['files'].items():
        (run / name).write_bytes(data)
    (run / 'local-init.gradle').write_text(prepared['init'])
    try:
        with (run / 'consumer.log').open('w') as output:
            cheap = subprocess.run([str(args.node), str(run / 'check-consumer.mjs'), str(args.web)],
                                   env=clean_env(), stdout=output, stderr=subprocess.STDOUT)
        if cheap.returncode:
            raise CheckError(first_failure((run / 'consumer.log').read_text()))
        feedback_seconds = round(time.monotonic() - started, 3)
        build = args.evidence_root / 'build' / prepared['api']['tree']
        build.mkdir(parents=True, exist_ok=True)
        env = clean_env()
        env.update(secrets)
        env.update(JAVA_HOME=str(args.java_home), GRADLE_USER_HOME=str(args.gradle_user_home),
            CYF_LOCAL_GRADLE_ACTIVE='1', CYF_LOCAL_BUILD_ROOT=str(build),
            CYF_HISTORY_CONTRACT=str(run / 'execution-history.json'),
            CYF_HISTORY_NODE_SCRIPT=str(run / 'check-http.mjs'), CYF_HISTORY_WEB=str(args.web),
            CYF_HISTORY_WEB_COMMIT=prepared['web']['commit'], CYF_HISTORY_MYSQLD=str(args.mysqld),
            CYF_HISTORY_NODE=str(args.node), CYF_HISTORY_RESULT=str(run / 'result.json'),
            CYF_HISTORY_INPUT_DIGEST=prepared['fixtureDigest'])
        if getattr(args, 'browser', False):
            env.update(CYF_HISTORY_BROWSER='1', CHROME_PATH=str(args.chrome))
        command = [sys.executable, '-B', str(args.orchestrator), 'gradle', '--cwd', str(args.api),
            '--tree-sha', prepared['api']['tree'], '--selector', SELECTOR, '--fixture-digest',
            prepared['fixtureDigest'], '--artifact', str(run / 'summary.json'), args.task_id, '--',
            str(args.gradle), '-I', str(run / 'local-init.gradle')] + SELECTOR.split() + ['--no-daemon', '--console=plain']
        with log.open('w') as output:
            result = subprocess.run(command, env=env, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            raise CheckError(first_failure(log.read_text()))
        xmls = list(build.glob('*/agent__jia-agent-service/test-results/executionHistoryHttp/TEST-' + TEST_NAME + '.xml'))
        if len(xmls) != 1:
            raise CheckError('Expected exactly one real contract JUnit report')
        (run / 'junit.xml').write_bytes(xmls[0].read_bytes())
        frontend = validate_result(json.loads((run / 'result.json').read_text()), run / 'junit.xml', prepared)
        # Do not accept source/dependency mutations while the build was waiting/running.
        after = precheck(args, orchestrator)
        if after['identity'] != prepared['identity'] or after['api'] != prepared['api']:
            raise CheckError('Inputs changed during verification; no accepted evidence')
        text = log.read_text()
        if 'BUILD SUCCESSFUL' not in text or '> Task :validateLayering' not in text:
            raise CheckError('Missing successful Gradle/validateLayering evidence')
        extra_artifacts = tuple(frontend['browser']['screenshots']) if frontend.get('browser') else ()
        summary = dict(manifest, status='PASS', taskId=args.task_id, selector=SELECTOR,
            frontendAssertions=frontend['assertions'], httpRequests=frontend['requests'],
            realMapperQueries=json.loads((run / 'result.json').read_text())['realMapperQueries'],
            firstEffectiveFeedbackSeconds=feedback_seconds, elapsedSeconds=round(time.monotonic() - started, 3),
            artifacts={name: digest_file(run / name) for name in
                       (('manifest.json', 'result.json', 'junit.xml', 'gradle.log', 'consumer.log') + extra_artifacts)},
            evidence=str(run / 'summary.json'), limitations=([x for x in LIMITS if x != 'No rendered browser UI'] + frontend['browser']['limitations'] if frontend.get('browser') else LIMITS))
        orchestrator.atomic_write(run / 'summary.json', summary, default_mode=0o600)
        return summary
    except (CheckError, OSError, ValueError, ET.ParseError) as exc:
        cause = str(exc)
        for value in secrets.values():
            cause = cause.replace(value, '[redacted]')
        # A Gradle exit-zero receipt is provisional until result/XML/input checks pass.
        with log.open('a') as stream, redirect_stdout(stream), redirect_stderr(stream):
            try:
                orchestrator.cmd_evidence_put(argparse.Namespace(task_id=args.task_id, tree_sha=prepared['api']['tree'],
                    selector=SELECTOR, fixture_digest=prepared['fixtureDigest'], result='failed',
                    command='execution_history_check', artifact=str(log)))
            except SystemExit:
                print('Task baseline changed; no evidence overwrite. Incomplete bundle remains non-reusable.')
        attribute_failure(args, orchestrator, prepared, log, cause)
        orchestrator.atomic_write(run / 'failure.json', {'status': 'FAILED', 'firstDiagnostic': cause,
            'evidence': str(log), 'elapsedSeconds': round(time.monotonic() - started, 3)}, default_mode=0o600)
        raise CheckError(cause + '; evidence=' + str(run))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task-id', required=True)
    p.add_argument('--api', required=True, type=Path)
    p.add_argument('--web', required=True, type=Path)
    p.add_argument('--browser', action='store_true', help='Add standalone real Chromium history UI diagnostic')
    p.add_argument('--chrome', type=Path, default=Path('/usr/lib64/chromium-browser/chromium-browser'), help='Explicit installed Chromium executable, distribution fingerprinted')
    p.add_argument('--baseline', default='develop', help='Local advisory baseline; no fetch or auto-merge')
    p.add_argument('--check-only', action='store_true', help='No credential extraction/build/services/evidence writes or task changes')
    p.add_argument('--fixtures', type=Path, default=ROOT / FIXTURE_DIR)
    p.add_argument('--orchestrator', type=Path, default=ROOT / 'ops/orchestration/cyf_orchestrator.py')
    p.add_argument('--evidence-root', type=Path, default=Path('/var/tmp/cyf-execution-history-check'))
    p.add_argument('--node', type=Path, default=Path('/usr/bin/node'))
    p.add_argument('--mysqld', type=Path, default=Path('/home/isp/apps/mysql/bin/mysqld'))
    p.add_argument('--java-home', type=Path, default=Path('/home/isp/apps/jdk21'))
    p.add_argument('--gradle', type=Path, default=Path('/home/isp/apps/gradle/9.3.1/bin/gradle'))
    p.add_argument('--gradle-user-home', type=Path, default=Path.home() / '.gradle')
    p.add_argument('--credentials-init', type=Path, help='Optional explicitly authorized existing consumer init; never copied/printed')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    for name, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, name, value.resolve())
    started = time.monotonic()
    try:
        orchestrator = load_orchestrator(args.orchestrator)
        if args.check_only:
            prepared = precheck(args, orchestrator)
            report = {'status': 'PRECHECK_OK', 'verification': 'NOT_RUN', 'api': prepared['api'],
                'web': prepared['web'], 'baseline': prepared['baseline'], 'fixtureDigest': prepared['fixtureDigest'],
                'elapsedSeconds': round(time.monotonic() - started, 3),
                'nextAction': 'Owner confirms verification gate, then run without --check-only; no task transition was made'}
        else:
            # Acquire the per-tree output lock BEFORE fingerprints: waiting for a
            # prior run must not let us reuse an observation taken before the wait.
            api = source_identity(args.api)
            lock = Path('/tmp') / ('cyf-history-check-' + api['tree'] + '.lock')
            with orchestrator.exclusive_lock(lock):
                prepared = precheck(args, orchestrator)
                if prepared['api'] != api:
                    raise CheckError('API changed while waiting for its verification lock; restart on the confirmed candidate')
                result = execute(args, orchestrator, prepared, started)
            report = {name: result[name] for name in ('status', 'elapsedSeconds', 'frontendAssertions',
                      'httpRequests', 'realMapperQueries', 'evidence', 'limitations')}
            if result['status'] == 'REUSED':
                report['reusedFrom'] = result['reusedFrom']
            else:
                report['firstEffectiveFeedbackSeconds'] = result['firstEffectiveFeedbackSeconds']
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (CheckError, OSError, ValueError, KeyError, SystemExit) as exc:
        # argparse runs above this block; rejected gates/tool failures are short and actionable.
        print(json.dumps({'status': 'FAILED', 'firstDiagnostic': str(exc), 'verification': 'NOT_ACCEPTED',
                          'elapsedSeconds': round(time.monotonic() - started, 3)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
