"""What ``TEST_WINDOWING`` may name, and who has to agree about it.

Several modules read it, and :mod:`backends` is the list they read.  Two of
them refuse an unknown name by raising at import, so a name one accepts and
another does not is a collection error rather than a test result:

    ValueError: TEST_WINDOWING='cgl' is not recognised

These hold every reader to the one list, because the cost of a disagreement is
a suite that will not run at all.
"""

import backends
import os

import paths
import pytest


class TestTheVocabulary:
    def test_the_windowed_backends_open_a_window(self):
        assert backends.WINDOWED == ('glfw', 'pygame', 'tk')

    def test_a_backend_named_for_its_module_needs_no_translation(self):
        assert backends.module_for('glfw') == 'glfw'

    def test_tk_is_served_by_tkinter(self):
        """The standard library's name for it, which some distributions
        package separately from Python itself."""
        assert backends.module_for('tk') == 'tkinter'

    def test_the_headless_ones_need_no_display(self):
        """One per platform: EGL's device platform on Linux, CGL on macOS."""
        assert backends.HEADLESS == ('egl', 'cgl')

    def test_every_name_is_one_or_the_other(self):
        assert set(backends.ALL) == set(backends.WINDOWED) | set(backends.HEADLESS)


class TestReadingTheRequest:
    def test_nothing_asked_for_is_no_request(self):
        assert backends.requested({}) is None

    def test_an_empty_setting_is_the_same_as_none(self):
        """What an unexported shell variable expands to."""
        assert backends.requested({'TEST_WINDOWING': ''}) is None

    @pytest.mark.parametrize('name', ['glfw', 'pygame', 'tk', 'egl', 'cgl'])
    def test_each_name_is_accepted(self, name):
        assert backends.requested({'TEST_WINDOWING': name}) == name

    def test_it_is_read_case_and_space_insensitively(self):
        assert backends.requested({'TEST_WINDOWING': '  CGL '}) == 'cgl'

    def test_a_name_nobody_offers_is_refused_with_the_whole_list(self):
        with pytest.raises(ValueError) as raised:
            backends.requested({'TEST_WINDOWING': 'sideways'})
        message = str(raised.value)
        for name in backends.ALL:
            assert name in message, message

    def test_a_headless_name_is_known_to_be_headless(self):
        assert backends.is_headless('cgl')
        assert backends.is_headless('egl')
        assert not backends.is_headless('glfw')


class TestOnlyOneModuleReadsTheVariable:
    """``glcontext.pick_backend`` chooses the backend for everything now, so a
    module that read ``TEST_WINDOWING`` for itself would be a second answer to
    a question with one."""

    #: Scanned rather than listed, and over the whole suite rather than one
    #: directory: a second reader is most likely to appear in a sub-suite that
    #: nobody thought to add here.
    EXEMPT = ('backends.py', 'test_backend_names.py')

    def sources(self):
        """Every ``.py`` under ``tests/``, as ``(relative path, source)``."""
        import os

        for directory, folders, names in os.walk(paths.TESTS):
            folders[:] = [f for f in folders if f != '__pycache__']
            for name in sorted(names):
                if not name.endswith('.py') or name in self.EXEMPT:
                    continue
                full = os.path.join(directory, name)
                with open(full, encoding='utf-8') as handle:
                    yield os.path.relpath(full, paths.TESTS), handle.read()

    def test_nobody_compares_it_against_a_literal(self):
        offenders = [
            name for name, source in self.sources()
            if "TEST_WINDOWING', ''" in source or '"TEST_WINDOWING", ""' in source
        ]
        assert offenders == [], (
            'these read TEST_WINDOWING themselves rather than through '
            'backends.requested(): %s' % (', '.join(offenders),))

    def test_nobody_reads_it_out_of_the_environment_directly(self):
        """Naming it in prose is fine; reaching into os.environ for it is not.

        ``backends.requested()`` is the one place that reads it, so that the
        vocabulary and the default live together.  A module that read it
        itself would be a second answer to a question with one.
        """
        offenders = [
            name for name, source in self.sources()
            if 'TEST_WINDOWING' in source
            and ("environ['TEST_WINDOWING']" in source
                 or 'environ["TEST_WINDOWING"]' in source
                 or "environ.get('TEST_WINDOWING'" in source
                 or 'environ.get("TEST_WINDOWING"' in source)
        ]
        assert offenders == [], (
            'these read TEST_WINDOWING out of the environment rather than '
            'through backends.requested(): %s' % (', '.join(offenders),))

    def test_the_scan_reaches_the_modules_it_is_about(self):
        """A walk that found nothing would pass the two above trivially."""
        found = {name for name, _ in self.sources()}
        for expected in ('glcontext.py', 'conftest.py',
                         os.path.join('checks', 'test_checks.py')):
            assert expected in found, (expected, sorted(found)[:20])


class TestWhetherThereIsAWindowServer:
    """The windowed check-scripts open a window, and freeglut answers a
    display it cannot open by writing to stderr and calling ``exit()``.  The
    process is gone before it can say what happened, so the harness sees a
    script that produced no output and reports a failure:

        freeglut (foo): failed to open display ''
        RuntimeError: Test script failure on test_check_crash_on_glutinit

    Having the library installed is a different question from having somewhere
    to put a window, so the gate has to ask both.

    These are the Linux rule, and they name the platform rather than relying on
    being run on one: the answer is read from the environment only there, and a
    case that asked whichever machine it happened to run on would be asserting
    the Linux rule of a Mac.
    """

    def test_an_x_display_is_a_window_server(self):
        assert backends.has_window_server(
            {'DISPLAY': ':0'}, platform='linux') is True

    def test_so_is_a_wayland_one(self):
        assert backends.has_window_server(
            {'WAYLAND_DISPLAY': 'wayland-0'}, platform='linux') is True

    def test_neither_is_not(self):
        """What a CI runner has: the libraries, and nowhere to draw."""
        assert backends.has_window_server({}, platform='linux') is False

    def test_an_empty_setting_is_no_setting(self):
        """An unexported shell variable expands to the empty string."""
        assert backends.has_window_server(
            {'DISPLAY': ''}, platform='linux') is False

    def test_it_reads_the_environment_by_default(self):
        import os

        assert backends.has_window_server(platform='linux') == (
            backends.has_window_server(os.environ, platform='linux')
        )


class TestAskingMacOS:
    """A Mac has no DISPLAY to read, and the answer is not simply yes.

    A Mac in front of somebody always has a window server; a Mac running a CI
    job under launchd has none -- and Apple's GLUT does not answer that by
    failing.  ``glutInit`` waits for a window server that will not arrive,
    which stops the run rather than the case, and says nothing about which
    script it was waiting in.
    """

    def test_a_gui_session_is_a_window_server(self, monkeypatch):
        monkeypatch.setattr(backends, 'macos_gui_session', lambda: True)
        assert backends.has_window_server({}, platform='darwin') is True

    def test_and_a_launchd_job_without_one_is_not(self, monkeypatch):
        monkeypatch.setattr(backends, 'macos_gui_session', lambda: False)
        assert backends.has_window_server({}, platform='darwin') is False

    def test_a_mac_that_cannot_be_asked_is_taken_at_its_word(self, monkeypatch):
        """Answering no would skip every windowed case on a working desktop;
        the probe failing is not evidence that there is nothing there."""
        monkeypatch.setattr(backends, 'macos_gui_session', lambda: None)
        assert backends.has_window_server({}, platform='darwin') is True

    def test_the_display_variables_are_not_read_there(self):
        """They mean nothing on a Mac: XQuartz sets DISPLAY and is not the
        window server the GLUT framework talks to."""
        import os

        monkey = dict(os.environ, DISPLAY=':0')
        assert backends.has_window_server(
            monkey, platform='darwin'
        ) is backends.has_window_server({}, platform='darwin')


class TestAskingElsewhere:
    def test_windows_has_one(self):
        """There is no variable to read and no equivalent failure to avoid."""
        assert backends.has_window_server({}, platform='win32') is True
