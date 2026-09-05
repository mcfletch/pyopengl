"""What ``TEST_WINDOWING`` may name, and who has to agree about it.

Three modules dispatch on it -- ``glcontext`` for the API-agnostic suites,
``basetestcase`` and ``testdecorator`` for the legacy root-level ones -- and
each used to carry its own list of the names it accepted. Adding ``cgl`` to one
left the other two raising ``ValueError`` at import, which is a collection
error rather than a test result:

    ValueError: TEST_WINDOWING='cgl' is not recognised
    (expected "pygame", "glfw" or "egl")

They read one list now. These hold them to it, because the failure is not a
wrong answer but a suite that will not collect at all.
"""

import backends
import pytest


class TestTheVocabulary:
    def test_the_windowed_backends_open_a_window(self):
        assert backends.WINDOWED == ('glfw', 'pygame')

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

    @pytest.mark.parametrize('name', ['glfw', 'pygame', 'egl', 'cgl'])
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


class TestTheThreeDispatchersAgree:
    """Each of these imports at collection time, so a name one accepts and
    another does not is a suite that will not collect."""

    @pytest.mark.parametrize('module', ['glcontext', 'basetestcase',
                                        'testdecorator'])
    def test_none_of_them_keeps_its_own_list(self, module):
        import importlib
        import inspect

        source = inspect.getsource(importlib.import_module(module))
        assert "'pygame', 'glfw', 'egl'" not in source, (
            '%s carries its own copy of the accepted names' % (module,))
        assert 'backends' in source, (
            '%s does not read the shared list' % (module,))
