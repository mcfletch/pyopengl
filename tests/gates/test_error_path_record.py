"""What ``src/check_error_paths.py`` calls an error path nobody entered.

The gate reads two things and compares them: every ``except`` clause and
``finally`` block in the package, from the syntax trees, and the lines a run
executed, from a coverage data file.  A handler no line of which ran is
unentered, and one that is unentered and not in the record fails the build.

Both halves can be wrong quietly.  A handler the AST pass misses is one the
gate will never ask about, and a record naming handlers the package no longer
has is a claim the next reader has to check the tree to disprove.

The cases build a package of their own and a coverage file to match, rather
than measuring ``OpenGL/``: what is under test is the comparison, and a run of
the real suite would make it answer differently every time.
"""

import sys

import paths
import pytest

sys.path.insert(0, paths.SRC)
try:
    import check_error_paths
finally:
    sys.path.pop(0)


@pytest.fixture
def package(tmp_path):
    """A tree shaped like the package: a directory of modules to read."""
    root = tmp_path / 'package'
    root.mkdir()
    return root


def coverage_for(tmp_path, executed):
    """A coverage data file naming `executed`: ``{path: [line, ...]}``.

    ``coverage`` is a dependency of the ``errorpaths`` environment rather than
    of the suite, so the cases that need one skip in a run without it.  What
    the record says about the package is asked of every run.
    """
    CoverageData = pytest.importorskip(
        'coverage', reason='coverage is installed in the errorpaths environment',
    ).CoverageData

    datafile = str(tmp_path / '.coverage-under-test')
    data = CoverageData(basename=datafile)
    data.add_lines({str(path): lines for path, lines in executed.items()})
    data.write()
    return datafile


class TestWhichHandlersTheGateFinds:
    """Every ``except`` and every ``finally``, named by scope rather than line."""

    def test_a_handler_no_line_of_which_ran_is_unentered(self, tmp_path, package):
        module = package / 'thing.py'
        module.write_text(
            'def call():\n'
            '    try:\n'
            '        work()\n'
            '    except KeyError:\n'
            '        report()\n'
        )
        datafile = coverage_for(tmp_path, {module: [1, 2, 3]})
        found = check_error_paths.unentered(datafile, root=str(package))
        assert [key for key, _description, _why in found] == [
            'thing.py::call::KeyError::0'
        ]

    def test_a_handler_that_ran_is_not_reported(self, tmp_path, package):
        module = package / 'thing.py'
        module.write_text(
            'def call():\n'
            '    try:\n'
            '        work()\n'
            '    except KeyError:\n'
            '        report()\n'
        )
        datafile = coverage_for(tmp_path, {module: [1, 2, 3, 5]})
        assert check_error_paths.unentered(datafile, root=str(package)) == []


class TestAPragmaDoesNotDecideThis:
    """``# pragma: no cover`` on a clause changes nothing the gate reads.

    The pragma is a reporting instruction: it decides what ``coverage report``
    leaves out, while the tracer records those lines like any others.  The gate
    reads the data rather than a report, so a pragma'd handler a case reaches
    is entered -- and one nothing reaches is a handler to write a case for, not
    a measurement that cannot move.
    """

    def test_a_pragmad_handler_a_case_reached_is_entered(self, tmp_path, package):
        module = package / 'thing.py'
        module.write_text(
            'def call():\n'
            '    try:\n'
            '        work()\n'
            '    except KeyError:  # pragma: no cover - only at shutdown\n'
            '        report()\n'
        )
        datafile = coverage_for(tmp_path, {module: [1, 2, 3, 5]})
        assert check_error_paths.unentered(datafile, root=str(package)) == []

    def test_a_pragmad_handler_nothing_reached_is_unentered(self, tmp_path, package):
        module = package / 'thing.py'
        module.write_text(
            'def call():\n'
            '    try:\n'
            '        work()\n'
            '    except KeyError:  # pragma: no cover - only at shutdown\n'
            '        report()\n'
        )
        datafile = coverage_for(tmp_path, {module: [1, 2, 3]})
        [(key, _description, why)] = check_error_paths.unentered(
            datafile, root=str(package))
        assert key == 'thing.py::call::KeyError::0'
        assert why == 'no line of it ran'


class TestTheRecordIsRewrittenWithItsReasons:
    """``--write`` keeps what a line already says about itself."""

    def test_a_reason_already_given_survives(self, tmp_path, package):
        record = tmp_path / 'record.txt'
        record.write_text(
            '# a comment\n'
            'thing.py::call::KeyError::0  # no OSMesa on this machine\n'
        )
        entries = [('thing.py::call::KeyError::0', 'except KeyError', 'no line of it ran')]
        check_error_paths.write(entries, path=str(record))
        assert check_error_paths.recorded(str(record)) == {
            'thing.py::call::KeyError::0': 'no OSMesa on this machine',
        }

    def test_a_new_one_says_nothing_reaches_it(self, tmp_path, package):
        record = tmp_path / 'record.txt'
        entries = [('thing.py::call::KeyError::0', 'except KeyError', 'no line of it ran')]
        check_error_paths.write(entries, path=str(record))
        assert check_error_paths.recorded(str(record)) == {
            'thing.py::call::KeyError::0': 'not reached by any case',
        }


class TestTheRealRecordAgreesWithTheRealPackage:
    """A recorded handler that is no longer in the tree is a line to take out.

    It costs nothing to carry and it is not a failure, but it is a claim about
    a handler that does not exist, and the next reader has to check the file to
    find that out.  This needs no coverage run: both halves are the source.
    """

    def test_every_recorded_handler_is_still_in_the_package(self):
        present = set(check_error_paths.package_handlers())
        stale = sorted(
            key for key in check_error_paths.recorded() if key not in present
        )
        assert stale == [], (
            'these recorded error paths are no longer in OpenGL/: %s.  '
            '`python src/check_error_paths.py --write` takes them out, from a '
            'run of the `errorpaths` environment.' % ', '.join(stale)
        )

