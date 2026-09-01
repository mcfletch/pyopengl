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


#: Entry points that must keep their ctypes binding whatever the generator
#: could describe about them.
#:
#: ``OpenGL/GL/pointers.py`` builds the client-array family, and its typed
#: variants, with a helper that mutates a wrapper *in place* and discards the
#: result -- ``function.setPyConverter(...)`` as a statement, not as part of a
#: chain.  An entry point of ours cannot take part in that: there is no return
#: value for the builder to pick up, so it would keep the object it was given
#: and never see the one it needs, and glVertexPointerd(array) would come out
#: with glVertexPointer's four-argument signature.
#:
#: Making them work means changing how pointers.py builds them, which is a
#: larger change than this is worth and belongs with that module.
EXCLUDED = frozenset(
    [
        'glVertexPointer',
        'glNormalPointer',
        'glColorPointer',
        'glIndexPointer',
        'glTexCoordPointer',
        'glEdgeFlagPointer',
        'glSecondaryColorPointer',
        'glFogCoordPointer',
    ]
)


def lookup(api, name):
    """The hand-written implementation for one binding, or None."""
    for entry in ENTRIES:
        if entry.name == name and api in entry.apis:
            return entry
    return None
