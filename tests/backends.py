"""Which windowing backends the suite knows, and what ``TEST_WINDOWING`` names.

Three modules dispatch on that variable -- :mod:`glcontext` for the
API-agnostic gl/gles/glu suites, :mod:`basetestcase` and :mod:`testdecorator`
for the legacy root-level ones -- and all three read the vocabulary from here.
They each used to carry their own copy, so a backend added to one left the
others raising ``ValueError`` at import: a collection error rather than a test
result, and one that names the module nobody changed.

A **windowed** backend opens a window on a display server.  A **headless** one
needs neither, and there is one per platform: EGL's device platform on Linux,
CGL on macOS.  The legacy root-level tests create their own windowed context
and have no headless equivalent, so under a headless request they skip.
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
