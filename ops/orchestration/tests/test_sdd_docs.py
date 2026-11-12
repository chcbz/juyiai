import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('sdd_docs', Path(__file__).resolve().parents[1] / 'sdd_docs.py')
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


class DocumentNavigationTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cyf-sdd-docs-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.put('docs/sdd-document-map.json', json.dumps({'removed': {}, 'feature_dispositions': {}}))
        self.folder = self.root / 'specs/example'
        for name in D.REQUIRED:
            self.put('specs/example/' + name, '# Example\n' if name.endswith('.md') else
                     'feature_id: example\nstatus: draft\npinned_revisions:\n  api_commit: null\n')

    def put(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def run_check(self):
        return D.check(self.root, 'example')

    def test_unpinned_draft_is_document_only_pass_without_git(self):
        result = self.run_check()
        self.assertEqual(result['result'], 'DOCUMENT_NAVIGATION_PASS')
        self.assertIn('not YAML schema', result['scope'])

    def test_missing_artifact_fails(self):
        (self.folder / 'tasks.md').unlink()
        self.assertTrue(self.run_check()['errors'])

    def test_query_and_fragment_do_not_become_filename(self):
        self.put('specs/example/page.html', '<html></html>')
        self.put('specs/example/spec.md', '[page](page.html?scenario=results#chat)')
        self.assertFalse(self.run_check()['errors'])

    def test_remote_links_and_code_examples_are_not_local_targets(self):
        self.put('specs/example/spec.md', '[remote](https://example.invalid/a)\n```md\n[x](missing.md)\n```\n')
        self.assertFalse(self.run_check()['errors'])

    def test_missing_link_fails(self):
        self.put('specs/example/spec.md', '[x](missing.md)')
        self.assertTrue(self.run_check()['errors'])

    def test_current_navigation_is_checked(self):
        self.put('specs/example/integration.yaml', 'current_design: "absent.md"\n')
        self.assertTrue(self.run_check()['errors'])

    def test_unsupported_navigation_scalar_fails(self):
        self.put('specs/example/integration.yaml', 'current_design: [design.md]\n')
        self.assertTrue(self.run_check()['errors'])

    def test_navigation_fragment_and_comment(self):
        self.put('specs/example/integration.yaml', 'clarifications: design.md#details # source\n')
        self.assertFalse(self.run_check()['errors'])

    def test_missing_mapping_successor_fails(self):
        self.put('docs/sdd-document-map.json', json.dumps({'removed': {'specs/example/old.md': 'specs/example/missing.md'}}))
        self.assertTrue(self.run_check()['errors'])

    def test_deleted_inline_reference_fails(self):
        self.put('docs/sdd-document-map.json', json.dumps({'removed': {'specs/example/old.md': 'specs/example/design.md'}}))
        self.put('specs/example/spec.md', '`specs/example/old.md`')
        self.assertTrue(self.run_check()['errors'])

    def test_historical_snapshot_and_pin_unchanged(self):
        p = self.put('specs/example/evidence/before/spec.md', '[old](missing.md)')
        original = (self.folder / 'integration.yaml').read_bytes()
        self.assertFalse(self.run_check()['errors'])
        self.assertEqual((self.folder / 'integration.yaml').read_bytes(), original)
        self.assertEqual(p.read_text(), '[old](missing.md)')

    def test_source_summary_is_explicit_exception(self):
        self.put('docs/sdd-document-map.json', json.dumps({'removed': {}, 'feature_dispositions': {'example': {'category': '历史来源'}}}, ensure_ascii=False))
        for name in D.REQUIRED[1:]:
            (self.folder / name).unlink()
        result = self.run_check()
        self.assertFalse(result['errors'])
        self.assertEqual(len(result['exceptions']), 1)

    def test_invalid_and_unknown_ids_rejected(self):
        for name in ('../example', 'unknown', '/tmp'):
            with self.assertRaises(ValueError):
                D.check(self.root, name)


class DocumentDiscoveryTest(unittest.TestCase):
    def put(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='cyf-doc-discovery-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.mapping = {'removed': {}, 'feature_dispositions': {}, 'discovery': {
            'entrypoints': ['AGENTS.md', 'docs/README.md', 'specs/INDEX.md'],
            'current_guides': [], 'selected_details': [],
            'selected_versioned_contracts': [], 'baseline_references': [],
            'history_routes': {}, 'regression': {}}}
        self.save_mapping()
        for name in D.REQUIRED:
            self.put('specs/example/' + name, '# Example\n' if name.endswith('.md') else 'feature_id: example\n')
        self.put('specs/example/spec.md', '[design](design.md) [tasks](tasks.md) [acceptance](acceptance.md)\n')
        self.put('AGENTS.md', '[docs](docs/README.md)\n')
        self.put('docs/README.md', '[index](../specs/INDEX.md)\n')
        self.put('specs/INDEX.md', '[example](example/spec.md)\n')
        for name in ('api/AGENTS.md', 'web/AGENTS.md', 'docs/codex-project-map.md',
                     'docs/sdd-workflow.md', 'docs/knowledge-base/README.md',
                     'specs/README.md', 'web/prototypes/juyiting/specs/prototype-spec.md'):
            self.put(name, '# Navigation fixture\n')

    def save_mapping(self):
        self.put('docs/sdd-document-map.json', json.dumps(self.mapping))

    def rows(self):
        return {r['path']: r for r in D.inventory(self.root)}

    def check(self):
        return D.check(self.root, all_docs=True)

    def test_current_feature_reachable_from_root_rules(self):
        result = self.check()
        self.assertFalse(result['errors'])
        self.assertEqual(result['reachable_default_documents'], 7)

    def test_all_docs_needs_discovery_metadata(self):
        del self.mapping['discovery']
        self.save_mapping()
        self.assertIn('Missing document discovery routes', self.check()['errors'])

    def test_orphan_current_guide_is_reported(self):
        self.put('docs/current-guide.md', '# Current\n')
        self.mapping['discovery']['current_guides'] = ['docs/current-guide.md']
        self.save_mapping()
        self.assertIn('Not discoverable from AGENTS.md: docs/current-guide.md', self.check()['errors'])

    def test_missing_selected_document_fails(self):
        self.mapping['discovery']['selected_details'] = ['specs/example/missing.md']
        self.save_mapping()
        self.assertTrue(any('Missing entry' in e for e in self.check()['errors']))

    def test_new_feature_not_in_index_is_undiscoverable(self):
        for name in D.REQUIRED:
            self.put('specs/other/' + name, '# Other\n' if name.endswith('.md') else 'feature_id: other\n')
        self.assertIn('Not discoverable from AGENTS.md: specs/other/spec.md', self.check()['errors'])

    def test_evidence_is_not_promoted_even_if_explicitly_selected(self):
        self.put('specs/example/evidence/before/spec.md', '[old](missing.md)\n')
        self.mapping['discovery']['current_guides'] = ['specs/example/evidence/before/spec.md']
        self.save_mapping()
        row = self.rows()['specs/example/evidence/before/spec.md']
        self.assertEqual(row['role'], 'HISTORICAL_EVIDENCE')
        self.assertFalse(row['default_search'])
        result = self.check()
        self.assertTrue(any('Cannot promote preserved evidence' in e for e in result['errors']))
        self.assertFalse(any('missing target missing.md' in e for e in result['errors']))

    def test_historical_links_do_not_masquerade_as_current_failures(self):
        p = self.put('docs/implementation/archive/old.md', '[old](gone.md)\n')
        before = p.read_bytes()
        self.assertFalse(self.check()['errors'])
        self.assertEqual(before, p.read_bytes())
        self.assertEqual(self.rows()['docs/implementation/archive/old.md']['role'], 'HISTORICAL_EVIDENCE')

    def test_unknown_note_remains_unverified(self):
        self.put('specs/example/support-note.md', '# Unverified\n')
        row = self.rows()['specs/example/support-note.md']
        self.assertEqual(row['role'], 'REFERENCE_UNVERIFIED')
        self.assertFalse(row['default_search'])
        self.assertEqual(row['entry'], 'specs/example/spec.md')
        self.assertIn(row['path'], self.check()['unverified_references'])

    def test_explicit_current_contract_can_have_old_date(self):
        self.put('specs/example/detail-20260101.md', '# Selected contract\n')
        self.mapping['discovery']['selected_details'] = ['specs/example/detail-20260101.md']
        self.save_mapping()
        row = self.rows()['specs/example/detail-20260101.md']
        self.assertEqual(row['role'], 'CURRENT_DETAIL')
        self.assertIn('verify actual implementation', row['validity'])

    def test_unselected_wire_does_not_become_current_protocol(self):
        self.put('specs/example/old-contract-v1.md', '# Old protocol\n')
        row = self.rows()['specs/example/old-contract-v1.md']
        self.assertEqual(row['role'], 'UNSELECTED_VERSIONED_REFERENCE')
        self.assertFalse(row['default_search'])

    def test_frozen_core_remains_discoverable_without_current_pass_claim(self):
        self.put('specs/example/core-ui-regression.md', '# Frozen\n')
        self.mapping['discovery']['regression'] = {'frozen_core': 'specs/example/core-ui-regression.md'}
        self.save_mapping()
        row = self.rows()['specs/example/core-ui-regression.md']
        self.assertEqual(row['role'], 'FROZEN_REGRESSION')
        self.assertTrue(row['default_search'])
        self.assertIn('historical candidate scope only', row['validity'])

    def test_missing_current_link_still_fails(self):
        self.put('specs/example/spec.md', '[missing](missing.md)\n')
        self.assertTrue(any('missing target missing.md' in e for e in self.check()['errors']))

    def test_known_stale_baseline_is_an_explicit_warning(self):
        self.put('docs/baseline.md', '[old](old-source.java)\n')
        self.mapping['discovery']['baseline_references'] = ['docs/baseline.md']
        self.mapping['discovery']['known_stale_baseline_links'] = {'docs/baseline.md': ['old-source.java']}
        self.put('docs/README.md', '[index](../specs/INDEX.md) [baseline](baseline.md)\n')
        self.save_mapping()
        result = self.check()
        self.assertFalse(result['errors'])
        self.assertEqual(result['stale_reference_links'][0]['source'], 'docs/baseline.md')

    def test_stale_exception_cannot_hide_missing_current_guide_link(self):
        self.put('docs/guide.md', '[gone](gone.java)\n')
        self.mapping['discovery']['current_guides'] = ['docs/guide.md']
        self.mapping['discovery']['known_stale_baseline_links'] = {'docs/guide.md': ['gone.java']}
        self.save_mapping()
        self.assertTrue(any('missing target gone.java' in e for e in self.check()['errors']))

    def test_history_route_must_have_a_real_responsible_entry(self):
        self.put('docs/old-plan.md', '# Old\n')
        self.mapping['discovery']['history_routes'] = {'docs/old-plan.md': 'specs/missing/spec.md'}
        self.save_mapping()
        self.assertTrue(any('missing responsible entry' in e for e in self.check()['errors']))

    def test_template_and_content_source_are_not_execution_guidance(self):
        self.put('specs/_template/spec.md', '# Template\n')
        self.put('specs/example/content/ATTRIBUTION.md', '# Provenance\n')
        self.mapping['discovery']['source_attributions'] = ['specs/example/content/ATTRIBUTION.md']
        self.save_mapping()
        self.assertEqual(self.rows()['specs/_template/spec.md']['role'], 'TEMPLATE')
        self.assertEqual(self.rows()['specs/example/content/ATTRIBUTION.md']['role'], 'CONTENT_SOURCE')
        self.assertFalse(self.rows()['specs/example/content/ATTRIBUTION.md']['default_search'])

    def test_external_symlink_directory_is_not_cataloged(self):
        with tempfile.TemporaryDirectory(prefix='cyf-external-docs-') as target:
            Path(target, 'outside.md').write_text('# Outside\n')
            (self.root / 'docs/outside').symlink_to(target, target_is_directory=True)
            self.assertNotIn('docs/outside/outside.md', self.rows())

    def test_search_excludes_history_by_default_and_uses_literal_argv(self):
        from unittest.mock import patch
        self.put('docs/implementation/archive/old.md', '# token\n')
        with patch.object(D.subprocess, 'call', return_value=0) as call:
            self.assertEqual(D.search(self.root, '--glob=*.secret'), 0)
            args = call.call_args[0][0]
            self.assertEqual(args[:5], ['rg', '-n', '-i', '--', '--glob=*.secret'])
            self.assertNotIn('docs/implementation/archive/old.md', args)
        with patch.object(D.subprocess, 'call', return_value=0) as call:
            D.search(self.root, 'token', include_history=True)
            self.assertIn('docs/implementation/archive/old.md', call.call_args[0][0])

    def retire_example(self):
        self.mapping['feature_dispositions']['example'] = {
            'category': '已退役专题', 'successor': 'docs/README.md'}
        self.save_mapping()

    def test_retired_topic_and_new_notes_do_not_reenter_default_search(self):
        self.retire_example()
        self.put('specs/example/new-note.md', '# Old follow-up')
        for row in self.rows().values():
            if row['path'].startswith('specs/example/'):
                self.assertEqual(row['role'], 'HISTORICAL_CONTEXT')
                self.assertFalse(row['default_search'])
                self.assertEqual(row['entry'], 'docs/README.md')
        self.assertFalse(self.check()['errors'])

    def test_retired_topic_cannot_be_explicitly_promoted(self):
        self.retire_example()
        self.mapping['discovery']['selected_details'] = ['specs/example/spec.md']
        self.save_mapping()
        self.assertTrue(any('Cannot promote retired/historical' in e for e in self.check()['errors']))

    def test_retired_topic_needs_real_successor(self):
        self.retire_example()
        self.mapping['feature_dispositions']['example']['successor'] = 'specs/gone/spec.md'
        self.save_mapping()
        self.assertTrue(any('missing retirement successor' in e for e in self.check()['errors']))

    def test_retired_topic_preserves_evidence_role_and_bytes(self):
        p = self.put('specs/example/evidence/test.md', '[old](missing.md)')
        before = p.read_bytes()
        self.retire_example()
        self.assertEqual(self.rows()['specs/example/evidence/test.md']['role'], 'HISTORICAL_EVIDENCE')
        self.assertFalse(self.check()['errors'])
        self.assertEqual(before, p.read_bytes())

    def test_old_baseline_requires_explicit_history_search(self):
        from unittest.mock import patch
        self.put('docs/baseline.md', '# Old source snapshot')
        self.mapping['discovery']['baseline_references'] = ['docs/baseline.md']
        self.save_mapping()
        self.assertEqual(self.rows()['docs/baseline.md']['role'], 'BASELINE_REFERENCE')
        self.assertFalse(self.rows()['docs/baseline.md']['default_search'])
        with patch.object(D.subprocess, 'call', return_value=0) as call:
            D.search(self.root, 'snapshot')
            self.assertNotIn('docs/baseline.md', call.call_args[0][0])
            D.search(self.root, 'snapshot', include_history=True)
            self.assertIn('docs/baseline.md', call.call_args[0][0])

    def test_catalog_is_read_only(self):
        import hashlib
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        result = D.catalog(self.root)
        after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(result['documents'], sum(result['role_counts'].values()))


if __name__ == '__main__':
    unittest.main()
