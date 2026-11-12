import hashlib
import importlib.util
import io
import pathlib
import tarfile
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'prepare-backend-jdk.py'
spec = importlib.util.spec_from_file_location('jdk_bootstrap', str(SCRIPT))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class BootstrapTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def archive(self, extras=()):
        archive = self.root / 'test.tar.gz'
        with tarfile.open(str(archive), 'w:gz') as out:
            member = tarfile.TarInfo('jdk/bin/javac')
            member.mode = 0o755
            member.size = 2
            out.addfile(member, io.BytesIO(b'ok'))
            for x in extras:
                out.addfile(x)
        return archive

    def test_fresh_and_no_executable_reuse(self):
        archive = self.archive()
        dest = self.root / 'extract'
        home = m.extract_fresh(archive, dest)
        self.assertEqual((home / 'bin/javac').read_bytes(), b'ok')
        with self.assertRaises(FileExistsError):
            m.extract_fresh(archive, dest)

    def test_traversal_and_absolute_member(self):
        for index, name in enumerate(('../escape', '/absolute')):
            with self.subTest(name=name):
                member = tarfile.TarInfo(name)
                with self.assertRaises(ValueError):
                    m.extract_fresh(self.archive([member]), self.root / ('d' + str(index)))

    def test_symlink_escape(self):
        member = tarfile.TarInfo('jdk/escape')
        member.type = tarfile.SYMTYPE
        member.linkname = '../../escape'
        with self.assertRaises(ValueError):
            m.extract_fresh(self.archive([member]), self.root / 'extract')

    def test_internal_link(self):
        member = tarfile.TarInfo('jdk/bin/java')
        member.type = tarfile.SYMTYPE
        member.linkname = 'javac'
        home = m.extract_fresh(self.archive([member]), self.root / 'extract')
        self.assertEqual((home / 'bin/java').read_bytes(), b'ok')

    def test_file_under_link(self):
        link = tarfile.TarInfo('jdk/lib'); link.type = tarfile.SYMTYPE; link.linkname = 'bin'
        file = tarfile.TarInfo('jdk/lib/other')
        with self.assertRaises(ValueError):
            m.extract_fresh(self.archive([link, file]), self.root / 'extract')

    def test_cache_rehash_and_no_network_on_hit(self):
        cache = self.root / 'cache'; cache.mkdir()
        data = b'archive'; digest = hashlib.sha256(data).hexdigest()
        target = cache / ('jdk-' + digest + '.tar.gz'); target.write_bytes(data)
        def no_network(*args, **kwargs):
            self.fail('cache hit must not download')
        self.assertEqual(m.verified_archive(cache, digest, '', no_network), (target, True))
        target.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            m.verified_archive(cache, digest, '', no_network)

    def test_cache_symlink_rejected(self):
        cache = self.root / 'cache'; cache.mkdir()
        real = self.root / 'data'; real.write_bytes(b'bytes')
        (cache / ('jdk-' + '0' * 64 + '.tar.gz')).symlink_to(real)
        with self.assertRaises(ValueError):
            m.verified_archive(cache, '0' * 64, '')

    def test_wrong_download_removed(self):
        class Response(io.BytesIO):
            def geturl(self): return 'https://example.invalid/archive'
        cache = self.root / 'cache'
        with self.assertRaises(ValueError):
            m.verified_archive(cache, '0' * 64, '', lambda *a, **k: Response(b'bad'))
        self.assertEqual(list(cache.iterdir()), [])

    def test_duplicate_and_special_members(self):
        duplicate = tarfile.TarInfo('jdk/bin/javac')
        special = tarfile.TarInfo('jdk/device'); special.type = tarfile.CHRTYPE
        for i, member in enumerate((duplicate, special)):
            with self.subTest(index=i):
                with self.assertRaises(ValueError):
                    m.extract_fresh(self.archive([member]), self.root / ('bad' + str(i)))

    def test_symlink_destination_rejected(self):
        real = self.root / 'real'; real.mkdir()
        alias = self.root / 'alias'; alias.symlink_to(real)
        with self.assertRaises(ValueError):
            m.extract_fresh(self.archive(), alias / 'fresh')

    def test_plaintext_redirect_rejected(self):
        class Response(io.BytesIO):
            def geturl(self): return 'http://example.invalid/archive'
        with self.assertRaises(ValueError):
            m.verified_archive(self.root / 'cache', hashlib.sha256(b'ok').hexdigest(), '',
                               lambda *a, **k: Response(b'ok'))

    def test_compile_only_policy(self):
        text = (SCRIPT.parent / 'flow-compile-cache.init.gradle').read_text()
        for required in ('CYF_FLOW_COMPILE_CACHE_OPT_IN', 'JavaCompile',
                         'outputs.cacheIf { false }', 'outputs.upToDateWhen { false }',
                         "task.name == 'bootJar'", "task.name == 'validateLayering'"):
            self.assertIn(required, text)


    def test_short_lived_jvm_is_opt_in_and_test_only(self):
        text = (SCRIPT.parent / 'flow-compile-cache.init.gradle').read_text()
        profile = text.split("if (System.getenv('CYF_FLOW_SHORT_LIVED_TEST_JVM') == '1') {", 1)[1]
        self.assertIn('withType(org.gradle.api.tasks.testing.Test)', profile)
        self.assertIn("task.jvmArgs '-XX:TieredStopAtLevel=1'", profile)
        self.assertNotIn('JavaExec', profile)
        self.assertNotIn('exclude', profile)
        self.assertNotIn('maxParallelForks', profile)


if __name__ == '__main__':
    unittest.main()
