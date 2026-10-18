"""Which platform plugin this run selected, for a case that needs a given one.

``PYOPENGL_PLATFORM`` decides which library every entry point is loaded from,
and a run pins it for the windowing backend it asked for -- ``conftest`` sets
it to ``egl`` for the EGL-device backend and ``osmesa`` for the OSMesa one.
That is a whole-process choice, so a case about a *different* window-system
binding cannot be run in that process at all: under the OSMesa platform there
is no GLX to ask about and no EGL to import, and every entry point in either
resolves to null.

Such a case skips, saying which platform it needed.  It is the same honesty
the suite applies to a driver that cannot serve a feature: a case that cannot
run here says so, rather than failing as though the library were broken.

    from platforms import needs

    @needs('GLX')
    class TestSomethingGLX:
        ...

**Not the same question as "does this machine have the library".**  A machine
with GLX installed still has no GLX in a process that selected OSMesa, because
the plugin decides what is loaded and the plugin was chosen at import.
"""

import os

import pytest


def selected():
    """The ``PYOPENGL_PLATFORM`` value in force, lowercased.

    Empty where none was set, which means the plugin chose itself from the
    machine -- and a machine's own choice serves the window-system bindings it
    has.
    """
    return os.environ.get('PYOPENGL_PLATFORM', '').strip().lower()


#: Two different questions get asked about a platform and a library, and
#: confusing them silently removes coverage.  "Answers None" is a platform
#: saying it has no such library -- the raw modules still import, and every
#: entry point in them reports itself unavailable when called, which is a
#: thing worth testing.  "Raises" is a platform that cannot be asked at all.


#: The window-system binding a Tk widget's context is made through, by
#: ``sys.platform``: the three `OpenGL.Tk` has an implementation for, GLX being
#: the one for the Unix platforms that run an X11 Tk.  This is the usual case
#: and not a certainty: `OpenGL.Tk.context` decides from Tk's own
#: ``windowingsystem`` at run time, which differs for an X11 Tk on macOS.
WINDOW_SYSTEM_LIBRARIES = {
    'darwin': 'CGL',
    'win32': 'WGL',
    'linux': 'GLX',
    'freebsd': 'GLX',
    'openbsd': 'GLX',
    'netbsd': 'GLX',
    'dragonfly': 'GLX',
}


def window_system_library(platform=None):
    """The library a widget's context comes through on ``platform``, or None

    GLX on X11, WGL on Windows, CGL on macOS; this machine's by default.  None
    for a platform `OpenGL.Tk` has no implementation for (Android, iOS,
    WebAssembly): there is no binding to ask whether it is present.  ``sys.platform``
    carries a version on the BSDs (``freebsd14``), which is not part of the name.
    """
    import sys

    name = platform or sys.platform
    if name in WINDOW_SYSTEM_LIBRARIES:
        return WINDOW_SYSTEM_LIBRARIES[name]
    for known, library in WINDOW_SYSTEM_LIBRARIES.items():
        if name.startswith(known) and name[len(known):].replace('.', '').isdigit():
            return library
    return None


def supplies(library):
    """Whether the selected platform has a usable `library` behind it.

    The question for a case that is going to *call* something: a Tk widget
    making its context through GLX, or the GLX querier asking a server.  A
    platform answering None has none, and no amount of the library being
    installed changes that -- the plugin decides what this process loads.
    """
    from OpenGL import platform

    try:
        return getattr(platform.PLATFORM, library, None) is not None
    except Exception:  # noqa: BLE001 each platform plugin loads its libraries on first read, and fails as its loader does
        return False


def bindable(api):
    """Whether `api`'s generated bindings can be built in this process.

    The question for a case sweeping the declaration tables, and it is asked
    of the tables rather than of the platform: a platform answering None for a
    library still builds them -- every entry point reports itself unavailable
    when called, which is exactly what such a sweep checks, and it is how
    ``GLSC2`` everywhere and ``WGL`` on Linux stay covered.

    EGL is the one that cannot: its binding raises ImportError naming the
    library rather than answering None, deliberately, because ``try: from
    OpenGL import EGL`` is how a program asks whether the machine has one.
    Under a platform with no EGL there is nothing there to sweep, so importing
    the API's error checker is the probe -- it is the first thing every
    declaration in that API reaches for.
    """
    import importlib

    try:
        importlib.import_module('OpenGL.raw.%s._errors' % (api,))
    except ImportError:
        return False
    return True


def needs(library):
    """Skip unless the selected platform has a usable `library`.

    A `library` of None is a case that asked for a binding there is none of --
    :func:`window_system_library` on a platform `OpenGL.Tk` does not serve --
    and always skips.
    """
    if library is None:
        return pytest.mark.skip(
            reason='this platform has no window-system binding to test through')
    return pytest.mark.skipif(
        not supplies(library),
        reason='the %s platform supplies no %s, so nothing in this process '
               'can reach it' % (selected() or 'default', library),
    )
