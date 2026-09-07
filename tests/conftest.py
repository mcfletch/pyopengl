"""What has to be decided before any test module is imported.

Which platform the entry points are built for, and whether the implementation
under test is the one the run asked for: both are settled once per process, and
this file is the last place either can be said. It is loaded before any test
module under ``tests/``.

The directories the suites import their helpers from are named by
``pythonpath`` in ``pyproject.toml``, so nothing here edits ``sys.path``.
"""

import os

import pytest

# The headless EGL-device backend loads the GL entry points through EGL, so
# PYOPENGL_PLATFORM must be 'egl' before anything imports OpenGL.  conftest runs
# before any test module, so this is the safe place to set it.  Named rather
# than compared as a string: `backends` is where TEST_WINDOWING is read, and
# this is the one backend that needs the platform set -- the other headless one,
# cgl, is macOS's own and needs nothing.
import backends

if backends.requested() == 'egl':
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

    from OpenGL import dispatch

    if dispatch.settle() != 'c':
        raise pytest.UsageError(
            'PYOPENGL_DISPATCH=c but the C layer is not active: %s.  So this '
            'run would test ctypes while claiming to test C.  Build the '
            'extension with PYOPENGL_REQUIRE_C_DISPATCH=1 to see why, or set '
            'PYOPENGL_DISPATCH_STRICT=0 if the fallback is what you want.'
            % (dispatch.status().reason,)
        )


def pytest_terminal_summary(terminalreporter):
    """Say what ``exercise()`` swallowed, so the number is not invisible."""
    try:
        from glcontext import FORGIVEN
    except Exception:
        return
    if not FORGIVEN:
        return
    cases = {entry[0] for entry in FORGIVEN}
    terminalreporter.write_sep(
        '-', 'exercise() forgave %d GL error(s) across %d case(s)'
        % (len(FORGIVEN), len(cases))
    )
    for entry in FORGIVEN:
        terminalreporter.write_line('  %s %s %r' % entry)
