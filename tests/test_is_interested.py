"""Tests for WhenChanged.is_interested() - path filtering logic."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# conftest.py mocks watchdog before this import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def make_wc(files, **kwargs):
    """Helper: create a WhenChanged instance without starting the observer."""
    with patch.object(WhenChanged, '__init__', lambda self, *a, **kw: None):
        wc = WhenChanged.__new__(WhenChanged)
    # Reproduce only the attributes needed for is_interested()
    wc.files = files
    paths = {}
    for f in files:
        paths[os.path.realpath(f)] = f
    wc.paths = paths
    wc.recursive = kwargs.get('recursive', False)
    wc.exclude = WhenChanged.exclude
    return wc


# --- Exclusion patterns ---

class TestExcludePatterns:
    def test_vim_swp(self, tmp_path):
        f = str(tmp_path / '.file.swp')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_vim_swo(self, tmp_path):
        f = str(tmp_path / '.file.swo')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_vim_swn(self, tmp_path):
        f = str(tmp_path / '.file.swn')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_vim_4913(self, tmp_path):
        f = str(tmp_path / '4913')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_backup_tilde(self, tmp_path):
        # NOTE: regex r'.~$' has an unescaped dot — matches any char before ~.
        # file.py~ is therefore NOT excluded (bug). Documents current behavior.
        f = str(tmp_path / 'file.py~')
        wc = make_wc([str(tmp_path)])
        assert wc.is_interested(f)  # should be False once regex is fixed


    def test_git_dir(self, tmp_path):
        f = str(tmp_path / '.git' / 'COMMIT_EDITMSG')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_pycache(self, tmp_path):
        f = str(tmp_path / '__pycache__' / 'mod.pyc')
        wc = make_wc([str(tmp_path)])
        assert not wc.is_interested(f)

    def test_normal_py_file_not_excluded(self, tmp_path):
        f = str(tmp_path / 'main.py')
        wc = make_wc([str(tmp_path)])
        # not excluded by pattern — is_interested returns True for watched dir
        assert wc.is_interested(f)


# --- Direct file watching ---

class TestDirectFile:
    def test_watched_file_itself(self, tmp_path):
        f = tmp_path / 'main.py'
        f.touch()
        wc = make_wc([str(f)])
        assert wc.is_interested(os.path.realpath(str(f)))

    def test_unwatched_sibling(self, tmp_path):
        f = tmp_path / 'main.py'
        other = tmp_path / 'other.py'
        f.touch()
        other.touch()
        wc = make_wc([str(f)])
        assert not wc.is_interested(str(other))


# --- Directory watching ---

class TestDirectoryWatching:
    def test_file_in_watched_dir(self, tmp_path):
        wc = make_wc([str(tmp_path)])
        f = str(tmp_path / 'script.py')
        assert wc.is_interested(f)

    def test_file_in_subdir_non_recursive(self, tmp_path):
        subdir = tmp_path / 'sub'
        subdir.mkdir()
        f = str(subdir / 'script.py')
        wc = make_wc([str(tmp_path)], recursive=False)
        assert not wc.is_interested(f)

    def test_file_in_subdir_recursive(self, tmp_path):
        subdir = tmp_path / 'sub' / 'deep'
        subdir.mkdir(parents=True)
        f = str(subdir / 'script.py')
        wc = make_wc([str(tmp_path)], recursive=True)
        assert wc.is_interested(f)

    def test_file_outside_watched_dir(self, tmp_path):
        other = tmp_path / 'other'
        other.mkdir()
        watched = tmp_path / 'watched'
        watched.mkdir()
        wc = make_wc([str(watched)])
        f = str(other / 'script.py')
        assert not wc.is_interested(f)
