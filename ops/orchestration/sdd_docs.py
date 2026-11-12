#!/usr/bin/env python3
"""Read-only SDD document navigation checks; not YAML schema or release validation."""
import argparse
import json
import re
import sys
import os
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

REQUIRED = ('spec.md', 'design.md', 'tasks.md', 'acceptance.md', 'integration.yaml')
NAV_KEYS = {'current_design', 'current_plan', 'current_acceptance',
            'current_optimization', 'clarifications', 'v1_10_plan', 'previous_design'}
LINK = re.compile(r'(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')


def without_fences(text):
    lines = []
    fence = None
    for line in text.splitlines():
        mark = re.match(r'^\s*(`{3,}|~{3,})', line)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append('')
        else:
            lines.append('' if fence else line)
    return '\n'.join(lines)


# Only explicit active routes promote supporting notes. A date or file name never
# certifies implementation, publication, or permission to replay an old plan.
CURRENT_ROLES = {'ENTRY', 'CURRENT_GUIDE', 'CURRENT_SPEC', 'CURRENT_DETAIL',
                 'SELECTED_VERSIONED_CONTRACT', 'FROZEN_REGRESSION'}
PROTECTED_PARTS = {'evidence', 'archive', 'history', 'fixtures', 'before', 'receipts',
                   'verification', 'snapshots', 'logs', 'node_modules', '__pycache__'}


def inventory(root, mapping=None):
    root = Path(root).resolve()
    if mapping is None:
        mapping = json.loads((root / 'docs/sdd-document-map.json').read_text())
    discovery = mapping.get('discovery', {})
    explicit = {}
    for key, role in (('entrypoints', 'ENTRY'), ('current_guides', 'CURRENT_GUIDE'),
                      ('selected_details', 'CURRENT_DETAIL'),
                      ('selected_versioned_contracts', 'SELECTED_VERSIONED_CONTRACT'),
                      ('baseline_references', 'BASELINE_REFERENCE'),
                      ('source_attributions', 'CONTENT_SOURCE')):
        for path in discovery.get(key, []):
            explicit[path] = role
    rows = []
    paths = []
    for directory in ('docs', 'specs'):
        base = root / directory
        if base.is_dir():
            # Do not traverse symlinked external documentation or vendored trees.
            for folder, dirs, files in os.walk(str(base), followlinks=False):
                dirs[:] = sorted(d for d in dirs if not (Path(folder) / d).is_symlink())
                paths.extend(Path(folder) / f for f in sorted(files) if f.endswith('.md'))
    paths.extend(root / p for p in ('AGENTS.md', 'README.md') if (root / p).is_file())
    for p in sorted(set(paths)):
        if p.is_symlink():
            continue
        rel = str(p.relative_to(root))
        parts = p.relative_to(root).parts
        disposition = mapping.get('feature_dispositions', {}).get(parts[1], {}) if parts[0] == 'specs' and len(parts) > 2 else {}
        inactive = disposition.get('category') in ('已退役专题', '已闭环专题')
        topic = ('specs/' + parts[1] + '/spec.md') if parts[0] == 'specs' and len(parts) > 2 and parts[1] != '_template' else 'docs/README.md'
        if set(parts) & PROTECTED_PARTS or any(re.match(r'^(integration-evidence|verification|browser-acceptance)(-|$)', v) for v in parts) or 'prototypes' in parts:
            role = 'HISTORICAL_EVIDENCE'
        elif inactive:
            role = 'HISTORICAL_CONTEXT'
        elif rel in explicit:
            role = explicit[rel]
        elif rel == discovery.get('regression', {}).get('frozen_core'):
            role = 'FROZEN_REGRESSION'
        elif parts[0] == 'specs' and '_template' in parts:
            role = 'TEMPLATE'
        elif parts[:2] == ('specs', 'codex-history-closeout-20261023'):
            role = 'HISTORICAL_CONTEXT'
        elif parts[0] == 'specs' and len(parts) == 3 and p.name in REQUIRED[:4] + ('README.md',):
            role = 'CURRENT_SPEC'
        elif parts[:2] == ('docs', 'implementation') and p.name == 'TEMPLATE.md':
            role = 'TEMPLATE'
        elif parts[0] == 'specs' and re.search(r'(contract|schema|bundle|baseline|core-ui-regression)', p.name, re.I):
            role = 'UNSELECTED_VERSIONED_REFERENCE'
        elif (parts[:2] == ('docs', 'implementation') or parts[:2] in (('docs', 'superpowers'), ('docs', 'marketing'))
              or rel in discovery.get('history_routes', {})
              or re.search(r'(\d{8}|\d{4}-\d{2}-\d{2}|delivery-status|release-|checkpoint|handoff|audit|review|progress|recheck|test-results|integration-)', p.name, re.I)):
            role = 'HISTORICAL_CONTEXT'
        else:
            role = 'REFERENCE_UNVERIFIED'
        successor = disposition.get('successor', topic) if inactive else discovery.get('history_routes', {}).get(rel, topic)
        rows.append({'path': rel, 'role': role, 'default_search': role in CURRENT_ROLES,
                     'entry': successor, 'validity': (
                         'VERIFY_EXACT_SOURCE; not a current implementation/deployment assertion' if role == 'BASELINE_REFERENCE' else
                         'FROZEN_BYTES; historical candidate scope only' if role == 'FROZEN_REGRESSION' else
                         'CONTRACT_OR_GUIDANCE_ONLY; verify actual implementation and authorization' if role in CURRENT_ROLES else
                         'TRACEABILITY_OR_UNVERIFIED; enter responsible current topic before action')})
    return rows


def catalog(root):
    rows = inventory(root)
    return {'scope': 'All local docs/specs Markdown roles, not content or production certification',
            'documents': len(rows), 'role_counts': dict(sorted(Counter(r['role'] for r in rows).items())),
            'items': rows}


def search(root, pattern, include_history=False):
    root = Path(root).resolve()
    rows = inventory(root)
    files = [r['path'] for r in rows if include_history or r['default_search']]
    if not files:
        return 1
    # Argument list and -- keep the pattern out of shell/option interpretation.
    return subprocess.call(['rg', '-n', '-i', '--', pattern] + files, cwd=str(root))


def check(root, feature=None, all_docs=False):
    root = Path(root).resolve()
    errors, exceptions = [], []
    checked = set()
    links = 0
    stale_reference_links = []
    mapping_path = root / 'docs/sdd-document-map.json'
    mapping = json.loads(mapping_path.read_text())
    removed = mapping['removed']
    for old, new in removed.items():
        if (root / old).exists():
            errors.append('Removed path reappeared: ' + old)
        if not (root / new).exists():
            errors.append('Missing successor: ' + new)
    if feature:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', feature):
            raise ValueError('Invalid feature ID')
        dirs = [root / 'specs' / feature]
        if not dirs[0].is_dir():
            raise ValueError('Unknown feature: ' + feature)
    else:
        dirs = sorted(p for p in (root / 'specs').iterdir()
                      if p.is_dir() and not p.is_symlink() and p.name != '_template')

    def target_exists(p, target):
        nonlocal links
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            return
        links += 1
        dest = p.parent / unquote(url.path)
        if not dest.exists():
            source = str(p.relative_to(root))
            discovery = mapping.get('discovery', {})
            known = discovery.get('known_stale_baseline_links', {}).get(source, [])
            if source in discovery.get('baseline_references', []) and target in known:
                stale_reference_links.append({'source': source, 'target': target,
                    'status': 'STALE_BASELINE_SOURCE_MISSING; not current source navigation'})
            else:
                errors.append('{}: missing target {}'.format(source, target))

    def markdown(p):
        if p in checked:
            return
        checked.add(p)
        if not p.is_file():
            errors.append('Missing entry: ' + str(p.relative_to(root)))
            return
        text = without_fences(p.read_text())
        for match in LINK.finditer(text):
            target_exists(p, match.group(1))
        # Root-relative / absolute references used by AGENTS and the prototype spec.
        # Bare historical filenames in prose are not current navigation contracts.
        for token in re.findall(r'`([^`\n]+)`', text):
            path = token.split('#')[0]
            relative = path[len(str(root)) + 1:] if path.startswith(str(root) + '/') else path
            if (p.name == 'AGENTS.md' or p.name == 'prototype-spec.md') and re.match(
                    r'^(?:docs/|api/docs/|ops/|specs/|web/prototypes/|\.\./|'
                    + re.escape(str(root)) + r'/)', path):
                if not any(c in path for c in (' ', '*', '<', '>')):
                    if not (p.parent / path).exists() and not (root / path).exists():
                        errors.append('{}: missing inline path {}'.format(p.relative_to(root), path))
            if relative in removed:
                errors.append('{}: deleted reference {} -> {}'.format(
                    p.relative_to(root), path, removed[relative]))

    for folder in dirs:
        role = mapping.get('feature_dispositions', {}).get(folder.name, {}).get('category')
        if role in ('历史来源', '已退役专题', '已闭环专题'):
            exceptions.append(folder.name + ': historical/retired/closed source, not an active implementation feature')
            if role == '已退役专题':
                successor = mapping['feature_dispositions'][folder.name].get('successor')
                if not successor or not (root / successor).is_file():
                    errors.append(folder.name + ': missing retirement successor')
            markdown(folder / 'spec.md')
            continue
        for name in REQUIRED:
            p = folder / name
            if not p.is_file() or not p.stat().st_size:
                errors.append('Missing/empty artifact: ' + str(p.relative_to(root)))
            elif name.endswith('.md'):
                markdown(p)
        manifest = folder / 'integration.yaml'
        if manifest.is_file():
            # Deliberately only the established scalar navigation keys, not a YAML parser.
            # Pins, statuses, frozen evidence and arbitrary nested fields are never rewritten.
            for line in manifest.read_text().splitlines():
                match = re.match(r'^\s*([a-z_0-9]+):\s*(.*?)\s*$', line)
                if not match or match.group(1) not in NAV_KEYS:
                    continue
                value = re.split(r'\s+#', match.group(2), maxsplit=1)[0].strip().strip('\"\'')
                if not value or value in ('null', '~') or value.startswith(('[', '{', '*', '|', '>')):
                    errors.append('{}: unsupported navigation scalar {}'.format(
                        manifest.relative_to(root), match.group(1)))
                else:
                    target_exists(manifest, value)
        for name in ('README.md',):
            if (folder / name).is_file():
                markdown(folder / name)
        # The UI specification deliberately keeps its current detail in optimization/.
        if (folder / 'optimization/README.md').is_file():
            for p in sorted((folder / 'optimization').glob('*.md')):
                if p.name in ('README.md', 'spec.md', 'detailed-design.md', 'tasks.md', 'acceptance.md'):
                    markdown(p)
    if not feature:
        for name in ('AGENTS.md', 'api/AGENTS.md', 'web/AGENTS.md',
                     'docs/codex-project-map.md', 'docs/sdd-workflow.md',
                     'docs/knowledge-base/README.md', 'specs/README.md', 'specs/INDEX.md',
                     'web/prototypes/juyiting/specs/prototype-spec.md'):
            markdown(root / name)
    extra = {}
    if all_docs:
        if feature:
            raise ValueError('--all-docs cannot be combined with a feature ID')
        discovery = mapping.get('discovery')
        if not discovery:
            errors.append('Missing document discovery routes')
        else:
            rows = inventory(root, mapping)
            extra = {'catalog_documents': len(rows),
                     'role_counts': dict(sorted(Counter(r['role'] for r in rows).items())),
                     'unverified_references': [r['path'] for r in rows if r['role'] == 'REFERENCE_UNVERIFIED']}
            for row in rows:
                if row['default_search']:
                    markdown(root / row['path'])
                if not (root / row['entry']).is_file():
                    errors.append(row['path'] + ': missing responsible entry ' + row['entry'])
            for key in ('entrypoints', 'current_guides', 'selected_details',
                        'selected_versioned_contracts', 'baseline_references', 'source_attributions'):
                for name in discovery.get(key, []):
                    row = next((r for r in rows if r['path'] == name), None)
                    if row and row['role'] == 'HISTORICAL_CONTEXT' and name not in discovery.get('source_attributions', []):
                        errors.append('Cannot promote retired/historical topic as a current route: ' + name)
                        continue
                    if row and row['role'] == 'HISTORICAL_EVIDENCE':
                        errors.append('Cannot promote preserved evidence as a current route: ' + name)
                        continue
                    markdown(root / name)
            for name in discovery.get('regression', {}).values():
                if not (root / name).is_file():
                    errors.append('Missing regression route: ' + name)
            # Verify actual discoverability from the root rules, not only existence.
            # Follow local Markdown links among default-search docs (plus INDEX).
            nodes = {r['path'] for r in rows if r['default_search']}
            reachable, pending = set(), ['AGENTS.md']
            while pending:
                name = pending.pop()
                if name in reachable or name not in nodes:
                    continue
                reachable.add(name)
                p = root / name
                if not p.is_file():
                    continue
                for match in LINK.finditer(without_fences(p.read_text())):
                    url = urlsplit(match.group(1))
                    if url.scheme or url.netloc or not url.path:
                        continue
                    dest = (p.parent / unquote(url.path)).resolve()
                    try:
                        target = str(dest.relative_to(root))
                    except ValueError:
                        continue
                    if target in nodes:
                        pending.append(target)
            extra['reachable_default_documents'] = len(reachable)
            extra['unreachable_default_documents'] = sorted(nodes - reachable)
            for name in nodes - reachable:
                errors.append('Not discoverable from AGENTS.md: ' + name)
    return {'scope': ('all docs/specs Markdown roles, current links and root-rule reachability; '
                      if all_docs else 'current document entries and scalar navigation only; ') +
                     'not YAML schema, historical snapshot link validity, full content/source verification, '
                     'candidate matching or release acceptance',
            'features_checked': len(dirs), 'markdown_files_checked': len(checked),
            'local_targets_checked': links, 'exceptions': exceptions, 'errors': sorted(set(errors)),
            'result': 'FAIL' if errors else 'DOCUMENT_NAVIGATION_PASS',
            'stale_reference_links': stale_reference_links, **extra}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feature', nargs='?')
    parser.add_argument('--all-docs', action='store_true', help='Classify all docs/specs and check all current routes and reachability')
    parser.add_argument('--catalog', action='store_true', help='Print the live role catalog; no rewriting')
    parser.add_argument('--search', metavar='REGEX', help='Search default current routes with ripgrep')
    parser.add_argument('--history', action='store_true', help='Include history/unverified references in --search')
    args = parser.parse_args()
    if sum([args.all_docs, args.catalog, args.search is not None]) > 1 or (args.history and args.search is None) or (args.feature and (args.catalog or args.search is not None)):
        parser.error('Choose a feature check, --all-docs, --catalog, or --search [--history]')
    try:
        root = Path(__file__).resolve().parents[2]
        if args.search is not None:
            return search(root, args.search, args.history)
        if args.catalog:
            print(json.dumps(catalog(root), ensure_ascii=False, indent=2))
            return 0
        result = check(root, args.feature, all_docs=args.all_docs)
    except (ValueError, OSError, KeyError) as error:
        print('Document check error: {}'.format(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
