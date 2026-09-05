"""A check script with nowhere to draw says so, rather than dying.

``test_checks`` runs the stand-alone scripts in this directory as subprocesses
and reads their stdout.  A script that cannot run is expected to exit with
``checkutils.SKIP_EXIT_CODE``; one that raises instead prints a traceback to
stderr, leaves stdout empty, and reaches the harness as::

    RuntimeError: Test script failure on test_feedbackvarying

which is a failure report for a machine that simply has no display.  The
windowed scripts meet exactly that on a CI runner: no X server, no Wayland
socket, and a backend that cannot open a window.

Two things have to hold for the report to be honest -- the backend has to call
a display it cannot open a skip, and the script has to turn that skip into the
exit code the harness reads.
"""

import unittest

import pytest


class TestTheSkipProtocol:
    """``checkutils`` owns the exit code; this is the wrapper that reaches it
    from a function that raised."""

    def test_a_skip_becomes_the_skip_exit_code(self, capsys):
        import checkutils

        def main():
            raise unittest.SkipTest('no display server')

        with pytest.raises(SystemExit) as caught:
            checkutils.run_check(main)
        assert caught.value.code == checkutils.SKIP_EXIT_CODE

    def test_the_reason_reaches_stdout(self, capsys):
        """The harness quotes stdout in its skip message, so the reason has to
        be on it rather than in the traceback."""
        import checkutils

        def main():
            raise unittest.SkipTest('no display server')

        with pytest.raises(SystemExit):
            checkutils.run_check(main)
        assert 'no display server' in capsys.readouterr().out

    def test_a_script_that_runs_is_left_alone(self):
        import checkutils

        printed = []
        assert checkutils.run_check(lambda: printed.append(1)) is None
        assert printed == [1]

    def test_a_real_failure_still_fails(self):
        """Only a skip is translated.  A broken script has to stay broken, or
        the harness is being told the machine was at fault."""
        import checkutils

        def main():
            raise ValueError('a genuine defect')

        with pytest.raises(ValueError):
            checkutils.run_check(main)


class TestABackendThatCannotStart:
    """glfw fails to initialise where there is no display at all.  That is the
    same condition as a window it cannot open, which this backend already
    skips for, so it reports it the same way."""

    def test_it_skips_rather_than_raising(self, monkeypatch):
        glfw = pytest.importorskip('glfw')
        import glcontext_glfw

        monkeypatch.setattr(glcontext_glfw, '_glfw_ready', False)
        monkeypatch.setattr(glfw, 'init', lambda: False)

        case = unittest.TestCase.__new__(unittest.TestCase)
        skipped = []
        case.skipTest = lambda reason: skipped.append(reason) or (_ for _ in ()).throw(
            unittest.SkipTest(reason)
        )
        with pytest.raises(unittest.SkipTest):
            glcontext_glfw.GLFWBackend._create_context(case)
        assert skipped and 'glfw' in skipped[0].lower()
