import importlib.util
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('reopen', str(Path(__file__).resolve().parents[1] / 'mysql_error_log_reopen.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReopenTests(unittest.TestCase):
    def test_check_does_not_signal(self):
        with patch.object(m, 'identity', return_value=(2017, '123')), patch.object(m, 'log_open', return_value=True), self.context(), patch.object(m.os, 'kill') as kill:
            self.assertEqual(m.run('check'), 2017)
            kill.assert_not_called()

    def test_check_rejects_stale_fd(self):
        with patch.object(m, 'identity', return_value=(2017, '123')), patch.object(m, 'log_open', return_value=False), self.context():
            with self.assertRaises(ValueError):
                m.run('check')

    def context(self):
        return patch.object(m.subprocess, 'check_output', return_value=b'mysqld Ver 8.0.21 for Linux')

    def test_reopen_signals_only_actual_server(self):
        with patch.object(m, 'identity', return_value=(2017, '123')), patch.object(m, 'log_open', side_effect=[False, True]), self.context(), patch.object(m.os, 'kill') as kill, patch.object(m.time, 'sleep'):
            self.assertEqual(m.run('reopen'), 2017)
            kill.assert_called_once_with(2017, signal.SIGUSR1)

    def test_server_replaced_before_signal(self):
        with patch.object(m, 'identity', side_effect=[(2017, '123'), (2017, '999')]), self.context(), patch.object(m.os, 'kill') as kill:
            with self.assertRaises(ValueError):
                m.run('reopen')
            kill.assert_not_called()

    def test_unsupported_or_unknown_version_never_signalled(self):
        for mode in ('check', 'reopen'):
            for version in (b'mysqld Ver 8.0.18', b'mysqld Ver 5.7.44', b'unknown'):
                with patch.object(m, 'identity', return_value=(2017, '123')), patch.object(m.subprocess, 'check_output', return_value=version), patch.object(m.os, 'kill') as kill:
                    with self.assertRaises(ValueError):
                        m.run(mode)
                    kill.assert_not_called()

    def test_acknowledgement_failure_preserves_error(self):
        with patch.object(m, 'identity', return_value=(2017, '123')), patch.object(m, 'log_open', return_value=False), self.context(), patch.object(m.os, 'kill'), patch.object(m.time, 'monotonic', side_effect=[0, 6]):
            with self.assertRaisesRegex(ValueError, 'preserve uncompressed'):
                m.run('reopen')

    def test_restarted_server_during_acknowledgement_is_not_success(self):
        with patch.object(m, 'identity', side_effect=[(2017, '1'), (2017, '1'), (2017, '2')]), self.context(), patch.object(m.os, 'kill'):
            with self.assertRaises(ValueError):
                m.run('reopen')

    def test_identity_and_log_inode_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); proc = root / 'proc'; server = proc / '2017'; server.mkdir(parents=True)
            pid = root / 'mysql.pid'; pid.write_text('2017\n')
            (server / 'exe').symlink_to('/expected/mysqld')
            (server / 'cmdline').write_bytes(b'mysqld\0--defaults-file=/expected/my.cnf\0')
            (server / 'cgroup').write_text('1:name=systemd:/system.slice/mysql.service\n')
            (server / 'stat').write_text('2017 (mysqld) ' + ' '.join(['S'] + ['0'] * 18 + ['123']))
            log = root / 'mysql.log'; log.write_text('content')
            fd = server / 'fd'; fd.mkdir(); (fd / '1').symlink_to(log)
            class User:
                pw_uid = os.getuid()
            with patch.multiple(m, PROC=proc, PID_FILE=pid, EXE='/expected/mysqld', CONFIG_ARG=b'--defaults-file=/expected/my.cnf', LOG=log), patch.object(m.pwd, 'getpwnam', return_value=User()):
                self.assertEqual(m.identity(), (2017, '123'))
                self.assertTrue(m.log_open(2017))
                (server / 'exe').unlink(); (server / 'exe').symlink_to('/expected/mysqld_safe')
                with self.assertRaises(ValueError):
                    m.identity()
                (server / 'exe').unlink(); (server / 'exe').symlink_to('/expected/mysqld')
                (server / 'cmdline').write_bytes(b'mysqld\0--defaults-file=/other.cnf\0')
                with self.assertRaises(ValueError):
                    m.identity()
                (server / 'cmdline').write_bytes(b'mysqld\0--defaults-file=/expected/my.cnf\0')
                (server / 'cgroup').write_text('1:name=systemd:/other.service\n')
                with self.assertRaises(ValueError):
                    m.identity()
                log.rename(root / 'old'); log.write_text('new')
                # FD remains on the old inode, not a path that follows the new log.
                (fd / '1').unlink(); (fd / '1').symlink_to(root / 'old')
                self.assertFalse(m.log_open(2017))


if __name__ == '__main__':
    unittest.main()
