"""Tests for WhenChanged.run_command() - execution and run_once logic."""
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def make_wc(files=None, command=None, **kwargs):
    files = files or ['/tmp/test.py']
    command = command or ['echo', 'changed']
    with patch('whenchanged.whenchanged.Observer'):
        wc = WhenChanged(
            files=files,
            command=command,
            run_once=kwargs.get('run_once', False),
            verbose_mode=kwargs.get('verbose_mode', 0),
            quiet_mode=kwargs.get('quiet_mode', False),
            kill_mode=kwargs.get('kill_mode', False),
            debounce_delay=kwargs.get('debounce_delay', 0),
        )
    return wc


class TestRunCommand:
    def test_command_is_called(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], command=['echo', 'ok'])
        wc.set_envvar('event', 'file_modified')
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            wc.run_command(str(f))
            mock_popen.assert_called_once()

    def test_percent_f_replaced(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], command=['echo', '%f'])
        wc.set_envvar('event', 'file_modified')
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            wc.run_command(str(f))
            args = mock_popen.call_args[0][0]
            assert str(f) in args

    def test_run_once_skips_if_not_modified(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], run_once=True)
        wc.set_envvar('event', 'file_modified')
        wc.last_run = time.time() + 10  # simule un run récent
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            wc.run_command(str(f))
            mock_popen.assert_not_called()

    def test_run_once_runs_if_modified_after(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], run_once=True)
        wc.set_envvar('event', 'file_modified')
        wc.last_run = 0  # jamais exécuté
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            wc.run_command(str(f))
            mock_popen.assert_called_once()

    def test_last_run_updated(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)])
        wc.set_envvar('event', 'file_modified')
        before = time.time()
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            wc.run_command(str(f))
        assert wc.last_run >= before

    def test_kill_mode_terminates_previous_process(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], kill_mode=True)
        wc.set_envvar('event', 'file_modified')
        old_proc = MagicMock()
        old_proc.wait.return_value = 0
        wc._current_process = old_proc
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            wc.run_command(str(f))
            old_proc.terminate.assert_called_once()

    def test_quiet_mode_suppresses_stdout(self, tmp_path):
        f = tmp_path / 'test.py'
        f.write_text('hello')
        wc = make_wc(files=[str(f)], quiet_mode=True)
        wc.set_envvar('event', 'file_modified')
        with patch('whenchanged.whenchanged.subprocess.Popen') as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            with patch('builtins.open') as mock_open:
                wc.run_command(str(f))
                mock_open.assert_called_with(os.devnull, 'wb')
