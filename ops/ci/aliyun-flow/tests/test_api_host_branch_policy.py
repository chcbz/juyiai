"""Execute actual host receipt predicates without filesystem/production side effects."""
import ast
import copy
from pathlib import Path
import re
import unittest

HOST = Path(__file__).resolve().parents[4] / 'ops/ci/aliyun-flow/host'


def predicate(filename, message):
    source = (HOST / filename).read_text()
    # Installer embeds Python in a heredoc; isolate its actual receipt validation.
    if filename.endswith('install'):
        source = source[source.index("flow = receipt.get('flow')"):]
        source = source[:source.index('\nrecords = {}')]
    tree = ast.parse(source)
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
               and any(isinstance(child, ast.Str) and child.s == message
                       for statement in node.body for child in ast.walk(statement))]
    assert len(matches) == 1, message
    return compile(ast.Expression(matches[0].test), filename, 'eval')


class HostBranchPolicyTest(unittest.TestCase):
    def setUp(self):
        self.deploy = predicate('cyf-api-flow-deploy', 'receipt source is not a clean build')
        self.install = predicate('cyf-api-flow-install', 'receipt release gate failed')
        self.source = dict(branch='develop', clean_before=True, clean_after=True,
                           commit_sha='a' * 40, tree_sha='b' * 40)
        self.flow = dict(organization_id='org', pipeline_id='5260799',
                         job_id='cloud_ci.api_ci', run_id='437', source_tip_sha='a' * 40)
        self.receipt = dict(status='success', gradle_exit_code=0, bridge_exit_code=0,
                            ticket_sha256='c' * 64)

    def rejected(self, gate):
        return eval(gate, dict(source=self.source, flow=self.flow, receipt=self.receipt,
                    files=[], expected_org='org', expected_pipeline='5260799',
                    expected_job='cloud_ci.api_ci', run_re=re.compile(r'^[1-9][0-9]*$'),
                    git_re=re.compile(r'^[0-9a-f]{40,64}$'),
                    sha256_re=re.compile(r'^[0-9a-f]{64}$')))

    def test_source_branch_is_provenance_not_a_release_allowlist(self):
        for branch in ('develop', 'master', 'codex/skill-package-memory',
                       'release/new-unlisted-name', ''):
            self.source['branch'] = branch
            for gate in (self.deploy, self.install):
                with self.subTest(branch=branch, gate=gate.co_filename):
                    self.assertFalse(self.rejected(gate))

    def test_both_gates_still_reject_unclean_source(self):
        for field in ('clean_before', 'clean_after'):
            for value in (False, None, 1):
                self.source[field] = value
                for gate in (self.deploy, self.install):
                    self.assertTrue(self.rejected(gate))
            self.source[field] = True

    def test_installer_still_rejects_invalid_identity_source_and_failed_build(self):
        for target, field, value in (
            (self.flow, 'organization_id', 'other'), (self.flow, 'pipeline_id', 'other'),
            (self.flow, 'job_id', 'other'), (self.flow, 'run_id', '0'),
            (self.flow, 'source_tip_sha', 'bad'), (self.source, 'commit_sha', 'bad'),
            (self.source, 'tree_sha', 'bad'), (self.receipt, 'status', 'failed'),
            (self.receipt, 'gradle_exit_code', 1), (self.receipt, 'bridge_exit_code', 1),
            (self.receipt, 'ticket_sha256', 'bad')):
            old = copy.deepcopy(target[field])
            target[field] = value
            with self.subTest(field=field):
                self.assertTrue(self.rejected(self.install))
            target[field] = old


if __name__ == '__main__':
    unittest.main()
