"""Tests for -p PATTERN filtering (issue #90)."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# conftest.py mocks watchdog before this import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from whenchanged.whenchanged import WhenChanged


def make_wc(files=None, patterns=None, recursive=False):
    files = files or ['/tmp']
    with patch('whenchanged.whenchanged.Observer'):
        wc = WhenChanged(
            files=files,
            command=['echo', 'ok'],
            recursive=recursive,
            patterns=patterns or [],
        )
    return wc


class TestMatchesPatterns:
    def test_no_patterns_matches_everything(self):
        wc = make_wc()
        assert wc.matches_patterns('/tmp/main.py')
        assert wc.matches_patterns('/tmp/style.css')
        assert wc.matches_patterns('/tmp/README.md')

    def test_single_pattern_matches(self):
        wc = make_wc(patterns=['*.py'])
        assert wc.matches_patterns('/tmp/main.py')
        assert wc.matches_patterns('/tmp/src/utils.py')

    def test_single_pattern_rejects(self):
        wc = make_wc(patterns=['*.py'])
        assert not wc.matches_patterns('/tmp/style.css')
        assert not wc.matches_patterns('/tmp/README.md')

    def test_multiple_patterns_any_match(self):
        wc = make_wc(patterns=['*.py', '*.yml'])
        assert wc.matches_patterns('/tmp/main.py')
        assert wc.matches_patterns('/tmp/config.yml')
        assert not wc.matches_patterns('/tmp/style.css')

    def test_pattern_matches_basename_only(self):
        """Pattern should match filename, not full path."""
        wc = make_wc(patterns=['*.py'])
        assert wc.matches_patterns('/some/deep/path/script.py')
        assert not wc.matches_patterns('/some/deep/path/script.js')

    def test_pattern_wildcard_prefix(self):
        wc = make_wc(patterns=['test_*'])
        assert wc.matches_patterns('/tmp/test_main.py')
        assert not wc.matches_patterns('/tmp/main.py')

    def test_pattern_exact_filename(self):
        wc = make_wc(patterns=['Makefile'])
        assert wc.matches_patterns('/tmp/Makefile')
        assert not wc.matches_patterns('/tmp/makefile')  # case sensitive

    def test_pattern_question_mark_wildcard(self):
        wc = make_wc(patterns=['file?.py'])
        assert wc.matches_patterns('/tmp/file1.py')
        assert wc.matches_patterns('/tmp/fileA.py')
        assert not wc.matches_patterns('/tmp/file10.py')


class TestIsInterestedWithPatterns:
    def test_pattern_filters_in_watched_dir(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)], patterns=['*.py'])
        assert wc.is_interested(str(tmp_path / 'main.py'))
        assert not wc.is_interested(str(tmp_path / 'style.css'))

    def test_no_pattern_watches_all_in_dir(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)])
        assert wc.is_interested(str(tmp_path / 'main.py'))
        assert wc.is_interested(str(tmp_path / 'style.css'))

    def test_pattern_with_recursive(self, tmp_path):
        subdir = tmp_path / 'src' / 'deep'
        subdir.mkdir(parents=True)
        wc = make_wc(files=[str(tmp_path)], patterns=['*.py'], recursive=True)
        assert wc.is_interested(str(subdir / 'utils.py'))
        assert not wc.is_interested(str(subdir / 'style.css'))

    def test_multiple_patterns_in_dir(self, tmp_path):
        wc = make_wc(files=[str(tmp_path)], patterns=['*.py', '*.yml'])
        assert wc.is_interested(str(tmp_path / 'main.py'))
        assert wc.is_interested(str(tmp_path / 'config.yml'))
        assert not wc.is_interested(str(tmp_path / 'README.md'))

    def test_pattern_does_not_override_exclude(self, tmp_path):
        """Excluded files (vim swap etc.) must still be excluded even with patterns."""
        wc = make_wc(files=[str(tmp_path)], patterns=['*.py', '*.sw*'])
        assert not wc.is_interested(str(tmp_path / '.main.swp'))


class TestCLIPatternParsing:
    def run_main(self, args):
        with patch('sys.argv', ['when-changed'] + args), \
             patch('whenchanged.whenchanged.WhenChanged') as MockWC:
            MockWC.return_value.run = MagicMock()
            try:
                from whenchanged.whenchanged import main
                main()
            except SystemExit:
                pass
            return MockWC

    def test_single_pattern(self):
        MockWC = self.run_main(['-p', '*.py', 'src/', 'make', 'test'])
        args = MockWC.call_args[0]
        assert args[9] == ['*.py']

    def test_multiple_patterns(self):
        MockWC = self.run_main(['-p', '*.py', '-p', '*.yml', 'src/', 'make'])
        args = MockWC.call_args[0]
        assert args[9] == ['*.py', '*.yml']

    def test_no_pattern_defaults_to_empty_list(self):
        MockWC = self.run_main(['src/', 'make', 'test'])
        args = MockWC.call_args[0]
        assert args[9] == []
