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


ENTRIES = (
    HandWritten(
        name='glShaderSource',
        apis=('GL', 'GLES2', 'GLES3', 'GLSC2'),
        symbol='pygl_hand_glShaderSource',
        arg_names=('shader', 'string'),
        signature='glShaderSource(shader, string) -> None',
    ),
    HandWritten(
        name='glShaderSourceARB',
        apis=('GL',),
        symbol='pygl_hand_glShaderSource',
        arg_names=('shaderObj', 'string'),
        signature='glShaderSourceARB(shaderObj, string) -> None',
    ),
)


def lookup(api, name):
    """The hand-written implementation for one binding, or None."""
    for entry in ENTRIES:
        if entry.name == name and api in entry.apis:
            return entry
    return None
