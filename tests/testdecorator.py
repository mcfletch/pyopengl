"""``gltest``: a GL context around a plain function.

The stand-alone check scripts in this directory are not test cases -- they are
programs ``test_checks.py`` runs in a subprocess and reads the output of -- but
they still need a context.  This gives them one from the same place a test case
gets one: a backend chosen by :func:`glcontext.pick_backend`, driving
:class:`glcontext.ContextTestCase`'s fixture.

    from testdecorator import gltest

    @gltest
    def function():
        '''Runs with a 300x300 context current.'''

    @gltest(size=(640, 480), name='Cool Test')
    def function():
        '''Runs with a specifically configured one.'''

It borrows that fixture by making one throwaway case and calling its ``setUp``
and its cleanups, so the lifecycle -- which backend, which profile, tearing the
context down afterwards -- is the one every other test in the suite gets, and a
backend is wired up in one place.
"""

from functools import wraps

from glcontext import pick_backend
from glcontext_desktop import DesktopGLTestCaseBase


class _DecoratorCase(pick_backend(), DesktopGLTestCaseBase):
    """A case that exists only for its fixture; nothing collects it."""

    #: What to call the window, where the backend opens one.  The backends ask
    #: for this through ``_window_title()``, so it is overridden rather than
    #: assigned over.
    title = 'gltest'

    def _window_title(self):
        return self.title

    def runTest(self):                      # pragma: no cover - never run
        """``unittest.TestCase()`` insists on a method name."""


def gltest(maybe_function=None, *, size=(300, 300), name=None):
    """Run ``function`` with a GL context current, and take it away after.

    Supports both ``@gltest`` and ``@gltest(size=..., name=...)``.  ``name`` is
    the window title, where the backend has a window to title.
    """

    def make_wrapper(function):
        @wraps(function)
        def test_function(*args, **named):
            case = _DecoratorCase()
            case.width, case.height = size
            case.title = name or function.__name__
            case.setUp()
            try:
                return function(*args, **named)
            finally:
                case.doCleanups()

        return test_function

    if callable(maybe_function):
        return make_wrapper(maybe_function)
    return make_wrapper
