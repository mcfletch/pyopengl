#! /usr/bin/env python3
"""The coverage reports run, and count the suite that is actually there.

Nothing ran these -- they are reports a developer invokes by hand -- so they
could rot without anyone finding out, and had: one scanned ``check_es*.py``,
which no longer exists, and its docstring promised an ``ES_COVERAGE.md`` that
never did.

What matters more than the number is that the scan reaches the files.  A
pattern that matched nothing would report full coverage of an empty universe,
which reads as good news.
"""

import os
import subprocess
import sys

import paths
import pytest

import coverage_scan

REPORTS = (
    ('gl', os.path.join('gl', 'gl_coverage.py')),
    ('gles', os.path.join('gles', 'es_coverage.py')),
    ('glu', os.path.join('glu', 'glu_coverage.py')),
)


class TestTheScanFindsWhatIsThere:
    def test_it_reads_the_suite_and_not_a_pattern(self):
        """Every ``.py`` in the directory, so a new file counts by existing."""
        found = coverage_scan.called(os.path.join(paths.TESTS, 'gles'), 'gl')
        # From test_array_int64.py, which the old `test_es*.py` + `test_ext*.py`
        # patterns did not match and so never counted.
        assert 'glGetInteger64v' in found or 'glDeleteQueriesEXT' in found, (
            'the ES scan is missing a module whose name does not start test_es'
        )

    def test_it_ignores_the_report_itself(self):
        """``gl_coverage.py`` names commands in its own prose and tables."""
        directory = os.path.join(paths.TESTS, 'glu')
        assert 'gluNewTess' in coverage_scan.called(directory, 'glu')

    def test_an_empty_directory_finds_nothing_rather_than_everything(self, tmp_path):
        assert coverage_scan.called(str(tmp_path), 'gl') == set()


@pytest.mark.parametrize('api,script', REPORTS, ids=[api for api, _ in REPORTS])
class TestEachReportRuns:
    def run(self, script):
        return subprocess.run(
            [sys.executable, os.path.join(paths.TESTS, script)],
            capture_output=True, text=True, cwd=paths.ROOT, timeout=300,
            env=dict(os.environ, PYTHONPATH=os.pathsep.join([
                paths.TESTS,
                os.path.join(paths.TESTS, 'gl'),
                os.path.join(paths.TESTS, 'gles'),
                os.path.join(paths.TESTS, 'glu'),
            ])),
        )

    def test_it_exits_cleanly(self, api, script):
        completed = self.run(script)
        assert completed.returncode == 0, completed.stderr[-2000:]

    def test_it_reports_a_universe_that_is_not_empty(self, api, script):
        """A report of 100% over nothing is the failure mode worth catching."""
        completed = self.run(script)
        assert completed.stdout.strip(), completed.stderr[-2000:]
        assert '0 total' not in completed.stdout, completed.stdout[-2000:]
