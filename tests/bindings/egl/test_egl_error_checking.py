"""EGL calls are checked for errors, whichever implementation dispatches them.

Error checking is per API, because the APIs do not agree on how to be asked:
GL answers ``glGetError`` and calls zero success, EGL answers ``eglGetError``
and calls ``EGL_SUCCESS`` (0x3000) success, and each raises an exception class
of its own.  ``OpenGL/raw/<api>/_errors.py`` holds one checker per API saying
which is which.

A single ``glGetError`` standing in for all of them is wrong twice over: EGL
errors go unreported, since ``glGetError`` knows nothing of them, and where a
GL context happens to be current a GL error is reported against whichever EGL
call asked next.

These run against whichever implementation is installed, so they say the same
thing to both, and skip where there is no EGL library to ask -- which the
import says, since importing the bindings is how a program asks whether this
machine has EGL at all.
"""

import ctypes

import pytest

EGL = pytest.importorskip('OpenGL.EGL', exc_type=ImportError)

from OpenGL import error


class TestAFailedEglCallRaises:
    """``eglInitialize`` on ``EGL_NO_DISPLAY`` is defined to fail and to set
    ``EGL_BAD_DISPLAY``.  It needs no display, no config and no context, so it
    is the same question on every machine that has an EGL at all."""

    def _initialise_no_display(self):
        major, minor = ctypes.c_long(), ctypes.c_long()
        return EGL.eglInitialize(EGL.EGL_NO_DISPLAY, major, minor)

    def test_it_raises_rather_than_returning_false(self):
        with pytest.raises(error.GLError):
            self._initialise_no_display()

    def test_the_error_is_an_egl_error(self):
        """Not a bare GLError: the EGL codes are a different set, and
        ``EGLError`` is what names them in the message."""
        with pytest.raises(error.EGLError) as raised:
            self._initialise_no_display()
        assert raised.value is not None

    def test_it_carries_the_code_egl_gave(self):
        with pytest.raises(error.GLError) as raised:
            self._initialise_no_display()
        # `err` renders as the EGL name through the raw module's property, so
        # compare on the text rather than on the integer either side of it.
        assert 'EGL_BAD_DISPLAY' in str(raised.value.err)

    def test_it_names_the_call_that_failed(self):
        with pytest.raises(error.GLError) as raised:
            self._initialise_no_display()
        operation = raised.value.baseOperation
        name = getattr(operation, '__name__', operation)
        assert name == 'eglInitialize'


class TestASuccessfulEglCallDoesNot:
    """EGL_SUCCESS is 0x3000, not zero.  A check comparing what eglGetError
    said against zero raises on every successful EGL call, so the code that
    means success has to come from the API rather than from GL's."""

    def test_a_call_that_works_raises_nothing(self):
        # eglGetDisplay asks for the default display and needs nothing set up,
        # so it succeeds wherever there is an EGL at all -- and answering
        # EGL_NO_DISPLAY is a result, not an error.
        EGL.eglGetDisplay(EGL.EGL_DEFAULT_DISPLAY)

    def test_and_neither_does_asking_for_the_error(self):
        assert EGL.eglGetError() == EGL.EGL_SUCCESS

    def test_the_success_code_is_not_gls(self):
        """The two differ, which is the whole reason the code cannot be
        shared: 0 is a perfectly ordinary EGL error code."""
        assert EGL.EGL_SUCCESS == 0x3000


class TestTheCheckerIsTheOneTheApiDeclares:
    """The policy lives in the raw module, so both implementations read the
    same statement of it rather than each carrying its own copy."""

    def test_egl_declares_its_own(self):
        from OpenGL.raw.EGL import _errors

        checker = _errors._error_checker
        assert checker is not None
        assert checker._noErrorResult == 0x3000
        assert issubclass(checker._errorClass, error.EGLError)

    def test_and_it_does_not_wait_for_a_gl_context(self):
        """EGL is how a program gets a context, so its calls happen before
        there is one."""
        from OpenGL.raw.EGL import _errors

        assert not _errors._error_checker.needs_context


class TestEachApiIsAskedItsOwnWay:
    """What the compiled layer was handed, read back.  Under ctypes the same
    facts live on the checker objects; these are the copy the C dispatch uses,
    and the two have to say the same thing."""

    @pytest.fixture(autouse=True)
    def _dispatch(self):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')
        # Importing the API is what registers it.
        import OpenGL.EGL
        import OpenGL.GL

        return dispatch

    def test_gl_calls_zero_success(self, _dispatch):
        source = _dispatch._c.error_source('GL')
        assert source['active'] and source['no_error'] == 0

    def test_egl_calls_egl_success_success(self, _dispatch):
        source = _dispatch._c.error_source('EGL')
        assert source['active'] and source['no_error'] == EGL.EGL_SUCCESS

    def test_gl_errors_are_gls_and_egls_are_not(self, _dispatch):
        """Only GL's are reported by the GL_KHR_debug callback and suspended
        inside a glBegin block, both being GL constructs."""
        assert _dispatch._c.error_source('GL')['gl_family'] is True
        assert _dispatch._c.error_source('EGL')['gl_family'] is False

    @pytest.mark.parametrize('api', ['GLX', 'WGL'])
    def test_an_api_with_nothing_to_poll_is_not_polled(self, _dispatch, api):
        """Neither has a getError.  Polling them with GL's would report a GL
        error against whichever of their calls asked next; under ctypes their
        checker answers its no-error result and never raises."""
        assert _dispatch._c.error_source(api)['active'] is False


class TestTheClassComesFromTheApiThatFailed:
    """``EGLError`` is a subclass of ``GLError``, so raising it for a GL
    failure would still satisfy ``except GLError`` and still read, wrongly, as
    an EGL failure.  Which class goes with which API is recorded rather than
    inferred."""

    def _classes(self):
        import OpenGL.EGL
        import OpenGL.GL
        from OpenGL._dispatch import support

        return support._error_classes

    def test_gl_reports_a_gl_error(self):
        assert self._classes().get('GL') is error.GLError

    def test_egl_reports_an_egl_error(self):
        assert issubclass(self._classes()['EGL'], error.EGLError)

    def test_and_they_are_not_the_same_class(self):
        assert self._classes()['EGL'] is not self._classes()['GL']


#: The first EGL call of a process, made and reported on.  In a child because
#: what is under test is what happens before anything has resolved: the parent
#: has been making EGL calls since it imported the module.
FIRST_CALL = '''
import ctypes
from OpenGL import EGL, error

major, minor = ctypes.c_long(), ctypes.c_long()
try:
    EGL.eglInitialize(EGL.EGL_NO_DISPLAY, major, minor)
except error.GLError as raised:
    print('raised', raised.err)
else:
    print('silent')
'''


class TestTheFirstCallOfAProcessIsCheckedToo:
    """The check runs after the call, and asks the API's ``getError`` for the
    code.  Resolving an entry point makes calls of its own -- among them
    ``eglGetProcAddress``, which sets ``EGL_SUCCESS`` -- so a getter first
    resolved from inside the check clears the error the check was about to
    read, and the call answers ``0`` with nothing raised.

    It is the first failing call of a process that lands there, which is the
    one a program is most likely to have written a diagnostic around.
    """

    def test_it_raises_rather_than_returning_false(self):
        import subprocess
        import sys

        from childenv import run_in_child

        completed = run_in_child(FIRST_CALL)
        assert completed.returncode == 0, completed.stderr[-2000:]
        assert 'EGL_BAD_DISPLAY' in completed.stdout, completed.stdout
