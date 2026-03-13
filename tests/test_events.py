"""Tests for event handlers - on_created, on_modified, on_moved, on_deleted."""
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def make_wc(files=None, **kwargs):
    files = files or ['/tmp/test.py']
    with patch('whenchanged.whenchanged.Observer'):
        wc = WhenChanged(
            files=files,
            command=['echo', 'ok'],
            **kwargs
        )
    wc.on_change = MagicMock()
    return wc


def make_event(src_path, is_directory=False, dest_path=None):
    event = MagicMock()
    event.src_path = src_path
    event.is_directory = is_directory
    if dest_path:
        event.dest_path = dest_path
    return event


class TestOnCreated:
    def test_triggers_on_change(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_created(ev)
        wc.on_change.assert_called_once_with('/tmp/test.py')

    def test_sets_event_envvar(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_created(ev)
        assert wc.get_envvar('event') == 'file_created'

    def test_adds_to_recently_created(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_created(ev)
        assert '/tmp/test.py' in wc._recently_created

    def test_ignores_directories(self):
        wc = make_wc()
        ev = make_event('/tmp/mydir', is_directory=True)
        wc.on_created(ev)
        wc.on_change.assert_not_called()


class TestOnModified:
    def test_triggers_on_change(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_modified(ev)
        wc.on_change.assert_called_once_with('/tmp/test.py')

    def test_sets_event_envvar(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_modified(ev)
        assert wc.get_envvar('event') == 'file_modified'

    def test_skips_recently_created(self):
        wc = make_wc()
        wc._recently_created['/tmp/test.py'] = time.time()
        ev = make_event('/tmp/test.py')
        wc.on_modified(ev)
        wc.on_change.assert_not_called()

    def test_removes_from_recently_created_after_skip(self):
        wc = make_wc()
        wc._recently_created['/tmp/test.py'] = time.time()
        ev = make_event('/tmp/test.py')
        wc.on_modified(ev)
        assert '/tmp/test.py' not in wc._recently_created

    def test_purges_stale_recently_created(self):
        wc = make_wc()
        wc._recently_created['/tmp/old.py'] = time.time() - 2.0  # stale
        ev = make_event('/tmp/test.py')
        wc.on_modified(ev)
        assert '/tmp/old.py' not in wc._recently_created

    def test_ignores_directories(self):
        wc = make_wc()
        ev = make_event('/tmp/mydir', is_directory=True)
        wc.on_modified(ev)
        wc.on_change.assert_not_called()


class TestOnMoved:
    def test_triggers_on_change_with_dest_path(self):
        wc = make_wc()
        ev = make_event('/tmp/old.py', dest_path='/tmp/new.py')
        wc.on_moved(ev)
        wc.on_change.assert_called_once_with('/tmp/new.py')

    def test_sets_event_envvar(self):
        wc = make_wc()
        ev = make_event('/tmp/old.py', dest_path='/tmp/new.py')
        wc.on_moved(ev)
        assert wc.get_envvar('event') == 'file_moved'

    def test_ignores_directories(self):
        wc = make_wc()
        ev = make_event('/tmp/mydir', is_directory=True, dest_path='/tmp/newdir')
        wc.on_moved(ev)
        wc.on_change.assert_not_called()


class TestOnDeleted:
    def test_triggers_on_change(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_deleted(ev)
        wc.on_change.assert_called_once_with('/tmp/test.py')

    def test_sets_event_envvar(self):
        wc = make_wc()
        ev = make_event('/tmp/test.py')
        wc.on_deleted(ev)
        assert wc.get_envvar('event') == 'file_deleted'

    def test_ignores_directories(self):
        wc = make_wc()
        ev = make_event('/tmp/mydir', is_directory=True)
        wc.on_deleted(ev)
        wc.on_change.assert_not_called()
