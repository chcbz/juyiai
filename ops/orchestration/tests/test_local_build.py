"""Local fast-build controller checks. No Gradle, cloud, production, or network."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

S = importlib.util.spec_from_file_location('local_build', Path(__file__).resolve().parents[1] / 'local_build.py')
M = importlib.util.module_from_spec(S)
S.loader.exec_module(M)


class LocalBuildTest(unittest.TestCase):
    def command(self, extra=()):
        return M.build_command(Path('/source'), Path('/output'), Path('/private-cache'),
                               Path('/jdk'), {'tree': 'a' * 40}, 'OWN-TASK', extra)

    def test_original_orchestrator_guard_options_are_before_remainder(self):
        command = self.command()
        self.assertEqual(str(M.ORCHESTRATOR), command[2])
        self.assertLess(command.index('--fixture-digest'), command.index('OWN-TASK'))
        self.assertEqual('--', command[command.index('OWN-TASK') + 1])
        self.assertIn('--heavy', command)
        self.assertNotIn('--flow-ci', command)

    def test_fast_fail_keeps_security_layering_and_fresh_jar_boundaries(self):
        command = self.command()
        self.assertNotIn('--continue', command)
        self.assertIn('cn.jia.agent.security.AgentRuntimeSecurityIntegrationTest', command)
        for task in (':validateLayering', ':starter:bootJar', ':starter:publicArtifactVerifierTest',
                     ':starter:poiProductionRuntimeClasspathTest'):
            self.assertIn(task, command)
        self.assertIn(str(M.METADATA_INIT), command)
        self.assertIn('--build-cache', command)
        self.assertNotIn('-x', command)

    def test_selected_tests_do_not_require_full_test_source_compilation(self):
        command = self.command()
        self.assertIn(':agent:jia-agent-service:localReleaseBaseline', command)
        self.assertIn(':starter:localReleaseBaseline', command)
        self.assertNotIn(':agent:jia-agent-service:test', command)
        self.assertNotIn(':starter:test', command)
        text = M.LOCAL_INIT.read_text()
        self.assertIn("sourceSets.create('localReleaseBaseline')", text)
        self.assertIn("selected.each { include it }", text)
        self.assertIn("'CompileOnly', 'AnnotationProcessor'", text)
        self.assertIn("systemProperty 'cyf.sms.main-runtime-classpath'", text)
        self.assertNotIn('+= project.sourceSets.test.output', text)
        self.assertIn('slice.output + project.sourceSets.main.output +', text)

    def test_unrelated_diagnostics_are_not_default_or_compiled_in_release_slice(self):
        command = self.command()
        text = M.LOCAL_INIT.read_text()
        for name in ('cn.jia.diagnostics.StartupTimelineBootTest',
                     'cn.jia.config.ApiPerformanceMetricsConfigTest',
                     'cn.jia.config.ElasticsearchProductionHealthIsolationTest'):
            self.assertNotIn(name, command)
            self.assertNotIn(name.replace('.', '/') + '.java', text)
        self.assertIn('cn.jia.starter.AuthFormTransportTest', command)
        self.assertIn('cn.jia.config.SmsEmailRuntimeClasspathTest', command)
        self.assertIn('local-fast-baseline-v3-critical', command)
        self.assertNotIn('CYF_TASK_GRAPH ', text)
        for required in ('CYF_GRADLE_PHASE ', 'CYF_TASK_TIMING ',
                         "childEnvironment.remove('CYF_MAVEN_PASSWORD')", 'Nested Gradle Exec'):
            self.assertIn(required, text)

    def test_removed_default_tests_remain_explicit_regression_inputs(self):
        extra = [':starter:test', '--tests', 'cn.jia.config.ApiPerformanceMetricsConfigTest']
        command = self.command(extra)
        offset = command.index(':starter:test')
        self.assertEqual(command[offset:offset + len(extra)], extra)

    def test_bounded_parallelism_and_short_lived_build_jvm(self):
        command = self.command()
        self.assertIn('--max-workers=2', command)
        self.assertIn('--parallel', command)
        jvmargs = next(x for x in command if x.startswith('-Dorg.gradle.jvmargs='))
        self.assertIn('-Xmx768m', jvmargs)
        self.assertIn('-XX:ActiveProcessorCount=2', jvmargs)
        self.assertIn('-XX:TieredStopAtLevel=1', jvmargs)
        self.assertNotIn('-XX:-TieredCompilation', jvmargs)

    def test_local_api_package_has_uncompressed_tar_name(self):
        text = Path(M.__file__).read_text()
        self.assertIn("output / 'api.tar'", text)
        self.assertNotIn("output / 'api.tgz'", text)

    def test_offline_is_explicit_and_cannot_silently_fallback_to_network(self):
        self.assertNotIn('--offline', self.command())
        command = M.build_command(Path('/source'), Path('/output'), Path('/private-cache'),
                                  Path('/jdk'), {'tree': 'a' * 40}, 'OWN-TASK', offline=True)
        self.assertIn('--offline', command)
        self.assertLess(command.index('--offline'), command.index(':starter:bootJar'))

    def test_extra_regressions_are_not_dropped_or_rewritten(self):
        extra = [':user:jia-user-service:test', '--tests', 'cn.jia.user.Example']
        command = self.command(extra)
        offset = command.index(extra[0])
        self.assertEqual(extra, command[offset:offset + len(extra)])
        self.assertLess(offset, command.index(':starter:bootJar'))

    def test_init_script_c1_remains_scoped_to_test_tasks(self):
        text = M.LOCAL_INIT.read_text()
        self.assertNotIn('CYF_FLOW_GRADLE_ACTIVE', text)
        self.assertIn("CYF_LOCAL_GRADLE_ACTIVE", text)
        self.assertIn("tasks.withType(org.gradle.api.tasks.testing.Test).configureEach", text)
        self.assertIn("'-XX:TieredStopAtLevel=1'", text)
        self.assertIn('verifyOpenCv(artifact)', text)
        self.assertIn("childEnvironment.remove('CYF_MAVEN_PASSWORD')", text)

    def test_pin_hook_resolves_only_opencv_artifacts_not_entire_dependency_graph(self):
        text = M.LOCAL_INIT.read_text()
        hook = text.split('configuration.incoming.afterResolve { incoming ->', 1)[1].split(
            '// These properties', 1)[0]
        self.assertIn('incoming.artifactView {', hook)
        self.assertIn('componentFilter { component ->', hook)
        self.assertIn('component instanceof ModuleComponentIdentifier', hook)
        self.assertIn("component.group == 'org.opencv' && component.module == 'opencv'", hook)
        self.assertNotIn('component.version', hook)
        self.assertNotIn('incoming.artifacts.artifacts', hook)
        self.assertNotIn('lenient', hook)
        self.assertIn('verifyOpenCv(artifact)', hook)
        # Filtering artifacts must not remove pin, provenance, or receipt guards.
        for required in ("component.version != '4.5.5'", 'pinnedOpenCvSha256',
                         'jar.length() != pinnedOpenCvSize', 'opencv-resolved.json',
                         "excludeModule('org.opencv', 'opencv')"):
            self.assertIn(required, text)

    def test_fresh_outputs_skip_incremental_analysis_not_standard_compile_cache(self):
        text = M.LOCAL_INIT.read_text()
        hook = text.split('project.tasks.withType(org.gradle.api.tasks.compile.JavaCompile).configureEach {', 1)[1].split('project.configurations.configureEach', 1)[0]
        self.assertIn('options.incremental = false', hook)
        self.assertNotIn('cacheIf', hook)
        self.assertNotIn('upToDateWhen', hook)
        self.assertNotIn('compilerArgs', hook)
        self.assertIn('--build-cache', self.command())
        self.assertIn('fresh per-batch output is required', Path(M.__file__).read_text())

    def test_mandatory_fresh_tasks_skip_only_unused_state_snapshots(self):
        local = M.LOCAL_INIT.read_text()
        metadata = M.METADATA_INIT.read_text()
        self.assertIn("doNotTrackState('Local release tests always execute in a fresh batch')", local)
        self.assertIn("candidate instanceof org.gradle.api.tasks.testing.Test", metadata)
        self.assertIn("candidate.doNotTrackState('Local release tests always execute in a fresh batch')", metadata)
        self.assertIn("task.doNotTrackState('Local release bootJar must be created and verified fresh')", metadata)
        self.assertIn('new java.security.DigestInputStream(stream, hash).transferTo', metadata)
        self.assertIn("publicArtifactVerifier: 'bootJar-original-doLast-completed'", metadata)
        self.assertIn('CYF_LOCAL_RELEASE_BUILD_NOT_FRESH', metadata)

    def test_fixed_source_rejects_dirty_tree_and_binds_full_commit_tree(self):
        with tempfile.TemporaryDirectory(prefix='cyf-local-build-unit-') as temporary:
            source = Path(temporary)
            def run(*args):
                return subprocess.check_output(['git', '-C', str(source)] + list(args),
                                               stderr=subprocess.DEVNULL).decode().strip()
            run('init'); run('config', 'user.name', 'test'); run('config', 'user.email', 'test@example.invalid')
            (source / 'build.gradle').write_text('// fixture\n')
            run('add', '.'); run('commit', '-qm', 'fixture')
            identity = M.fixed_source(source)
            self.assertEqual(run('rev-parse', 'HEAD'), identity['commit'])
            self.assertEqual(run('rev-parse', 'HEAD^{tree}'), identity['tree'])
            (source / 'build.gradle').write_text('// dirty\n')
            with self.assertRaisesRegex(ValueError, 'dirty'):
                M.fixed_source(source)


if __name__ == '__main__':
    unittest.main()
