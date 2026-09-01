"""Entry points implemented by hand rather than generated.

A few entry points promise their callers a computation rather than a
description of their arguments, so no table can express them.  Each gets a C
function in ``src/c/pygl_handwritten.c``, and is named here so the generator
emits its metadata and table entry pointing at that function.  A hand-written
entry point is reached exactly as a generated one is.

Adding one: write ``pygl_hand_<name>`` in ``pygl_handwritten.c``, add a row
here, and regenerate.
"""

from dataclasses import dataclass

__all__ = ['HandWritten', 'ENTRIES', 'lookup']


@dataclass(frozen=True)
class HandWritten:
    """One hand-written entry point."""

    #: The command it implements.
    name: str
    #: Which API namespaces it serves.  The same C function can implement the
    #: entry point for several, since the behaviour does not differ between
    #: them -- only the library the slot resolves against does.
    apis: tuple
    #: The C function, in pygl_handwritten.c.
    symbol: str
    #: The argument names the friendly form takes, which are not the C entry
    #: point's: glShaderSource computes count and length from what it is given.
    #: They go into the docstring and the text signature.  ``argNames`` keeps
    #: reporting the C entry point's names, which is what it reports today and
    #: what the compatibility contract preserves.
    arg_names: tuple
    #: Its docstring's first line.
    signature: str
    #: What ``argNames`` reports.  The C entry point's names, which is what it
    #: reports today; a friendly module that rebuilds the binding may spell
    #: them differently from the raw declaration, and that spelling is the one
    #: callers see.
    c_arg_names: tuple = ()


ENTRIES = (
    HandWritten(
        name='glShaderSource',
        apis=('GL', 'GLES2', 'GLES3', 'GLSC2'),
        symbol='pygl_hand_glShaderSource',
        arg_names=('shader', 'string'),
        signature='glShaderSource(shader, string) -> None',
        c_arg_names=('shaderObj', 'count', 'string', 'length'),
    ),
    HandWritten(
        name='glShaderSourceARB',
        apis=('GL',),
        symbol='pygl_hand_glShaderSource',
        arg_names=('shaderObj', 'string'),
        signature='glShaderSourceARB(shaderObj, string) -> None',
        c_arg_names=('shaderObj', 'count', 'string', 'length'),
    ),
)


#: Entry points that keep their ctypes binding whatever the generator could
#: describe about them.
#:
#: Empty.  It held the bases that ``OpenGL/GL/pointers.py`` and
#: ``OpenGL/GL/images.py`` derive typed variants from -- glVertexPointerd from
#: glVertexPointer, glDrawPixelsub from glDrawPixels -- because those builders
#: applied their customisations *in place* and discarded the result, which an
#: entry point of ours cannot take part in.  Both builders now rebind instead,
#: which is what a wrapper's setters have always returned something for, so
#: the bases are described and generated like anything else and the variants
#: still come out with their own signatures.
EXCLUDED = frozenset()


def lookup(api, name):
    """The hand-written implementation for one binding, or None."""
    for entry in ENTRIES:
        if entry.name == name and api in entry.apis:
            return entry
    return None
