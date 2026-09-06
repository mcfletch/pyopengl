"""What ``CONTEXT_CHECKING`` does, and which APIs it is a question about.

``OpenGL.CONTEXT_CHECKING`` asks the error checker to look for a current GL
context before it asks the driver for an error, so that a call made without one
says so instead of reading whatever ``glGetError`` answers with no context.

It is a question about *GL*. EGL, GLX and WGL manage the display, the config
and the context itself: their calls are made before any GL context exists, and
by definition. An EGL error checker that waits for a GL context reports no EGL
errors at all in the part of a program where every EGL call happens.

And skipping the check is not skipping the call. ``errcheck`` hands its return
value back as the call's result, so a checker that returns nothing turns every
result into ``None`` -- a wrong answer, arriving wherever the caller reads it:

    eglQueryDevicesEXT(0, None, count) -> None, with count set to 2
"""

import os
import subprocess
import sys

import paths
import pytest

ROOT = paths.ROOT


#: What a child needs to find an interpreter, a library and a renderer, and
#: nothing else: the settings under test are passed explicitly, so an inherited
#: one cannot decide the answer.  The Windows half is what an interpreter needs
#: to start at all -- without SystemRoot the DLL search and the random seed
#: both fail, and the child dies before it can report anything.
_KEEP = ('PATH', 'HOME', 'LD_LIBRARY_PATH', 'DISPLAY', 'WAYLAND_DISPLAY',
         'XDG_RUNTIME_DIR', 'LIBGL_ALWAYS_SOFTWARE', 'GALLIUM_DRIVER',
         'VIRTUAL_ENV', 'PYTHONPATH',
         'SystemRoot', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATHEXT',
         'COMSPEC', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA')

#: EGL is the display API to pin only where the platform chooses between EGL
#: and GLX at run time.  Windows reaches GL through WGL and macOS through CGL,
#: and asking either for the Linux platform module gets a process with no GL
#: library at all -- so every checker is None and the answers below say nothing
#: about context checking.
_PIN_EGL = sys.platform.startswith('linux')


def in_child(body, **environment):
    """Run ``body`` with a fresh interpreter, since the flag is read once."""
    child = {key: os.environ[key] for key in _KEEP if key in os.environ}
    child.update({key: str(value) for key, value in environment.items()})
    if _PIN_EGL:
        child.setdefault('PYOPENGL_PLATFORM', 'egl')
    return subprocess.run([sys.executable, '-c', body], cwd=ROOT, env=child,
                          capture_output=True, text=True, check=False)


class TestTheCheckerKnowsWhichApiItIsFor:
    """The checkers are built when their module is imported, so the flag has to
    be on before that -- hence a child interpreter for each."""

    def _check_context_of(self, api, accelerate=True):
        completed = in_child(
            'import OpenGL\n'
            'OpenGL.CONTEXT_CHECKING = True\n'
            'OpenGL.USE_ACCELERATE = %r\n'
            'from OpenGL.raw.%s import _errors\n'
            'checker = _errors._error_checker\n'
            'print("CHECKS", "none" if checker is None else '
            'int(bool(checker.checkContext)))\n' % (accelerate, api)
        )
        line = [x for x in completed.stdout.splitlines()
                if x.startswith('CHECKS')]
        if not line:
            # A platform without these bindings has nothing to answer, and
            # says so by failing to import them.  Anything else is this case
            # unable to ask its question, which is a broken test rather than
            # an absent platform -- and skipping it hid a stale attribute name
            # here for as long as the name has been wrong.
            if 'ImportError' in completed.stderr:
                pytest.skip('no %s bindings on this platform: %s'
                            % (api, completed.stderr.strip().splitlines()[-1]))
            raise AssertionError(
                'the %s checker could not be asked whether it wants a '
                'context:\n%s' % (api, completed.stderr[-800:])
            )
        return line[0].split()[1]

    #: Both checkers are held to this.  ``checkContext`` is the switch the
    #: compiled one gates on, and PyOpenGL is supported with and without the
    #: compiled one -- so a checker that answers only in one of the two builds
    #: is a difference a program would meet and this file would not.
    IMPLEMENTATIONS = [True, False]

    @pytest.mark.parametrize('accelerate', IMPLEMENTATIONS)
    def test_the_gl_checker_asks_about_a_context(self, accelerate):
        """GL is what the question is about, so it stays on."""
        assert self._check_context_of('GL', accelerate) == '1'

    @pytest.mark.parametrize('accelerate', IMPLEMENTATIONS)
    @pytest.mark.parametrize('api', ['EGL', 'GLX'])
    def test_the_display_apis_do_not(self, api, accelerate):
        """Their calls are what a program makes *to get* a context."""
        answer = self._check_context_of(api, accelerate)
        if answer == 'none':
            pytest.skip('no %s error checker on this platform' % (api,))
        assert answer == '0', (
            '%s errors go unreported wherever no GL context is current, which '
            'is where %s calls are made' % (api, api))


#: Both entry-point implementations are held to this: whichever is selected,
#: a call answers with its own result.
DISPATCH = ['ctypes', 'c']


class TestSkippingTheCheckKeepsTheResult:
    """``errcheck``'s return value *is* the call's result."""

    @pytest.mark.parametrize('dispatch', DISPATCH)
    def test_an_egl_call_answers_with_its_result(self, dispatch):
        completed = in_child(
            'import OpenGL\n'
            'OpenGL.CONTEXT_CHECKING = True\n'
            'from OpenGL.EGL import EGLint\n'
            'from OpenGL.EGL.EXT.device_enumeration import eglQueryDevicesEXT\n'
            'count = EGLint()\n'
            'print("RESULT", eglQueryDevicesEXT(0, None, count), count.value)\n',
            PYOPENGL_DISPATCH=dispatch, PYOPENGL_DISPATCH_STRICT='0',
        )
        line = [x for x in completed.stdout.splitlines() if x.startswith('RESULT')]
        if not line:
            pytest.skip('no EGL device enumeration here: %s'
                        % (completed.stderr[-400:],))
        _marker, result, count = line[0].split()
        assert int(count) >= 1, completed.stdout
        assert result != 'None', (
            'the count came back but the result did not: %s' % (line[0],))

    @pytest.mark.parametrize('dispatch', DISPATCH)
    def test_enumeration_answers_the_same_either_way(self, dispatch):
        """The flag is about *checking*, so it must not change an answer."""
        body = ('from OpenGL.EGL.devices import devices\n'
                'print("COUNT", len(devices()))\n')
        settings = {'PYOPENGL_DISPATCH': dispatch,
                    'PYOPENGL_DISPATCH_STRICT': '0'}
        off = in_child('import OpenGL\nOpenGL.CONTEXT_CHECKING = False\n' + body,
                       **settings)
        on = in_child('import OpenGL\nOpenGL.CONTEXT_CHECKING = True\n' + body,
                      **settings)
        found = [x for x in (off.stdout + on.stdout).splitlines()
                 if x.startswith('COUNT')]
        if len(found) != 2:
            pytest.skip('no EGL enumeration here')
        assert found[0] == found[1], (off.stdout, on.stdout)
