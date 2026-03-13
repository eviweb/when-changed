"""Tests for CLI argument parsing in main()."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def run_main_with_args(args):
    """Helper: run main() capturing WhenChanged instantiation args."""
    with patch('sys.argv', ['when-changed'] + args), \
         patch('whenchanged.whenchanged.WhenChanged') as MockWC:
        MockWC.return_value.run = MagicMock()
        try:
            from whenchanged.whenchanged import main
            main()
        except SystemExit:
            pass
        return MockWC


class TestCLIParsing:
    def test_basic_file_and_command(self):
        MockWC = run_main_with_args(['file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[0] == ['file.py']   # files
        assert args[1] == ['echo', 'ok']  # command

    def test_flag_r_sets_recursive(self):
        MockWC = run_main_with_args(['-r', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[2] == True  # recursive

    def test_flag_1_sets_run_once(self):
        MockWC = run_main_with_args(['-1', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[3] == True  # run_once

    def test_flag_s_sets_run_at_start(self):
        MockWC = run_main_with_args(['-s', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[4] == True  # run_at_start

    def test_flag_v_sets_verbose(self):
        MockWC = run_main_with_args(['-v', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[5] == 1  # verbose_mode

    def test_flag_vvv_sets_verbose_3(self):
        MockWC = run_main_with_args(['-vvv', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[5] == 3

    def test_flag_q_sets_quiet(self):
        MockWC = run_main_with_args(['-q', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[6] == True  # quiet_mode

    def test_flag_k_sets_kill_mode(self):
        MockWC = run_main_with_args(['-k', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[7] == True  # kill_mode

    def test_flag_d_sets_debounce(self):
        MockWC = run_main_with_args(['-d', '0.5', 'file.py', 'echo', 'ok'])
        args, kwargs = MockWC.call_args
        assert args[8] == 0.5  # debounce_delay

    def test_flag_c_multifile(self):
        MockWC = run_main_with_args(['a.py', 'b.py', '-c', 'make', 'test'])
        args, kwargs = MockWC.call_args
        assert args[0] == ['a.py', 'b.py']
        assert args[1] == ['make', 'test']

    def test_no_args_exits(self):
        with patch('sys.argv', ['when-changed']):
            with pytest.raises(SystemExit):
                from whenchanged.whenchanged import main
                main()
