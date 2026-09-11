"""Which windowing backends the suite knows, and what ``TEST_WINDOWING`` names.

Everything that reads that variable reads it here: :mod:`glcontext`, which
chooses the backend; :mod:`conftest`, which sets ``PYOPENGL_PLATFORM`` for the
one backend that needs it; and ``test_checks``, which decides what to hand a
subprocess.  A name one of them accepts and another refuses is not a wrong
answer but a suite that will not collect, since two of them refuse by raising
at import.

A **windowed** backend opens a window on a display server.  A **headless** one
needs neither, and there is one per platform: EGL's device platform on Linux,
CGL on macOS, WGL pbuffers on Windows.
"""

#: Backends that open a window, in the order preferred when nothing is asked
#: for.  ``tk`` is last because it is the widget this package ships rather than
#: a third-party toolkit: running the suite on it is how that widget is held to
#: the same behaviour as everything else, which is a thing to ask for by name
#: rather than to fall into.
WINDOWED = ('glfw', 'pygame', 'tk')

#: Backends that need no window and no display server, one per platform.
HEADLESS = ('egl', 'cgl', 'wgl')

#: Which of them serves each platform, by the prefix ``sys.platform`` takes
#: there.  A run that wants "headless, whatever that means here" asks
#: :func:`headless_for` rather than naming one, since a name is only ever
#: right on one platform.
HEADLESS_BY_PLATFORM = (
    ('linux', 'egl'),
    ('darwin', 'cgl'),
    ('win32', 'wgl'),
    ('cygwin', 'wgl'),
)

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


def headless_for(platform=None):
    """The headless backend this platform has, or ``None`` where it has none.

    A test that means "run without a window" has to ask rather than name one:
    ``egl`` is the answer on Linux and nowhere else, and a run that named it on
    Windows would select the Linux platform module, find no GL library, and
    skip every case while reporting green.

    ``platform`` defaults to ``sys.platform``; pass one to ask about another,
    which is what lets the mapping be checked anywhere.
    """
    import sys

    if platform is None:
        platform = sys.platform
    for prefix, name in HEADLESS_BY_PLATFORM:
        if platform.startswith(prefix):
            return name
    return None


def macos_gui_session():
    """Whether this process is in a macOS GUI login session; None if unasked.

    ``CGSessionCopyCurrentDictionary`` is the documented way to tell: it
    answers a dictionary describing the session a window server is running
    for, and NULL outside one -- which is what a job under launchd is, and
    what a CI runner gives.

    None where the question could not be put at all, so a caller can tell
    "there is no window server" from "this Mac would not say".
    """
    import ctypes
    import ctypes.util

    frameworks = {}
    for name, fallback in (
        ('CoreGraphics',
         '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics'),
        ('CoreFoundation',
         '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation'),
    ):
        try:
            frameworks[name] = ctypes.cdll.LoadLibrary(
                ctypes.util.find_library(name) or fallback
            )
        except OSError:
            return None
    try:
        current = frameworks['CoreGraphics'].CGSessionCopyCurrentDictionary
        release = frameworks['CoreFoundation'].CFRelease
    except AttributeError:
        return None
    current.restype = ctypes.c_void_p
    current.argtypes = []
    release.argtypes = [ctypes.c_void_p]
    session = current()
    if session:
        release(ctypes.c_void_p(session))
        return True
    return False


def has_window_server(environ=None, platform=None):
    """Whether there is somewhere to open a window.

    Having a windowing library installed is a different question from having a
    display to use it on, and the windowed check-scripts need both: freeglut
    answers a display it cannot open by writing to stderr and calling
    ``exit()``, which leaves the harness a script that produced no output.

    On Linux the answer is whether X11 or Wayland named a display.

    On macOS there is no such variable -- ``DISPLAY`` there is XQuartz's and
    not the window server the GLUT framework talks to -- so the session is
    asked directly.  It has to be: a Mac running a CI job under launchd has no
    window server, and Apple's GLUT does not answer that by failing the way
    freeglut does.  ``glutInit`` waits for one that will not arrive, which
    stops the run rather than the case.  A Mac that will not say is taken at
    its word, since answering no would skip every windowed case on a working
    desktop.

    Anywhere else the window server is part of the running session and there is
    no equivalent to read, so the answer is yes and what cannot be opened says
    so when it is opened.

    `platform` names the machine being asked about, for a case asking on
    another's behalf; it defaults to this one.
    """
    import os
    import sys

    if environ is None:
        environ = os.environ
    if platform is None:
        platform = sys.platform
    if platform == 'darwin':
        answer = macos_gui_session()
        return True if answer is None else answer
    if not platform.startswith('linux'):
        return True
    return bool(
        environ.get('DISPLAY', '').strip()
        or environ.get('WAYLAND_DISPLAY', '').strip()
    )


def egl_refusal():
    """The ``ImportError`` importing ``OpenGL.raw.EGL`` raises here, or None.

    Where there is no EGL library -- macOS and Windows have none, and a Linux
    machine may lack one -- the raw binding refuses to import at all, so every
    declaration and module under it is out of reach on that machine.  Asked by
    importing it, which is how the platform answers, rather than by reading the
    platform's attributes.
    """
    import importlib

    try:
        importlib.import_module('OpenGL.raw.EGL')
    except ImportError as error:
        return error
    return None


#: Modules that load a native library while being imported, with the libraries
#: whose absence each one reports as an ``ImportError`` naming it.  For these
#: that refusal is the supported answer on a machine without the library, and
#: ``test_optional_module_imports`` holds them to giving it.
OPTIONAL_MODULES = {
    # libgbm is Linux graphics infrastructure: absent on Windows, where ANGLE
    # can still provide EGL.  Where there is no EGL at all -- macOS -- the EGL
    # binding refuses first, and names EGL.
    'OpenGL.EGL.gbmdevice': ('gbm', 'EGL'),
}


def missing_library(name, error):
    """Whether `error`, raised importing module `name`, is that module saying
    a library it needs is not installed here"""
    return any(library in str(error) for library in OPTIONAL_MODULES.get(name, ()))
