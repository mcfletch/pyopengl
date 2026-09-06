"""What ``TEST_WINDOWING`` may name, and who has to agree about it.

Several modules read it, and :mod:`backends` is the list they read.  Two of
them refuse an unknown name by raising at import, so a name one accepts and
another does not is a collection error rather than a test result:

    ValueError: TEST_WINDOWING='cgl' is not recognised

These hold every reader to the one list, because the cost of a disagreement is
a suite that will not run at all.
"""

import backends
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

    def test_nobody_compares_it_against_a_literal(self):
        import os

        here = os.path.dirname(os.path.abspath(__file__))
        offenders = []
        for name in sorted(os.listdir(here)):
            if not name.endswith('.py') or name in ('backends.py',
                                                    'test_backend_names.py'):
                continue
            with open(os.path.join(here, name), encoding='utf-8') as handle:
                source = handle.read()
            if "TEST_WINDOWING', ''" in source or '"TEST_WINDOWING", ""' in source:
                offenders.append(name)
        assert offenders == [], (
            'these read TEST_WINDOWING themselves rather than through '
            'backends.requested(): %s' % (', '.join(offenders),))

    @pytest.mark.parametrize('module', ['glcontext.py', 'conftest.py',
                                        'test_checks.py', 'glget_audit.py'])
    def test_the_readers_go_through_the_shared_module(self, module):
        """By path: ``conftest`` as an importable name is the *root* one, and
        the module meant here is this directory's."""
        import os

        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, module), encoding='utf-8') as handle:
            source = handle.read()
        assert 'backends.' in source, (
            '%s does not read the shared list' % (module,))


class TestWhetherThereIsAWindowServer:
    """The windowed check-scripts open a window, and freeglut answers a
    display it cannot open by writing to stderr and calling ``exit()``.  The
    process is gone before it can say what happened, so the harness sees a
    script that produced no output and reports a failure:

        freeglut (foo): failed to open display ''
        RuntimeError: Test script failure on test_check_crash_on_glutinit

    Having the library installed is a different question from having somewhere
    to put a window, so the gate has to ask both.
    """

    def test_an_x_display_is_a_window_server(self):
        assert backends.has_window_server({'DISPLAY': ':0'}) is True

    def test_so_is_a_wayland_one(self):
        assert backends.has_window_server({'WAYLAND_DISPLAY': 'wayland-0'}) is True

    def test_neither_is_not(self):
        """What a CI runner has: the libraries, and nowhere to draw."""
        assert backends.has_window_server({}) is False

    def test_an_empty_setting_is_no_setting(self):
        """An unexported shell variable expands to the empty string."""
        assert backends.has_window_server({'DISPLAY': ''}) is False

    def test_it_reads_the_environment_by_default(self):
        import os

        assert backends.has_window_server() == backends.has_window_server(os.environ)
