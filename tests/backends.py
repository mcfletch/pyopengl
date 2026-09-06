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
#: for.  ``tk`` is last because it is the widget this package ships rather than
#: a third-party toolkit: running the suite on it is how that widget is held to
#: the same behaviour as everything else, which is a thing to ask for by name
#: rather than to fall into.
WINDOWED = ('glfw', 'pygame', 'tk')

#: Backends that need no window and no display server, one per platform.
HEADLESS = ('egl', 'cgl')

#: Every name ``TEST_WINDOWING`` may take.
ALL = WINDOWED + HEADLESS

#: The module whose presence means a backend can be used, where it is not the
#: backend's own name.  ``tk`` is served by the standard library's ``tkinter``,
#: which some distributions package separately from Python itself.
MODULES = {'tk': 'tkinter'}


def module_for(name):
    """The importable module a backend needs, given the backend's name."""
    return MODULES.get(name, name)


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


def has_window_server(environ=None):
    """Whether there is somewhere to open a window.

    Having a windowing library installed is a different question from having a
    display to use it on, and the windowed check-scripts need both: freeglut
    answers a display it cannot open by writing to stderr and calling
    ``exit()``, which leaves the harness a script that produced no output.

    On Linux the answer is whether X11 or Wayland named a display.  Elsewhere
    the window server is part of the running session and there is no equivalent
    variable to read, so the answer is yes and what cannot be opened says so
    when it is opened.
    """
    import os
    import sys

    if environ is None:
        environ = os.environ
    if not sys.platform.startswith('linux'):
        return True
    return bool(
        environ.get('DISPLAY', '').strip()
        or environ.get('WAYLAND_DISPLAY', '').strip()
    )
