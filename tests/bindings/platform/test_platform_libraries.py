"""Every platform answers for every library ``BasePlatform`` documents.

``BasePlatform`` names GL, GLU, GLUT, GLE, GLES1, GLES2 and GLES3 as the
libraries a platform supplies, and the modules under :mod:`OpenGL.raw` read
those attributes while they are being built.  A platform that simply leaves one
out turns ``import OpenGL.GLES2`` into an ``AttributeError`` naming the platform
class, several frames away from anything the caller wrote.

A platform with no such library answers ``None``, which is what the raw modules
treat as "no entry points here": the namespace imports and every function in it
raises :class:`OpenGL.error.NullFunctionError` when called.
"""

import pytest

from childenv import run_in_child
from OpenGL.platform import PLATFORM, baseplatform

#: The library attributes BasePlatform's docstring promises.
LIBRARIES = ('GL', 'GLU', 'GLUT', 'GLE', 'GLES1', 'GLES2', 'GLES3')

#: The namespaces that read a platform library attribute to build themselves.
#: Windows is the case that keeps them honest: it has no OpenGL-ES unless an
#: application has installed ANGLE beside it, and these still import.
#:
#: OpenGL.EGL is not among them because it does not fall back; see below.
ES_NAMESPACES = ('OpenGL.GLES1', 'OpenGL.GLES2', 'OpenGL.GLES3')


@pytest.mark.parametrize('name', LIBRARIES)
def test_baseplatform_defines_every_documented_library(name):
    """The base class answers for a library a subclass does not implement."""
    assert getattr(baseplatform.BasePlatform(), name, 'missing') is None


@pytest.mark.parametrize('name', LIBRARIES)
def test_current_platform_answers_every_documented_library(name):
    """Whichever platform this machine selected, the attribute exists."""
    getattr(PLATFORM, name)


@pytest.mark.parametrize('name', ES_NAMESPACES)
def test_es_namespace_imports(name):
    """The ES namespaces import whether or not this machine has the library."""
    __import__(name)


def test_the_egl_namespace_imports_or_names_the_library():
    """EGL is the one with nowhere to fall back to.

    An ES namespace reaches for the desktop library where the machine has no
    ES one, so it imports anywhere.  EGL ships with the graphics driver and has
    no such second source: where there is none it raises ImportError naming it,
    deliberately, because ``try: from OpenGL import EGL`` is how a program asks
    whether this machine has EGL.  macOS is a platform that answers no.
    """
    try:
        import OpenGL.EGL
    except ImportError as raised:
        assert 'EGL' in str(raised), str(raised)


#: Reach for a platform-specific namespace from a platform that is not it.
#: OSMesa is the one people arrive at: it is how a machine with no display
#: renders, so the caller finding this is by definition unable to see what
#: their session is.
ASKING_THE_WRONG_PLATFORM = '''
import sys
try:
    from OpenGL import osmesa
except Exception as raised:
    sys.stdout.write('%s: %s' % (type(raised).__name__, raised))
else:
    sys.stdout.write('imported')
'''


def test_a_namespace_the_platform_cannot_serve_says_how_to_select_it():
    """``PYOPENGL_PLATFORM`` is the answer, so the failure has to name it.

    Importing ``OpenGL.osmesa`` under any other platform cannot work -- the
    entry points belong to a library that platform does not load.  What the
    caller needs to be told is that the platform is chosen from the
    environment and which value chooses this one; what they get instead is an
    ``AttributeError`` naming an attribute of a class they have never heard
    of, which reads as a defect in PyOpenGL rather than as a setting they have
    not made.

    https://github.com/mcfletch/pyopengl/issues/129
    https://github.com/mcfletch/pyopengl/issues/70
    """
    if getattr(PLATFORM, 'OSMesa', None) is not None:
        pytest.skip('this run has selected the OSMesa platform')
    answered = run_in_child(ASKING_THE_WRONG_PLATFORM).stdout.strip()
    if answered == 'imported':
        pytest.skip('OSMesa is importable here, so there is no refusal to read')
    assert 'PYOPENGL_PLATFORM' in answered, answered
    assert 'osmesa' in answered.lower(), answered


def test_absent_entry_point_raises_pyopengls_own_error():
    """An entry point nothing supplies reports itself, rather than failing in ctypes.

    Where a platform has no OpenGL-ES library the ES namespaces fall back to the
    desktop library, which supplies some of the same entry points and not
    others.  ``glCreateShader`` is one of the others on stock Windows, so the
    call has nothing underneath it -- and that has to arrive as PyOpenGL naming
    the function, not as an AttributeError from the ctypes layer.
    """
    from OpenGL import GLES2
    from OpenGL import error

    if PLATFORM.GLES2 is not None:
        pytest.skip('this platform has an OpenGL-ES library to dispatch to')
    try:
        GLES2.glCreateShader(0)
    except error.NullFunctionError as raised:
        assert 'glCreateShader' in str(raised)
    except error.Error:
        # Resolved through the desktop library, which needs a current context.
        pass
