"""Tests for debounce (-d) and on_change dispatch logic."""
import os
import sys
import time
import threading
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def make_wc(files=None, debounce_delay=0, **kwargs):
    files = files or ['/tmp']
    with patch('whenchanged.whenchanged.Observer'):
        wc = WhenChanged(
            files=files,
            command=['echo', 'ok'],
            debounce_delay=debounce_delay,
            **kwargs
        )
    return wc


class TestOnChange:
    def test_no_debounce_calls_run_command_immediately(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)])
        wc.run_command = MagicMock()
        wc.on_change(str(tmp_path / 'test.py'))
        wc.run_command.assert_called_once()

    def test_uninterested_path_not_called(self, tmp_path):
        watched = tmp_path / 'watched'
        watched.mkdir()
        other = tmp_path / 'other'
        other.mkdir()
        wc = make_wc(files=[str(watched)])
        wc.run_command = MagicMock()
        wc.on_change(str(other / 'test.py'))
        wc.run_command.assert_not_called()


class TestDebounce:
    def test_single_event_runs_after_delay(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)], debounce_delay=0.1)
        wc.run_command = MagicMock()
        wc.on_change(str(tmp_path / 'test.py'))
        wc.run_command.assert_not_called()  # pas encore
        time.sleep(0.2)
        wc.run_command.assert_called_once()

    def test_rapid_events_coalesced_into_one(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)], debounce_delay=0.1)
        wc.run_command = MagicMock()
        # 5 events rapides
        for _ in range(5):
            wc.on_change(str(tmp_path / 'test.py'))
            time.sleep(0.02)
        time.sleep(0.2)
        # doit avoir été appelé une seule fois
        assert wc.run_command.call_count == 1

    def test_timer_reset_on_new_event(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)], debounce_delay=0.15)
        wc.run_command = MagicMock()
        wc.on_change(str(tmp_path / 'test.py'))
        time.sleep(0.05)
        wc.on_change(str(tmp_path / 'test.py'))  # reset le timer
        time.sleep(0.1)
        wc.run_command.assert_not_called()  # timer pas encore écoulé
        time.sleep(0.1)
        wc.run_command.assert_called_once()
