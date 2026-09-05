"""Which windowing backends the suite knows, and what ``TEST_WINDOWING`` names.

Everything that reads that variable reads it here: :mod:`glcontext`, which
chooses the backend; :mod:`conftest`, which sets ``PYOPENGL_PLATFORM`` for the
one backend that needs it; and ``test_checks``, which decides what to hand a
subprocess.  A name one of them accepts and another refuses is not a wrong
answer but a suite that will not collect, since two of them refuse by raising
at import.

A **windowed** backend opens a window on a display server.  A **headless** one
needs neither, and there is one per platform: EGL's device platform on Linux,
CGL on macOS.
"""

#: Backends that open a window, in the order preferred when nothing is asked
#: for.
WINDOWED = ('glfw', 'pygame')

#: Backends that need no window and no display server, one per platform.
HEADLESS = ('egl', 'cgl')

#: Every name ``TEST_WINDOWING`` may take.
ALL = WINDOWED + HEADLESS


def requested(environ=None):
    """The backend ``TEST_WINDOWING`` asks for, or ``None`` for no preference.

    An unset variable and an empty one agree, since that is what an unexported
    shell variable expands to.  A name nobody offers is a ``ValueError`` naming
    the whole list: it is a typo in a run's own configuration, and running on
    some other backend instead would answer a question that was not asked.
    """
    import os

    if environ is None:
        environ = os.environ
    name = environ.get('TEST_WINDOWING', '').strip().lower() or None
    if name is not None and name not in ALL:
        raise ValueError(
            'TEST_WINDOWING=%r is not recognised (expected one of %s)'
            % (name, ', '.join(ALL))
        )
    return name


def is_headless(name):
    """Whether ``name`` renders without a window or a display server."""
    return name in HEADLESS
