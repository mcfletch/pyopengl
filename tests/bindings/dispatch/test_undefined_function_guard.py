"""``bool(someFunction)`` answers whether calling it will work.

That is the guard :class:`OpenGL.error.NullFunctionError` names -- "check for
bool(glutInit) before calling" -- so it is the one piece of the API a caller
reaches for precisely when nothing else about the environment is certain.  It
has two ways to be wrong, and both mislead in the direction of a crash or a
silent skip:

* an entry point the library holds but has not resolved yet reports absent, and
  the caller skips work the driver would have done;
* a Python-coded wrapper reports present whatever became of the entry point
  underneath it, and the caller walks into the call the guard exists to stop.

The second is what a runner with no freeglut on it meets: ``glutInit`` is a
wrapper, so the guard says yes, and the call raises out of a suite that meant
to skip.
"""

import pytest

from OpenGL import platform
from OpenGL.platform import baseplatform


class TestAnUnresolvedEntryPoint:
    """The load is what settles it, so the question has to provoke one."""

    def _pointer(self, extension=None):
        # Through nullFunction rather than the class directly: resolving one
        # writes __call__ onto its own type, and nullFunction gives each entry
        # point a type of its own to be written on.
        return platform.PLATFORM.nullFunction(
            'someFunction',
            dll=None,
            resultType=None,
            argTypes=(),
            argNames=(),
            extension=extension,
        )

    @pytest.fixture
    def resolves(self, monkeypatch):
        """The platform hands back an entry point for anything asked of it."""
        calls = []

        def constructFunction(name, dll, **named):
            calls.append(name)
            return lambda *args: None

        monkeypatch.setattr(platform.PLATFORM, 'constructFunction',
                            constructFunction)
        return calls

    @pytest.fixture
    def absent(self, monkeypatch):
        """The platform has no such entry point -- what a missing library or a
        missing symbol looks like from here."""
        calls = []

        def constructFunction(name, dll, **named):
            calls.append(name)
            raise AttributeError(name)

        monkeypatch.setattr(platform.PLATFORM, 'constructFunction',
                            constructFunction)
        return calls

    def test_one_the_library_has_reports_present(self, resolves):
        """A core entry point, never called.  Nothing has resolved it, so the
        answer can only come from trying."""
        assert bool(self._pointer()) is True
        assert resolves == ['someFunction']

    def test_one_the_library_lacks_reports_absent(self, absent):
        assert bool(self._pointer()) is False

    def test_an_extension_is_asked_the_same_way(self, resolves):
        assert bool(self._pointer(extension='GL_ARB_something')) is True

    def test_asking_twice_resolves_once(self, resolves):
        pointer = self._pointer()
        assert bool(pointer) and bool(pointer)
        assert resolves == ['someFunction']

    def test_an_absent_one_is_asked_again(self, absent):
        """A negative is about the moment it was taken: an entry point that
        needs a context resolves once there is one.  Caching the no would
        strand it."""
        pointer = self._pointer()
        assert not bool(pointer)
        assert not bool(pointer)
        assert absent == ['someFunction', 'someFunction']

    def test_what_it_reports_is_what_calling_it_does(self, absent):
        """The guard and the call have to agree, or the guard is noise."""
        from OpenGL import error

        pointer = self._pointer()
        assert not bool(pointer)
        with pytest.raises(error.NullFunctionError):
            pointer()


class TestADeprecatedEntryPoint:
    """``FORWARD_COMPATIBLE_ONLY`` turns the deprecated entry points into ones
    that refuse the call, whatever the driver exports.  The refusal is the
    point, so the guard has to report it rather than reporting what the library
    would have been able to resolve."""

    def _pointer(self):
        return platform.PLATFORM.nullFunction(
            'glBegin',
            dll=platform.PLATFORM.GL,
            resultType=None,
            argTypes=(),
            argNames=(),
            deprecated=True,
        )

    def test_it_reports_absent(self):
        assert bool(self._pointer()) is False

    def test_and_calling_it_raises(self):
        from OpenGL import error

        with pytest.raises(error.NullFunctionError):
            self._pointer()()


class TestAWrapperFollowsItsEntryPoint:
    """A Python-coded wrapper is a function object, and a function object is
    always true.  The wrapper stands where the entry point would, so it has to
    answer for the entry point."""

    def test_glutinit_follows_the_function_it_calls(self):
        from OpenGL.GLUT import glutInit, special

        assert bool(glutInit) == bool(special._base_glutInit)

    def test_glutdestroywindow_follows_the_function_it_calls(self):
        from OpenGL.GLUT import glutDestroyWindow, special

        assert bool(glutDestroyWindow) == bool(special._base_glutDestroyWindow)

    def test_a_wrapper_over_an_absent_entry_point_is_false(self, monkeypatch):
        """What a runner with no GLUT on it has to see, so that the suite's
        own ``if not glutInit: skip`` reaches the skip."""
        from OpenGL.GLUT import glutInit, special

        def constructFunction(name, dll, **named):
            raise AttributeError(name)

        monkeypatch.setattr(platform.PLATFORM, 'constructFunction',
                            constructFunction)
        monkeypatch.setattr(special._base_glutInit, 'resolved', False,
                            raising=False)
        assert not bool(glutInit)

    def test_the_wrapper_is_still_callable(self):
        """Answering for the entry point does not stop it being the wrapper."""
        from OpenGL.GLUT import glutInit

        assert callable(glutInit)
        assert glutInit.__name__ == 'glutInit'
