set -eu
# The worker image provides the host libraries; its default JDK is not the tested toolchain.
# The verified Dragonwell 21 archive below always replaces JAVA_HOME/PATH.
for tool in python3 git curl tar sha256sum ldd; do command -v "$tool" >/dev/null; done
export CYF_EXPERIMENT="$(mktemp -d /tmp/cyf-backend-flow-ci.XXXXXX)"
# Numeric preparation evidence survives truncated Flow console logs. No new gate.
cyf_phase() {
  phase_uptime="$(cut -d' ' -f1 /proc/uptime)"
  printf 'CYF_FLOW_PHASE %s wall=%s monotonic=%s\n' "$1" "$(date -u +%FT%TZ)" "$phase_uptime"
  printf '%s\t%s\n' "$1" "$phase_uptime" >> "$CYF_EXPERIMENT/preparation-phases.tsv"
}
cyf_phase runtime.begin
python3 - <<'CYFTOOLS'
import io,base64,gzip,hashlib,json,os,pathlib
raw=base64.b64decode('@CYF_TOOL_BUNDLE_BASE64@',validate=True)
assert hashlib.sha256(raw).hexdigest()=='@CYF_TOOL_BUNDLE_SHA256@', 'tool bundle hash mismatch'
root=pathlib.Path(os.environ['CYF_EXPERIMENT'])
for name,text in json.loads(gzip.decompress(raw).decode()).items():
 p=root/name
 p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 p.write_text(text)
 p.chmod(0o600)
CYFTOOLS
cyf_phase jdk.begin
python3 "$CYF_EXPERIMENT/prepare-backend-jdk.py" --cache "$HOME/.cache/cyf-backend-jdk-archives" --destination "$CYF_EXPERIMENT/jdk" > "$CYF_EXPERIMENT/jdk-result.txt"
cat "$CYF_EXPERIMENT/jdk-result.txt"
export JAVA_HOME="$(tail -1 "$CYF_EXPERIMENT/jdk-result.txt")"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
cyf_phase jdk.end
# PPT raster previews were removed; no font-rendering packages are installed.
cyf_phase runtime.end

cyf_phase mysql.begin
export CYF_REVIEW_MYSQL_ARCHIVE_SHA=e6503f2ca665dbd4524a0109fa15969453f02b69c20f42d3fe8ba0d0b0ca1a1f
mysql_cache="$HOME/.cache/cyf-backend-mysql-archives"
mkdir -p "$mysql_cache"
mysql_archive="$mysql_cache/mysql-$CYF_REVIEW_MYSQL_ARCHIVE_SHA.tar.xz"
if [ ! -e "$mysql_archive" ]; then
  mysql_temporary="$(mktemp "$mysql_cache/.download.XXXXXX")"
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' 'https://cdn.mysql.com/archives/mysql-8.0/mysql-8.0.21-linux-glibc2.17-x86_64-minimal.tar.xz' -o "$mysql_temporary"
  printf '%s  %s\n' "$CYF_REVIEW_MYSQL_ARCHIVE_SHA" "$mysql_temporary" | sha256sum -c -
  mv "$mysql_temporary" "$mysql_archive"
fi
printf '%s  %s\n' "$CYF_REVIEW_MYSQL_ARCHIVE_SHA" "$mysql_archive" | sha256sum -c -
mkdir "$CYF_EXPERIMENT/mysql-runtime"
tar -xJf "$mysql_archive" -C "$CYF_EXPERIMENT/mysql-runtime" --strip-components=1
export CYF_REVIEW_MYSQLD="$CYF_EXPERIMENT/mysql-runtime/bin/mysqld"
libaio_archive="$mysql_cache/libaio-d1476e4beab3d85f8a7d31de94c27472711ed3ef399ce70708e24b259426125b.deb"
if [ ! -e "$libaio_archive" ]; then
  libaio_temporary="$(mktemp "$mysql_cache/.libaio.XXXXXX")"
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' 'https://deb.debian.org/debian/pool/main/liba/libaio/libaio1_0.3.113-4_amd64.deb' -o "$libaio_temporary"
  printf '%s  %s\n' d1476e4beab3d85f8a7d31de94c27472711ed3ef399ce70708e24b259426125b "$libaio_temporary" | sha256sum -c -
  mv "$libaio_temporary" "$libaio_archive"
fi
printf '%s  %s\n' d1476e4beab3d85f8a7d31de94c27472711ed3ef399ce70708e24b259426125b "$libaio_archive" | sha256sum -c -
export CYF_REVIEW_LIBAIO_ARCHIVE="$libaio_archive"
python3 - <<'LIBAIO'
import io,os,pathlib,tarfile
raw=pathlib.Path(os.environ['CYF_REVIEW_LIBAIO_ARCHIVE']).read_bytes()
assert raw[:8]==b'!<arch>\n'
offset=8;found=[]
while offset<len(raw):
 header=raw[offset:offset+60];assert len(header)==60 and header[58:60]==b'`\n'
 size=int(header[48:58]);name=header[:16].decode().strip().rstrip('/')
 payload=raw[offset+60:offset+60+size];assert len(payload)==size
 if name=='data.tar.xz':found.append(payload)
 offset+=60+size+(size%2)
assert len(found)==1
with tarfile.open(fileobj=io.BytesIO(found[0]),mode='r:xz') as archive:
 data=archive.extractfile('./usr/lib/x86_64-linux-gnu/libaio.so.1.0.2').read()
destination=pathlib.Path(os.environ['CYF_EXPERIMENT'])/'mysql-libs'
destination.mkdir(mode=0o700)
(destination/'libaio.so.1').write_bytes(data)
LIBAIO
libnuma_archive="$mysql_cache/libnuma-ab2277a2af54056f7c2b01f98c0ac9ea546753a35de00e74285b7a0f667ea7e7.deb"
if [ ! -e "$libnuma_archive" ]; then
  libnuma_temporary="$(mktemp "$mysql_cache/.libnuma.XXXXXX")"
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' 'https://archive.debian.org/debian/pool/main/n/numactl/libnuma1_2.0.12-1_amd64.deb' -o "$libnuma_temporary"
  printf '%s  %s\n' ab2277a2af54056f7c2b01f98c0ac9ea546753a35de00e74285b7a0f667ea7e7 "$libnuma_temporary" | sha256sum -c -
  mv "$libnuma_temporary" "$libnuma_archive"
fi
printf '%s  %s\n' ab2277a2af54056f7c2b01f98c0ac9ea546753a35de00e74285b7a0f667ea7e7 "$libnuma_archive" | sha256sum -c -
export CYF_REVIEW_LIBNUMA_ARCHIVE="$libnuma_archive"
python3 - <<'LIBNUMA'
import io,os,pathlib,tarfile
raw=pathlib.Path(os.environ['CYF_REVIEW_LIBNUMA_ARCHIVE']).read_bytes()
assert raw[:8]==b'!<arch>\n'
offset=8;found=[]
while offset<len(raw):
 header=raw[offset:offset+60];assert len(header)==60 and header[58:60]==b'`\n'
 size=int(header[48:58]);name=header[:16].decode().strip().rstrip('/')
 payload=raw[offset+60:offset+60+size];assert len(payload)==size
 if name=='data.tar.xz':found.append(payload)
 offset+=60+size+(size%2)
assert len(found)==1
with tarfile.open(fileobj=io.BytesIO(found[0]),mode='r:xz') as archive:
 data=archive.extractfile('./usr/lib/x86_64-linux-gnu/libnuma.so.1.0.0').read()
destination=pathlib.Path(os.environ['CYF_EXPERIMENT'])/'mysql-libs'
destination.mkdir(mode=0o700,exist_ok=True)
(destination/'libnuma.so.1').write_bytes(data)
LIBNUMA
export LD_LIBRARY_PATH="$CYF_EXPERIMENT/mysql-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

ldd "$CYF_REVIEW_MYSQLD" > "$CYF_EXPERIMENT/mysql-ldd.txt"
cat "$CYF_EXPERIMENT/mysql-ldd.txt"
if grep -q 'not found' "$CYF_EXPERIMENT/mysql-ldd.txt"; then echo 'MySQL runtime dependency missing' >&2; exit 1; fi

"$CYF_REVIEW_MYSQLD" --no-defaults --version
cyf_phase mysql.end

# SM-C1 bridge test dependency, fixed to the reviewed Runtime commit/tree.
# No deployment or persistent service; update the pin explicitly with its contract tests.
cyf_phase sm_node.begin
node_cache="$HOME/.cache/cyf-sm-node-archives"
mkdir -p "$node_cache"
node_archive="$node_cache/node-v20.20.2-df770b2a6f130ed8627c9782c988fda9669fa23898329a61a871e32f965e007d.tar.xz"
if [ ! -e "$node_archive" ]; then
  node_partial="$(mktemp "$node_cache/.download.XXXXXX")"
  curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' 'https://nodejs.org/dist/v20.20.2/node-v20.20.2-linux-x64.tar.xz' -o "$node_partial"
  printf '%s  %s\n' df770b2a6f130ed8627c9782c988fda9669fa23898329a61a871e32f965e007d "$node_partial" | sha256sum -c -
  mv "$node_partial" "$node_archive"
fi
printf '%s  %s\n' df770b2a6f130ed8627c9782c988fda9669fa23898329a61a871e32f965e007d "$node_archive" | sha256sum -c -
mkdir "$CYF_EXPERIMENT/sm-node"
tar -xJf "$node_archive" -C "$CYF_EXPERIMENT/sm-node" --strip-components=1
export CYF_SM_NODE_BIN="$CYF_EXPERIMENT/sm-node/bin/node"
export PATH="$CYF_EXPERIMENT/sm-node/bin:$PATH"
"$CYF_SM_NODE_BIN" --version
sm_runtime="$CYF_EXPERIMENT/sm-runtime"
git init -q "$sm_runtime"
git -C "$sm_runtime" remote add origin 'https://github.com/chcbz/juyiai-runtime.git'
git -C "$sm_runtime" fetch --depth=1 origin fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63
git -C "$sm_runtime" checkout -q --detach fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63
test "$(git -C "$sm_runtime" rev-parse HEAD)" = 'fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63'
test "$(git -C "$sm_runtime" rev-parse 'HEAD^{tree}')" = 'd220e1fdc63d8d8518b4ff5d261f38cb2531cbcd'
test -z "$(git -C "$sm_runtime" status --porcelain)"
(cd "$sm_runtime/conf/codex-bridge" && npm ci --ignore-scripts --no-audit --no-fund)
export CYF_SM_NODE_PEER="$sm_runtime/conf/codex-bridge/test/fixtures/skill-management-node-peer.mjs"
"$CYF_SM_NODE_BIN" --check "$CYF_SM_NODE_PEER"
printf 'CYF_SM_RUNTIME_INPUT commit=%s tree=%s\n' 'fb1ef101c2255c280e5bc53ba78fcd0c76d6cc63' 'd220e1fdc63d8d8518b4ff5d261f38cb2531cbcd'
sha256sum "$CYF_SM_NODE_BIN" "$CYF_SM_NODE_PEER" "$sm_runtime/conf/codex-bridge/package-lock.json"
cyf_phase sm_node.end

export CYF_FLOW_COMPILE_CACHE_OPT_IN=1
export CYF_FLOW_SHORT_LIVED_TEST_JVM=1
test -n "${CI_COMMIT_SHA:-}"
test "$(git rev-parse HEAD)" = "$CI_COMMIT_SHA"
export CYF_FLOW_GRADLE_ACTIVE=1
export CYF_FLOW_BUILD_ROOT="$CYF_EXPERIMENT/build"
test ! -e "$CYF_FLOW_BUILD_ROOT"
mkdir -p "$CYF_FLOW_BUILD_ROOT"
git diff --exit-code HEAD --
export CYF_SOURCE_CLEAN_BEFORE=1
# Preserve complete compiler diagnostics and per-task timing.
cat > "$CYF_EXPERIMENT/owner-fixture-diagnostics.gradle" <<'OWNERDIAGNOSTICS'
allprojects {
    tasks.withType(org.gradle.api.tasks.compile.JavaCompile).configureEach {
        options.compilerArgs += ['-Xmaxerrs', '1000']
    }
}
def cyfDiagnosticStart = System.nanoTime()
def cyfRuntime = java.lang.management.ManagementFactory.runtimeMXBean
def cyfCpu = java.lang.management.ManagementFactory.operatingSystemMXBean
def cyfPhase = { String name ->
    println('CYF_GRADLE_PHASE ' + groovy.json.JsonOutput.toJson([
        phase: name, rootBuild: gradle.parent == null, elapsedSeconds: (System.nanoTime() - cyfDiagnosticStart) / 1000000000.0,
        jvmUptimeSeconds: cyfRuntime.uptime / 1000.0,
        processCpuSeconds: cyfCpu.processCpuTime / 1000000000.0,
        availableProcessors: cyfCpu.availableProcessors,
        c1Only: cyfRuntime.inputArguments.contains('-XX:TieredStopAtLevel=1')]))
}
cyfPhase('init')
gradle.projectsEvaluated { cyfPhase('projectsEvaluated') }
gradle.taskGraph.whenReady { cyfPhase('taskGraphReady') }
def cyfTaskStarts = new java.util.concurrent.ConcurrentHashMap()
gradle.taskGraph.beforeTask { task -> cyfTaskStarts[task.path] = System.nanoTime() }
gradle.taskGraph.afterTask { task, state ->
    def started = cyfTaskStarts.remove(task.path)
    if (started != null) {
        println('CYF_TASK_TIMING ' + groovy.json.JsonOutput.toJson([
            task: task.path, rootBuild: gradle.parent == null, startedSeconds: (started - cyfDiagnosticStart) / 1000000000.0, seconds: (System.nanoTime() - started) / 1000000000.0,
            skipped: state.skipped, skipMessage: state.skipMessage, failed: state.failure != null]))
    }
}

OWNERDIAGNOSTICS
set +e
cyf_phase gradle.begin
python3 - > "$CYF_FLOW_BUILD_ROOT/gradle-output.log" 2>&1 <<'CYFGRADLE'
import hashlib,json,os,pathlib,subprocess,sys
root=pathlib.Path(os.environ['CYF_EXPERIMENT'])
raw=(root/'ops/ci/aliyun-flow/backend-ci-policy.json').read_bytes()
policy=json.loads(raw)
for name in ('build.gradle', 'settings.gradle'):
    path=pathlib.Path(name)
    print('CYF_BUILD_INPUT '+name+' '+hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
argv=[value.replace('$CYF_EXPERIMENT',str(root)).replace(
    '$CYF_FLOW_BUILD_ROOT',os.environ['CYF_FLOW_BUILD_ROOT']) for value in policy['argv']]
tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],universal_newlines=True).strip()
sys.exit(subprocess.run([sys.executable,str(root/'ops/orchestration/cyf_orchestrator.py'),
    'gradle','--flow-ci','--cwd',str(pathlib.Path.cwd()),'--tree-sha',tree,
    '--selector',policy['selector'],'--fixture-digest',hashlib.sha256(raw).hexdigest(),
    'FLOW-CI-5260799','--']+argv,check=False).returncode)
CYFGRADLE
gradle_rc=$?
cyf_phase gradle.end
set -e
cat "$CYF_FLOW_BUILD_ROOT/gradle-output.log"
python3 - <<'PYDIAGNOSTICS'
import base64, gzip, hashlib, json, os, re, xml.etree.ElementTree as ET
from pathlib import Path
root = Path(os.environ['CYF_FLOW_BUILD_ROOT'])
lines = (root / 'gradle-output.log').read_text(errors='replace').splitlines()
errors = []
current = None
for line in lines:
    if re.search(r'\.java:\d+: (?:error:|错误:)', line):
        current = {'diagnostic': line, 'details': []}
        errors.append(current)
    elif current is not None and re.match(r'\s*(?:required:|found:|reason:|symbol:|location:|需要:|找到:|原因:|符号:|位置:)', line):
        current['details'].append(line.strip())
def safe_failure_text(value):
    value = value or ''
    for name, secret in os.environ.items():
        if len(secret) >= 8 and re.search(r'(?i)secret|token|password|credential|access.?key', name):
            value = value.replace(secret, '[REDACTED]')
    value = re.sub(r'(?i)(authorization|api[_-]?key|password|secret|token)\s*[:=]\s*[^\s,;]+', r'\1=[REDACTED]', value)
    value = re.sub(r'https?://[^\s<>]+', '[URL]', value)
    return value[:3000]
reports = []
for path in sorted(root.rglob('TEST-*.xml')):
    suite = ET.parse(str(path)).getroot()
    failures = []
    for case in suite.findall('testcase'):
        for failure in list(case.findall('failure')) + list(case.findall('error')):
            failures.append({'class': case.get('classname'), 'test': case.get('name'), 'type': failure.get('type'), 'message': safe_failure_text(failure.get('message')), 'projectFrames': [line.strip() for line in (failure.text or '').splitlines() if re.match(r'\s*at (?:app//)?cn\.jia\.[\w.$]+\([^)]*\)', line)][:16]})
    reports.append({'path': str(path.relative_to(root)), 'name': suite.get('name'),
        'counts': {k: int(suite.get(k, 0)) for k in ('tests', 'failures', 'errors', 'skipped')}, 'failures': failures})
data = json.dumps({'commit': os.environ.get('CI_COMMIT_SHA'), 'run': os.environ.get('BUILD_NUMBER'),
    'compilerDiagnostics': errors, 'junitReports': reports,
    'gradlePhases': [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('CYF_GRADLE_PHASE ')]}, separators=(',', ':'), ensure_ascii=False).encode()
compressed = base64.b64encode(gzip.compress(data)).decode()
print('CYF_DIAGNOSTIC_SUMMARY ' + json.dumps({'compilerErrors': len(errors), 'junitSuites': len(reports),
    'sha256': hashlib.sha256(data).hexdigest(), 'encoding': 'gzip+base64', 'base64Bytes': len(compressed)}))
for index in range(0, len(compressed), 3000):
    print('CYF_DIAGNOSTIC_CHUNK %d %s' % (index // 3000, compressed[index:index + 3000]))
PYDIAGNOSTICS
if [ "$gradle_rc" -ne 0 ]; then exit "$gradle_rc"; fi
python3 - <<'PYARTIFACT'
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
    if (env.get('PIPELINE_ID') != '5260799'
            or commit != env.get('CI_COMMIT_SHA') or not re.fullmatch('[0-9a-f]{40,64}', commit)
            or not re.fullmatch('[1-9][0-9]*', env.get('BUILD_NUMBER', ''))):
        raise SystemExit('unexpected Flow source/run identity')
    # Both checks are enforced in the shell, before and after Gradle; repeat the
    # latter here. Untracked build outputs are not part of the tracked source.
    if env.get('CYF_SOURCE_CLEAN_BEFORE') != '1':
        raise SystemExit('missing successful pre-build source check')
    subprocess.check_call(['git', 'diff', '--exit-code', 'HEAD', '--'])
    build = Path(env['CYF_FLOW_BUILD_ROOT'])
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
    source = dict(branch=env.get('CI_COMMIT_REF_NAME'), commit_sha=commit, tree_sha=tree, clean_before=True, clean_after=True)
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
PYARTIFACT
python3 - <<'PYTESTREPORT'
import json, os, shutil, xml.etree.ElementTree as ET
from pathlib import Path
root = Path(os.environ['CYF_FLOW_BUILD_ROOT'])
dest = Path('_cyf_api_flow_export/test-results')
records = []
for xml in sorted(root.rglob('TEST-*.xml')):
    suite = ET.parse(str(xml)).getroot()
    relative = xml.relative_to(root)
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(xml), str(target))
    records.append(dict(path=str(relative), name=suite.attrib.get('name'), **{
        k:int(suite.attrib.get(k,0)) for k in ('tests','failures','errors','skipped')}))
if not records:
    raise RuntimeError('No actual JUnit reports')
counts = {k:sum(r[k] for r in records) for k in ('tests','failures','errors','skipped')}
if counts['failures'] or counts['errors']:
    raise RuntimeError('Actual failing JUnit report')
summary = dict(pipeline=os.environ.get('PIPELINE_ID'), run=os.environ.get('BUILD_NUMBER'),
    commit=os.environ.get('CI_COMMIT_SHA'), counts=counts, suites=records,
    countNote='Test executions; source sets can overlap. Skips remain explicit.')
# Keep numeric diagnostics in the existing summary: Flow's log API can omit the
# start of the replayed Gradle output even when its more flag is false.
gradle_lines=(root/'gradle-output.log').read_text(errors='replace').splitlines()
summary['gradlePhases']=[json.loads(line.split(' ',1)[1]) for line in gradle_lines
    if line.startswith('CYF_GRADLE_PHASE ')]
summary['taskTimings']=[json.loads(line.split(' ',1)[1]) for line in gradle_lines
    if line.startswith('CYF_TASK_TIMING ')]
# Preparation observations are value-free, optional diagnostics, not acceptance gates.
try:
    preparation = Path(os.environ['CYF_EXPERIMENT'])
    allowed = {name + '.' + edge for name in ('runtime', 'jdk', 'mysql', 'gradle')
               for edge in ('begin', 'end')}
    events = []
    for line in (preparation/'preparation-phases.tsv').read_text().splitlines():
        name, value = line.split('\t')
        if name in allowed:
            events.append(dict(phase=name, monotonicSeconds=float(value)))
    summary['flowPreparationPhases'] = events
    jdk = [json.loads(line.split(' ', 1)[1])
           for line in (preparation/'jdk-result.txt').read_text().splitlines()
           if line.startswith('CYF_JDK_TIMING ')]
    if len(jdk) == 1:
        summary['jdkBootstrap'] = {key: jdk[0][key] for key in
            ('archive_sha256', 'cache_hit', 'archive_seconds', 'total_seconds', 'version')}
except (OSError, KeyError, ValueError):
    summary['preparationObservationStatus'] = 'UNAVAILABLE'
(dest / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('CYF_API_TEST_SUMMARY '+json.dumps(dict(counts=counts,suites=len(records))))
# Bounded, value-free cache inventory. Observation failure does not fail a build.
import subprocess,time
started=time.monotonic()
home=Path.home()
paths={'gradle':home/'.gradle/caches', 'maven':home/'.m2',
       'jdk_archives':home/'.cache/cyf-backend-jdk-archives',
       'mysql_archives':home/'.cache/cyf-backend-mysql-archives',
       'other_runtimes':home/'.cache/cyf-test-runtime', 'node':home/'.npm',
       'yarn':home/'.yarn', 'go':Path('/go/pkg/mod'), 'all_runtime_cache':home/'.cache'}
for label in ('modules-2','build-cache-1','jars-9','transforms-3','transforms-4','8.14.3'):
    paths['gradle_'+label]=home/'.gradle/caches'/label
inventory={}
for label,path in paths.items():
    try:
        if path.is_symlink():
            inventory[label]={'status':'SYMLINK_NOT_FOLLOWED'}
        elif path.exists():
            result=subprocess.run(['du','-sx','--block-size=1',str(path)],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,universal_newlines=True,check=False)
            inventory[label]={'bytes':int(result.stdout.split()[0])} if result.returncode==0 else {'status':'DU_FAILED'}
        else:
            inventory[label]={'bytes':0}
    except (OSError,ValueError,IndexError):
        inventory[label]={'status':'UNKNOWN'}
result=dict(directories=inventory,seconds=round(time.monotonic()-started,3))
summary['cacheInventory']=result
(dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('CYF_CACHE_INVENTORY '+json.dumps(result,sort_keys=True))
PYTESTREPORT
cyf_phase package.end
