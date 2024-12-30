"""Test cases that run stand-alone check-scripts"""

import os, sys, subprocess, logging
import pytest
from functools import wraps
from OpenGL.GLUT import glutInit

try:
    import numpy
except ImportError:
    numpy = None
HERE = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger(__name__)


def glx_only(func):
    @wraps(func)
    def glx_only_test(*args, **named):
        if not sys.platform in ('linux', 'linux2'):
            pytest.skip("Linux-only")
        return func(*args, **named)

    return glx_only_test


def glut_only(func):
    @wraps(func)
    def glut_only_test(*args, **named):
        if not glutInit:
            pytest.skip("No GLUT installed")
        return func(*args, **named)

    return glut_only_test


def numpy_only(func):
    @wraps(func)
    def glut_only_test(*args, **named):
        if not numpy:
            pytest.skip("No GLUT installed")
        return func(*args, **named)

    return glut_only_test


def check_test(func):
    filename = func.__name__[5:] + '.py'
    file = os.path.join(HERE, filename)

    @wraps(func)
    def test_x():
        log.info("Starting test: %s", filename)
        pipe = subprocess.Popen(
            [
                sys.executable,
                file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = pipe.communicate()
        except subprocess.TimeoutExpired:
            log.warning("TIMEOUT on %s", filename)
            pipe.kill()
            raise
        except subprocess.CalledProcessError as err:
            log.warning("ERROR reported by process: %s", err)
            raise
        output = stdout.decode('utf-8', errors='ignore')
        lines = [x.strip() for x in output.strip().splitlines()]
        if not lines:
            log.error(
                "Test did not produce output: %s",
                stderr.decode('utf-8', errors='ignore'),
            )
            raise RuntimeError('Test script failure')
        if 'SKIP' in lines:
            raise pytest.skip("Skipped by executable")
        elif 'OK' in lines:
            return
        else:
            log.error(
                "Failing check script output: %s",
                stderr.decode('utf-8', errors='ignore'),
            )
            print(output)
            raise RuntimeError("Test Failed")

    return test_x


@glut_only
@check_test
def test_check_crash_on_glutinit():
    """Checks that basic glut init works"""


@numpy_only
@check_test
def test_check_egl_es1():
    """Checks egl with es1 under pygame"""


@numpy_only
@check_test
def test_check_egl_es2():
    """Checks egl with es2 under pygame"""


@numpy_only
@check_test
def test_check_egl_opengl():
    """Checks egl with opengl under pygame"""


@check_test
def test_check_egl_platform_ext():
    """Checks egl display platform directly from render devices"""


@glut_only
@check_test
def test_check_glutwindow():
    """Checks GLUT window manipulation functions"""


@pytest.mark.xfail
@check_test
def test_check_egl_pygame():
    """Checks egl running over a pygame context"""


@glut_only
@check_test
def test_check_freeglut_deinit():
    """Checks free-glut deinitialise"""


@check_test
def test_check_import_err():
    """Checks that the GLU module can be imported"""


@numpy_only
@check_test
def test_check_leak_on_discontiguous_array():
    """Checks that discontiguous array copy doesn't leak the copy"""


@check_test
def test_check_init_framebufferarb():
    """Checks that framebufferarb init function is non-null"""


@check_test
def test_check_gles_imports():
    """Checks that we can import GLES without crashing"""


@glut_only
@check_test
def test_check_glut_debug():
    """Tests GLUT debug function"""


@glut_only
@check_test
def test_check_glut_fc():
    """Tests GLUT forward-compatible-only"""


@glut_only
@check_test
def test_check_glut_load():
    """Tests GLUT forward-compatible-only"""


@glut_only
@check_test
def test_check_glutinit():
    """Tests GLUT init"""


@glut_only
@check_test
def test_check_glutinit_0args():
    """Tests GLUT init with no arguments"""


@glut_only
@check_test
def test_check_glutinit_single():
    """Tests GLUT init with single argument"""


@glut_only
@check_test
def test_check_glutinit_simplest():
    """Tests GLUT init in simplest possible case"""


@check_test
def test_check_silence_numpy_warning():
    """Tests GLUT init in simplest possible case"""


@check_test
def test_egl_ext_enumerate():
    """Tests that EGL can retrieve extension list"""


@check_test
def test_feedbackvarying():
    """Tests that feedback varying buffer operations work"""


@check_test
def test_test_sf2946226():
    """Test sourceforge bug vs. regressions"""


@glut_only
@check_test
def test_test_instanced_draw_detect():
    """Test that instanced draw extension can be identified"""


@glut_only
@check_test
def test_test_gldouble_ctypes():
    """Test use of gldouble array in ctypes"""


@check_test
def test_test_glgetactiveuniform():
    """Test use of gldouble array in ctypes"""


@check_test
def test_test_glgetfloat_leak():
    """Test use of gldouble array in ctypes"""
