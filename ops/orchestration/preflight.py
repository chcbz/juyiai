"""Read-only, offline task diagnostics. Never executes build tools or user commands."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess


def git(cwd, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    # Avoid implicit object downloads in partial clones; refs are local snapshots.
    env['GIT_NO_LAZY_FETCH'] = '1'
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(cwd)] + list(args), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError('local Git query failed: ' + args[0])
    return result.stdout.decode('utf-8', errors='replace').strip()


def file_probe(repo, value):
    path = Path(value)
    if not path.is_absolute():
        path = repo / path
    path = path.resolve()
    # Never read credential files or arbitrary external paths as fixtures.
    if repo != path and repo not in path.parents:
        return {'path': value, 'status': 'outside_repository'}
    if not path.is_file():
        return {'path': value, 'status': 'missing'}
    return {'path': str(path.relative_to(repo)), 'status': 'present',
            'bytes': path.stat().st_size}


def collect(args, ledger):
    item = ledger.get('tasks', {}).get(args.task_id)
    if item is None:
        raise ValueError('unknown task: ' + args.task_id)
    requested = Path(args.cwd).resolve()
    repo = Path(git(requested, 'rev-parse', '--show-toplevel')).resolve()
    if requested != repo:
        raise ValueError('--cwd must be the repository/worktree root')
    head = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}')
    tree = git(repo, 'rev-parse', '--verify', 'HEAD^{tree}')
    status = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=normal')
    try:
        branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    except ValueError:
        branch = None
    exact = item.get('exact_sha_tree') or {}
    issues = []
    def notice(code, action):
        issues.append({'code': code, 'next_action': action})
    if status:
        notice('DIRTY_WORKTREE', 'Preserve changes; choose a clean fixed candidate for formal verification.')
    matches = head == exact.get('commit_sha') and tree == exact.get('tree_sha')
    if not matches:
        notice('TASK_BASELINE_MISMATCH', 'Confirm task repository and exact commit/tree before verification; do not auto-update ledger.')
    baseline = {'ref': args.baseline, 'freshness': 'local_ref_only_no_fetch'}
    try:
        # Resolve an object, never accept refs as command options or execute shell text.
        base = git(repo, 'rev-parse', '--verify', '--end-of-options', args.baseline + '^{commit}')
        counts = git(repo, 'rev-list', '--left-right', '--count', base + '...' + head).split()
        baseline.update(commit=base, baseline_only_commits=int(counts[0]), head_only_commits=int(counts[1]))
        if counts[0] != '0':
            notice('BASELINE_NOT_CONTAINED', 'Inspect divergence from the chosen baseline; no automatic merge or checkout.')
    except ValueError:
        baseline['status'] = 'unavailable'
        notice('BASELINE_UNAVAILABLE', 'Supply a locally available baseline; remote freshness remains unverified.')
    tools = {name: {'available': shutil.which(name) is not None, 'version': 'not_executed'}
             for name in (['java', 'python3'] if args.component == 'api' else ['node', 'npm'])}
    for name, state in tools.items():
        if not state['available']:
            notice('TOOL_MISSING:' + name, 'Prepare the approved toolchain; this command installs nothing.')
    config_names = ['build.gradle', 'settings.gradle', 'gradlew'] if args.component == 'api' else ['package.json', 'package-lock.json']
    config = [file_probe(repo, name) for name in config_names]
    fixtures = [file_probe(repo, value) for value in args.fixture]
    for probe in config + fixtures:
        if probe['status'] != 'present':
            notice('PATH_' + probe['status'].upper(), 'Check required path: ' + probe['path'])
    # Current schema has no path ownership declarations. Do not invent conflict detection.
    others = [{'task_id': key, 'owner': value.get('owner'), 'gate': value.get('current_gate')}
              for key, value in ledger.get('tasks', {}).items()
              if key != args.task_id and value.get('owner') and value['owner'].get('mode') == 'writer']
    verification = {
        'selector': args.selector, 'execution': 'NOT_RUN',
        'fixture_readiness': 'existence_only; database/schema/content not verified',
        'dependency_readiness': 'NOT_VERIFIED; no downloads, credentials, services or dependency resolution',
        'path_conflicts': 'UNKNOWN; runtime ledger has no owned-path/worktree mapping',
        'route': 'orchestrated_local_fixed_clean_source' if args.component == 'api' else 'frontend_Flow_4403172',
        'next_action': ('Read applicable build.gradle; run the selected tests and validateLayering via orchestrator gradle.'
                        if args.component == 'api' else 'Use local preview/cheap diagnostics only; formal tests/build use exact Flow candidate.')}
    if not args.selector:
        notice('SELECTOR_NOT_SET', 'Select the smallest relevant verification before implementation; no test was selected automatically.')
    return {
        'schema_version': 1, 'kind': 'read_only_preflight',
        'observed_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        'task_id': args.task_id, 'owner': item.get('owner'), 'gate': item.get('current_gate'),
        'component': args.component, 'repository': str(repo), 'branch': branch,
        'head': head, 'tree': tree, 'worktree_clean': not bool(status),
        'task_exact_match': matches, 'baseline': baseline, 'tools': tools,
        'configuration': config, 'fixtures': fixtures, 'verification': verification,
        'other_writer_tasks': others, 'findings': issues,
        'verdict': 'OBSERVATIONS_ONLY_NOT_BUILD_OR_RELEASE_APPROVAL',
        'side_effects': 'none; local Git/filesystem reads only; no fetch/build/task transition/notification'}


def dispatch(args, ledger):
    try:
        report = collect(args, ledger)
    except (ValueError, OSError) as exc:
        # Do not print Git stderr or credential/config contents.
        print(json.dumps({'kind': 'read_only_preflight', 'status': 'ERROR',
                          'error': str(exc) if isinstance(exc, ValueError) else 'filesystem/tool unavailable'}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Findings are advisory, not a new admission gate.
    return 0
