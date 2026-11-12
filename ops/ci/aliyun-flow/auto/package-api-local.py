#!/usr/bin/env python3
"""Explicit, source-only local producer. Never invokes Gradle or an installer.

Evidence/hashes are cross-checked consistency inputs, NOT build authentication.
A later trusted root admission must authenticate the build and authorize release.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile

# Keep the actual original pin; no dependency relaxation in the local producer.
OPENCV_SHA = '323d40119548134b0966d3735e97a78d1edbc79bd91e7fb1074e5152392095f4'
OPENCV_SIZE = 722802
MEMBERS = ('application.jar', 'application.metadata.json', 'application.sidecar.json',
           'dependency.provenance.json', 'receipt.json')
METADATA_KEYS = ('CYF-Release-Version', 'CYF-Source-Commit', 'CYF-Source-Tree', 'CYF-Local-Build-Id')
SAFE_CODES = frozenset(('INPUT_INVALID', 'PATH_UNSAFE', 'SOURCE_MISMATCH', 'SOURCE_DIRTY',
    'EVIDENCE_INVALID', 'EVIDENCE_TAMPERED', 'BUILD_NOT_FRESH', 'TEST_EVIDENCE_INVALID',
    'JAR_INVALID', 'MAIL_RUNTIME_INVALID', 'PROVENANCE_INVALID', 'OUTPUT_EXISTS', 'IO_FAILURE'))


class Rejected(Exception):
    def __init__(self, code):
        assert code in SAFE_CODES
        self.code = code
        super().__init__(code)


def require(condition, code='EVIDENCE_INVALID'):
    if not condition:
        raise Rejected(code)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def exact(obj, keys, code='EVIDENCE_INVALID'):
    require(type(obj) is dict and set(obj) == set(keys), code)
    return obj


def token(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value), 'INPUT_INVALID')
    return value


def hex_value(value, length):
    require(type(value) is str and re.fullmatch('[0-9a-f]{%d}' % length, value), 'INPUT_INVALID')
    return value


def strict_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result)
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda unused: (_ for _ in ()).throw(Rejected('EVIDENCE_INVALID')))
    except (ValueError, UnicodeError):
        raise Rejected('EVIDENCE_INVALID') from None


def physical(value, kind='file', private=False):
    require(type(value) is str and value.startswith('/'), 'PATH_UNSAFE')
    path = Path(value)
    require(str(path) == value and path.resolve(strict=True) == path, 'PATH_UNSAFE')
    for component in (path,) + tuple(path.parents):
        require(not component.is_symlink(), 'PATH_UNSAFE')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) if kind == 'file' else stat.S_ISDIR(info.st_mode), 'PATH_UNSAFE')
    if kind == 'file':
        require(info.st_nlink == 1, 'PATH_UNSAFE')
    if private:
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o077, 'PATH_UNSAFE')
    return path


def within(path, root):
    require(path != root and root in path.parents, 'PATH_UNSAFE')
    return path


def disjoint(*roots):
    for i, root in enumerate(roots):
        for other in roots[i + 1:]:
            require(root != other and root not in other.parents and other not in root.parents, 'PATH_UNSAFE')


def read_stable(path):
    path = physical(str(path))
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'PATH_UNSAFE')
        data = handle.read()
        after = os.fstat(handle.fileno())
    current = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
    require(identity(before) == identity(after) == identity(current), 'EVIDENCE_TAMPERED')
    return data


def record(path):
    data = read_stable(path)
    return {'path': str(path), 'sha256': sha(data), 'size': len(data)}


def checked_record(obj, root=None):
    exact(obj, ('path', 'sha256', 'size'))
    hex_value(obj['sha256'], 64)
    require(type(obj['size']) is int and obj['size'] > 0)
    path = physical(obj['path'])
    if root:
        within(path, root)
    data = read_stable(path)
    require(sha(data) == obj['sha256'] and len(data) == obj['size'], 'EVIDENCE_TAMPERED')
    return path, data


def source_state(root, identity):
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'LANG': 'C',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0'}
    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(root), *args], env=env,
                                           stderr=subprocess.DEVNULL).decode().strip()
        except (subprocess.CalledProcessError, UnicodeError):
            raise Rejected('SOURCE_MISMATCH') from None
    require(git('rev-parse', '--show-toplevel') == str(root), 'SOURCE_MISMATCH')
    require(git('rev-parse', 'HEAD') == identity['commit'] and
            git('rev-parse', 'HEAD^{tree}') == identity['tree'], 'SOURCE_MISMATCH')
    require(not git('status', '--porcelain=v1', '--untracked-files=all'), 'SOURCE_DIRTY')
    return {'commit': identity['commit'], 'tree': identity['tree'], 'clean': True}


def manifest(jar_bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(jar_bytes)) as boot:
            names = boot.namelist()
            require(len(names) == len(set(names)), 'JAR_INVALID')
            require(all(not n.startswith('/') and '..' not in n.split('/') and '\\' not in n for n in names), 'JAR_INVALID')
            text = boot.read('META-INF/MANIFEST.MF').decode('utf-8')
        lines = text.replace('\r\n', '\n').split('\n')
        unfolded = []
        for line in lines:
            if not line:
                break  # main section only
            if line.startswith(' '):
                require(bool(unfolded), 'JAR_INVALID')
                unfolded[-1] += line[1:]
            else:
                unfolded.append(line)
        result = {}
        for line in unfolded:
            key, sep, value = line.partition(': ')
            require(bool(sep) and key.lower() not in {k.lower() for k in result}, 'JAR_INVALID')
            result[key] = value
        require(result.get('Start-Class') == 'cn.jia.JiaApplication' and
                result.get('Main-Class', '').startswith('org.springframework.boot.loader.'), 'JAR_INVALID')
        return result
    except (zipfile.BadZipFile, KeyError, UnicodeError, RuntimeError):
        raise Rejected('JAR_INVALID') from None


def mail_runtime(jar):
    # Only this real helper is reused. Loading its module does NOT call Flow main.
    helper = Path(__file__).with_name('package-api.py')
    spec = importlib.util.spec_from_file_location('cyf_mail_runtime_only', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.verify_mail_runtime(jar)
    except SystemExit:
        raise Rejected('MAIL_RUNTIME_INVALID') from None


def task_executed(log, task):
    lines = re.findall(r'^> Task ' + re.escape(task) + r'(?=\s|$)(.*)$', log, flags=re.MULTILINE)
    # Parallel Gradle can repeat a task header when resuming grouped output.
    # Keep rejecting cached/skipped/failed tasks; accept repeated empty headers
    # only with one exact root-build completion from the bound diagnostic init.
    completions = []
    for line in log.splitlines():
        if line.startswith('CYF_TASK_TIMING '):
            try:
                item = strict_json(line.split(' ', 1)[1])
            except Rejected:
                raise Rejected('BUILD_NOT_FRESH') from None
            if item.get('rootBuild') is True and item.get('task') == task:
                completions.append(item)
    if completions:
        require(len(completions) == 1 and bool(lines) and all(not x.strip() for x in lines)
                and completions[0].get('skipped') is False
                and completions[0].get('failed') is False
                and completions[0].get('skipMessage') is None, 'BUILD_NOT_FRESH')
    else:
        require(len(lines) == 1 and not lines[0].strip(), 'BUILD_NOT_FRESH')


def xml_summary(data):
    try:
        require(b'<!DOCTYPE' not in data and b'<!ENTITY' not in data, 'TEST_EVIDENCE_INVALID')
        root = ET.fromstring(data)
        require(root.tag in ('testsuite', 'testsuites'), 'TEST_EVIDENCE_INVALID')
        suites = [root] if root.tag == 'testsuite' else list(root)
        count = failed = errors = skipped = 0
        names = set()
        for suite in suites:
            require(suite.tag == 'testsuite', 'TEST_EVIDENCE_INVALID')
            n, f, e, s = [int(suite.attrib.get(key, '0')) for key in ('tests', 'failures', 'errors', 'skipped')]
            cases = suite.findall('testcase')
            require(n == len(cases) and min(n, f, e, s) >= 0, 'TEST_EVIDENCE_INVALID')
            for case in cases:
                identity = (case.get('classname'), case.get('name'))
                require(all(identity) and identity not in names, 'TEST_EVIDENCE_INVALID')
                names.add(identity)
                require(not case.findall('failure') and not case.findall('error'), 'TEST_EVIDENCE_INVALID')
            require(s == sum(bool(c.findall('skipped')) for c in cases), 'TEST_EVIDENCE_INVALID')
            count += n
            failed += f
            errors += e
            skipped += s
        require(count >= skipped and failed == errors == 0, 'TEST_EVIDENCE_INVALID')
        return {'tests': count, 'failures': failed, 'errors': errors, 'skipped': skipped}
    except (ET.ParseError, ValueError):
        raise Rejected('TEST_EVIDENCE_INVALID') from None


def validate_argv(argv, required_tasks, inputs):
    require(type(argv) is list and bool(argv) and all(type(x) is str for x in argv))
    require(Path(argv[0]).name in ('gradle', 'gradlew'))
    # Public grammar only. Preserve exact task/filter ordering; never execute argv.
    simple = {'--no-daemon', '--no-build-cache', '--build-cache', '--rerun-tasks', '--console=plain', '--stacktrace', '--info', '--parallel', '--no-parallel', '--offline', '--max-workers=2',
              '-Dorg.gradle.jvmargs=-Xmx768m -XX:MaxMetaspaceSize=384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1',
              '-Dorg.gradle.jvmargs=-Xmx512m -XX:+UseSerialGC -XX:MaxMetaspaceSize=384m -XX:ActiveProcessorCount=2 -XX:TieredStopAtLevel=1'}
    task = re.compile(r':[A-Za-z0-9_:-]+\Z')
    index = 1
    previous_task = None
    metadata_init_seen = False
    while index < len(argv):
        arg = argv[index]
        if arg in ('-I', '--init-script'):
            require(index + 1 < len(argv) and any(argv[index + 1] == item['path'] for item in inputs))
            metadata_init_seen |= Path(argv[index + 1]).name == 'local-release-metadata.init.gradle'
            index += 2
        elif arg == '--project-cache-dir':
            require(index + 1 < len(argv) and Path(argv[index + 1]).is_absolute()
                    and str(Path(argv[index + 1])) == argv[index + 1])
            index += 2
        elif arg == '--tests':
            require(previous_task in required_tasks and previous_task not in (':starter:bootJar', ':validateLayering') and
                    index + 1 < len(argv) and re.fullmatch(r'[A-Za-z0-9_.*$-]+', argv[index + 1]))
            index += 2
        else:
            require(arg in simple or task.fullmatch(arg))
            if task.fullmatch(arg):
                previous_task = arg
            index += 1
    require(set(required_tasks).issubset(argv) and '--console=plain' in argv and metadata_init_seen)


def verify_evidence(evidence_data, identity, source, build):
    ev = strict_json(evidence_data)
    exact(ev, ('format', 'identity', 'sourceRoot', 'buildRoot', 'sourceBefore', 'sourceAfter',
               'invocation', 'tests', 'validateLayering', 'bootJar', 'opencv'))
    require(ev['format'] == 'cyf-api-local-build-evidence-v1' and ev['identity'] == identity and
            ev['sourceRoot'] == str(source) and ev['buildRoot'] == str(build))
    clean = {'commit': identity['commit'], 'tree': identity['tree'], 'clean': True}
    for state in (ev['sourceBefore'], ev['sourceAfter']):
        exact(state, ('commit', 'tree', 'clean'))
        require(state['clean'] is True)
    require(ev['sourceBefore'] == clean and ev['sourceAfter'] == clean)
    inv = exact(ev['invocation'], ('argv', 'exitCode', 'cacheHit', 'log', 'selector', 'fixtureSha256', 'inputs'))
    require(type(inv['exitCode']) is int and inv['exitCode'] == 0 and inv['cacheHit'] is False, 'BUILD_NOT_FRESH')
    token(inv['selector'])
    hex_value(inv['fixtureSha256'], 64)
    log_path, log_bytes = checked_record(inv['log'], build)
    log = log_bytes.decode('utf-8', errors='strict')
    require('GRADLE_LOCK_ACQUIRED task=' in log and 'EVIDENCE_HIT' not in log and
            re.search(r'^BUILD SUCCESSFUL(?:\s|$)', log, re.MULTILINE), 'BUILD_NOT_FRESH')
    inputs = inv['inputs']
    require(type(inputs) is list and bool(inputs))
    checked = set()
    for item in inputs:
        path, unused = checked_record(item)
        require(str(path) not in checked)
        checked.add(str(path))
    require(str(source / 'settings.gradle') in checked and str(source / 'starter/build.gradle') in checked)
    require(type(ev['tests']) is list and bool(ev['tests']), 'TEST_EVIDENCE_INVALID')
    tests = []
    tasks = set()
    reports_seen = set()
    for item in ev['tests']:
        exact(item, ('task', 'selector', 'fixtureSha256', 'reports'))
        require(type(item['task']) is str and re.fullmatch(r':[A-Za-z0-9_:-]+', item['task']) and
                item['task'] not in tasks, 'TEST_EVIDENCE_INVALID')
        token(item['selector'])
        hex_value(item['fixtureSha256'], 64)
        task_executed(log, item['task'])
        tasks.add(item['task'])
        require(type(item['reports']) is list and bool(item['reports']), 'TEST_EVIDENCE_INVALID')
        summaries = []
        for report in item['reports']:
            path, data = checked_record(report, build)
            require(str(path) not in reports_seen, 'TEST_EVIDENCE_INVALID')
            reports_seen.add(str(path))
            summaries.append({'sha256': report['sha256'], 'size': report['size'], **xml_summary(data)})
        require(sum(s['tests'] - s['skipped'] for s in summaries) > 0, 'TEST_EVIDENCE_INVALID')
        tests.append({'task': item['task'], 'selector': item['selector'],
                      'fixtureSha256': item['fixtureSha256'], 'reports': summaries})
    require({':starter:publicArtifactVerifierTest', ':starter:poiProductionRuntimeClasspathTest'}.issubset(tasks),
            'TEST_EVIDENCE_INVALID')
    require(ev['validateLayering'] == {'task': ':validateLayering'})
    task_executed(log, ':validateLayering')
    boot = exact(ev['bootJar'], ('task', 'proof'))
    require(boot['task'] == ':starter:bootJar')
    task_executed(log, boot['task'])
    validate_argv(inv['argv'], tasks | {':validateLayering', boot['task']}, inputs)
    proof_path, proof_data = checked_record(boot['proof'], build)
    require(proof_path == build / 'local-bootjar-proof.json')
    proof = strict_json(proof_data)
    exact(proof, ('format', 'identity', 'sourceRoot', 'buildRoot', 'sourceBefore', 'sourceAfter',
                  'task', 'metadata', 'moduleVersion', 'implementationVersion', 'jar', 'publicArtifactVerifier'))
    for state in (proof['sourceBefore'], proof['sourceAfter']):
        exact(state, ('commit', 'tree', 'clean'))
        require(state['clean'] is True)
    metadata = dict(zip(METADATA_KEYS, [identity[k] for k in ('version', 'commit', 'tree', 'buildId')]))
    require(proof['format'] == 'cyf-api-local-bootjar-proof-v1' and proof['identity'] == identity and
            proof['sourceRoot'] == str(source) and proof['buildRoot'] == str(build) and
            proof['sourceBefore'] == clean and proof['sourceAfter'] == clean and proof['task'] == boot['task'] and
            proof['metadata'] == metadata and proof['publicArtifactVerifier'] == 'bootJar-original-doLast-completed')
    token(proof['moduleVersion'])
    require(proof['implementationVersion'] is None or
            (type(proof['implementationVersion']) is str and re.fullmatch(r'[A-Za-z0-9_.-]+', proof['implementationVersion'])))
    begin = 'CYF_LOCAL_BOOTJAR_BEGIN ' + identity['buildId'] + '\n'
    end = 'CYF_LOCAL_BOOTJAR_END ' + sha(proof_data) + '\n'
    require(log.count(begin) == 1 and log.count(end) == 1 and
            log.index(begin) < log.index(end) < log.index('BUILD SUCCESSFUL'), 'BUILD_NOT_FRESH')
    jar, jar_bytes = checked_record(proof['jar'], build)
    mf = manifest(jar_bytes)
    require(all(mf.get(key) == value for key, value in metadata.items()), 'JAR_INVALID')
    require(mf.get('Implementation-Version') == proof['implementationVersion'], 'JAR_INVALID')
    runtime = mail_runtime(jar)
    require(sha(read_stable(jar)) == sha(jar_bytes), 'EVIDENCE_TAMPERED')
    provenance_path, provenance_bytes = checked_record(ev['opencv'], build)
    provenance = strict_json(provenance_bytes)
    exact(provenance, ('coordinate', 'jar_sha256', 'jar_size', 'resolved_file'))
    require(provenance['coordinate'] == 'org.opencv:opencv:4.5.5' and
            provenance['jar_sha256'] == OPENCV_SHA and type(provenance['jar_size']) is int and
            provenance['jar_size'] == OPENCV_SIZE, 'PROVENANCE_INVALID')
    dependency = read_stable(physical(provenance['resolved_file']))
    require(sha(dependency) == OPENCV_SHA and len(dependency) == OPENCV_SIZE, 'PROVENANCE_INVALID')
    return ev, proof, jar_bytes, provenance_bytes, runtime, tests


def payloads(identity, evidence_data, verified):
    ev, proof, jar, prov, runtime, tests = verified
    jar_ref = {'path': 'application.jar', 'sha256': sha(jar), 'size': len(jar)}
    prov_ref = {'path': 'dependency.provenance.json', 'sha256': sha(prov), 'size': len(prov)}
    evidence = {'sha256': sha(evidence_data), 'invocationLogSha256': ev['invocation']['log']['sha256'],
                'selector': ev['invocation']['selector'], 'fixtureSha256': ev['invocation']['fixtureSha256'],
                'inputs': ev['invocation']['inputs'], 'tests': tests,
                'bootJarProofSha256': ev['bootJar']['proof']['sha256']}
    receipt = {'format': 'cyf-api-local-release-receipt-v1', 'status': 'packaged',
               'producer': {'kind': 'local-build-v1'}, 'identity': identity,
               'source': {'commit': identity['commit'], 'tree': identity['tree'], 'cleanBefore': True, 'cleanAfter': True},
               'evidence': evidence, 'applicationJar': jar_ref, 'dependencyProvenance': prov_ref,
               'verification': {'mailRuntimeClasses': runtime, 'publicArtifactVerifier': proof['publicArtifactVerifier']}}
    receipt_bytes = canonical(receipt)
    binding = {'identity': identity, 'receiptSha256': sha(receipt_bytes),
               'applicationJar': jar_ref, 'dependencyProvenance': prov_ref}
    return {'application.jar': jar, 'dependency.provenance.json': prov, 'receipt.json': receipt_bytes,
            'application.metadata.json': canonical({'format': 'cyf-api-local-application-metadata-v1', **binding,
                'moduleVersion': proof['moduleVersion'], 'implementationVersion': proof['implementationVersion']}),
            'application.sidecar.json': canonical({'format': 'cyf-api-local-application-sidecar-v1', **binding})}


def publish(output, data, before_publish):
    require(set(data) == set(MEMBERS))
    require(not os.path.lexists(str(output)), 'OUTPUT_EXISTS')
    parent = physical(str(output.parent), 'directory', private=True)
    identity = (parent.stat().st_dev, parent.stat().st_ino)
    with tempfile.TemporaryDirectory(prefix='.cyf-local-package-', dir=str(parent)) as stage:
        temporary = Path(stage) / 'package.tgz'
        with temporary.open('xb') as handle:
            os.fchmod(handle.fileno(), 0o600)
            with tarfile.open(fileobj=handle, mode='w:gz', format=tarfile.USTAR_FORMAT) as archive:
                for name in MEMBERS:
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = len(data[name]), 0o600, 0
                    archive.addfile(info, io.BytesIO(data[name]))
            handle.flush()
            os.fsync(handle.fileno())
        proof = record(temporary)
        before_publish()
        require((parent.stat().st_dev, parent.stat().st_ino) == identity, 'PATH_UNSAFE')
        try:
            os.link(str(temporary), str(output), follow_symlinks=False)  # atomic, no overwrite
        except FileExistsError:
            raise Rejected('OUTPUT_EXISTS') from None
        temporary.unlink()
        fd = os.open(str(parent), os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        require(record(output) == {**proof, 'path': str(output)}, 'EVIDENCE_TAMPERED')
    return {**proof, 'path': str(output)}


def produce(args):
    require(args.opt_in is True, 'INPUT_INVALID')
    require(not any(os.environ.get(key) for key in ('PIPELINE_ID', 'BUILD_NUMBER', 'CYF_FLOW_GRADLE_ACTIVE')),
            'INPUT_INVALID')
    identity = {'version': token(args.version), 'buildId': token(args.build_id),
                'commit': hex_value(args.commit, 40), 'tree': hex_value(args.tree, 40)}
    source = physical(args.source_root, 'directory')
    build = physical(args.build_root, 'directory', private=True)
    output_parent = physical(str(Path(args.output).parent), 'directory', private=True)
    require(Path(args.output).is_absolute() and str(Path(args.output)) == args.output and args.output.endswith('.tgz'), 'PATH_UNSAFE')
    disjoint(source, build, output_parent)
    evidence_path = within(physical(args.evidence), build)
    hex_value(args.evidence_sha256, 64)
    source_state(source, identity)
    evidence_data = read_stable(evidence_path)
    require(sha(evidence_data) == args.evidence_sha256, 'EVIDENCE_TAMPERED')
    verified = verify_evidence(evidence_data, identity, source, build)
    data = payloads(identity, evidence_data, verified)
    def final_readback():
        source_state(source, identity)
        require(read_stable(evidence_path) == evidence_data, 'EVIDENCE_TAMPERED')
        verify_evidence(evidence_data, identity, source, build)
    package = publish(Path(args.output), data, final_readback)
    return {'format': 'cyf-api-local-package-v1', 'identity': identity, 'package': package,
            'receiptSha256': sha(data['receipt.json']), 'applicationJarSha256': sha(data['application.jar']),
            'dependencyProvenanceSha256': sha(data['dependency.provenance.json']),
            'buildEvidenceSha256': sha(evidence_data), 'productionAuthorized': False}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise Rejected('INPUT_INVALID')


def parser():
    result = SafeParser(description=__doc__, allow_abbrev=False)
    result.add_argument('--opt-in', action='store_true', required=True)
    for name in ('source-root', 'commit', 'tree', 'version', 'build-id', 'build-root', 'evidence', 'evidence-sha256', 'output'):
        result.add_argument('--' + name, required=True)
    return result


def main():
    try:
        args = parser().parse_args()
        result = produce(args)
        print(canonical(result).decode(), end='')
        return 0
    except Rejected as exc:
        print(canonical({'format': 'cyf-api-local-package-error-v1', 'code': exc.code}).decode(), end='')
    except (KeyError, TypeError, AttributeError, UnicodeError, ValueError):
        print(canonical({'format': 'cyf-api-local-package-error-v1', 'code': 'EVIDENCE_INVALID'}).decode(), end='')
    except OSError:
        print(canonical({'format': 'cyf-api-local-package-error-v1', 'code': 'IO_FAILURE'}).decode(), end='')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
