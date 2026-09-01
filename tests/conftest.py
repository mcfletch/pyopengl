"""Make the shared tests/ helper modules importable from every sub-suite.

The gl / glu / gles suites live in sub-directories and import shared modules
(glcontext, glcontext_desktop, ...) by bare name.  pytest's prepend import mode
adds each test file's own directory to sys.path but not necessarily this one, so
add it here explicitly.  This conftest is loaded before any test under tests/.
"""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# The headless EGL-device backend (TEST_WINDOWING=egl) loads the GL entry points
# through EGL, so PYOPENGL_PLATFORM must be 'egl' before anything imports OpenGL.
# conftest runs before any test module, so this is the safe place to set it.
if os.environ.get('TEST_WINDOWING', '').strip().lower() == 'egl':
    os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')


def pytest_configure(config):
    """Refuse to run a dispatch axis that is not testing what it names.

    ``PYOPENGL_DISPATCH=c`` selects the C layer, but the extension is
    ``optional``: where it was not built the layer falls back to ctypes and
    says nothing.  A whole tox axis then passes while testing the
    implementation it was meant to be the control for -- which is how the
    C-on-Python-3.9 build failure went unnoticed, since ``Py_NewRef`` needs
    3.10 and the axis reported success.

    ``PYOPENGL_DISPATCH_STRICT=0`` turns this off for the case where somebody
    genuinely wants the fallback.
    """
    import os

    if os.environ.get('PYOPENGL_DISPATCH_STRICT', '1').strip().lower() in (
        '0',
        'false',
        'no',
    ):
        return
    if os.environ.get('PYOPENGL_DISPATCH', '').strip().lower() != 'c':
        return

    import OpenGL._dispatch as dispatch

    dispatch.install()
    if not dispatch.ACTIVE:
        raise pytest.UsageError(
            'PYOPENGL_DISPATCH=c but the C layer is not active: the extension '
            'was not built or failed to import, so this run would test ctypes '
            'while claiming to test C.  Build it with '
            'PYOPENGL_REQUIRE_C_DISPATCH=1 to see why, or set '
            'PYOPENGL_DISPATCH_STRICT=0 if the fallback is what you want.'
        )
