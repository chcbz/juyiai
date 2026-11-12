"""Narrow transport contract; live API authentication is verified separately."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
CONFIG = ROOT / 'ops/ci/aliyun-flow/host/nginx'


class RuntimeNativeNginxTest(unittest.TestCase):
    def setUp(self):
        self.text = (CONFIG / 'cyf-runtime-native-locations.conf').read_text()
        self.routes = [(re.compile(path), re.compile(method)) for path, method in re.findall(
            r'location ~ "([^"]+)" \{\s*if \(\$request_method !~ "([^"]+)"\)', self.text)]

    def accepts(self, method, path):
        return any(p.fullmatch(path) and m.fullmatch(method) for p, m in self.routes)

    def test_complete_native_contract(self):
        self.assertEqual(len(self.routes), 17)
        reads = [
            '/tasks/workspace-executions/commands', '/tasks/conversation-executions/commands',
            '/skill-installations/a/package', '/tasks/a/runs/b/inputs',
            '/tasks/a/runs/b/inputs/c/content', '/chat/requests/a/turns/b/inspection/inputs/c/content',
            '/tasks/a/work-items/b/reassignments/c/commands/d/lease',
            '/tasks/a/work-items/b/reassignments/c/commands/d/result-commit',
        ]
        writes = ['/tasks/a/runs/b/' + end for end in (
            'start', 'failure', 'outputs/c/content', 'output-commits/c',
            'conversation/inputs', 'conversation/inputs/c/content',
            'conversation/lease', 'conversation/lease/renew', 'conversation/resume',
            'conversation/usage', 'conversation/provider-usage', 'conversation/effects/c/start', 'conversation/effects/c/result',
            'conversation/failure', 'conversation/result-commits/c',
            'conversation/outputs/c/content')]
        reads += ['/position-skills', '/position-skills/a/receipt', '/chat/requests/a/turns/b/tools',
                  '/chat/requests/a/turns/b/materials/inputs/c/content']
        writes += ['/tasks/a/work-items/b/reassignments/c/commands/d/result-commit',
                   '/position-skills/results', '/chat/requests/a/turns/b/tools/skill_install',
                   '/chat/dispatches/a/usage', '/skill-management/results', '/hosting-leases/a/knowledge-usage']
        for method, paths in [('GET', reads), ('POST', writes)]:
            for path in paths:
                with self.subTest(method=method, path=path):
                    self.assertTrue(self.accepts(method, '/internal/agent' + path))
                    for wrong in ('DELETE', 'PUT', 'PATCH', 'OPTIONS', 'HEAD'):
                        self.assertFalse(self.accepts(wrong, '/internal/agent' + path))
                    other = 'POST' if method == 'GET' else 'GET'
                    if not path.endswith('/result-commit'):
                        self.assertFalse(self.accepts(other, '/internal/agent' + path))

    def test_archive_maintenance_methods(self):
        for suffix in ('', '/a/source', '/a/result'):
            self.assertTrue(self.accepts('GET', '/internal/archive/v1/jobs' + suffix))
        self.assertTrue(self.accepts('POST', '/internal/archive/v1/jobs/a/result'))
        for method, path in [('POST', '/internal/archive/v1/jobs'), ('POST', '/internal/archive/v1/jobs/a/source'),
                             ('DELETE', '/internal/archive/v1/jobs/a/result')]:
            self.assertFalse(self.accepts(method, path))

    def test_retired_execution_routes_not_restored(self):
        for path in ('/tasks/conversation-executions/controlled-image-v3-commands',
                     '/tasks/a/runs/b/conversation/inputs-v3', '/tasks/a/runs/b/conversation/provider-start',
                     '/tasks/a/runs/b/conversation/provider-start-controlled-image-v3',
                     '/tasks/a/runs/b/conversation/output-commits/c'):
            for method in ('GET', 'POST'):
                self.assertFalse(self.accepts(method, '/internal/agent' + path))

    def test_unknown_paths_and_invalid_ids_not_forwarded(self):
        for path in ('/internal/health', '/internal/agent/admin', '/internal/agent/tasks',
                     '/internal/agent/tasks/workspace-executions/commands/extra',
                     '/internal/agent/tasks/a/runs/b/delete',
                     '/internal/agent/tasks/../runs/b/inputs',
                     '/internal/agent/tasks/a%2fb/runs/c/inputs',
                     '/internal/agent/tasks//runs/b/inputs',
                     '/internal/agent/tasks/' + 'a' * 101 + '/runs/b/inputs'):
            for method in ('GET', 'POST'):
                self.assertFalse(self.accepts(method, path), (method, path))
        self.assertTrue(self.accepts('GET', '/internal/agent/tasks/' + 'a' * 100 + '/runs/b/inputs'))

    def test_transport_does_not_replace_identity(self):
        text = (CONFIG / 'cyf-runtime-native-proxy.conf').read_text()
        self.assertIn('proxy_pass_request_headers on;', text)
        self.assertIn('proxy_pass http://127.0.0.1:10018;', text)
        self.assertIn('proxy_cache off;', text)
        for directive in ('Authorization', 'X-Agent-', 'Origin', 'Cookie'):
            self.assertNotRegex(text, r'proxy_set_header\s+' + directive)
        self.assertNotRegex(text, r'(?m)^\s*rewrite\s')
        self.assertNotIn('location /internal', self.text)


if __name__ == '__main__':
    unittest.main()
