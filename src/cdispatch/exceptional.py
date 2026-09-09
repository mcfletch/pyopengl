"""Entry points ``OpenGL.GL`` exports through a wrapper of its own.

``OpenGL/GL/__init__.py`` ends with ``from OpenGL.GL.exceptional import *``, so
for the names below the callable a program reaches is the wrapper written in
``OpenGL/GL/exceptional.py`` rather than the entry point the registry
describes.  Each wrapper exists in order to take a call the C form cannot: the
count comes from the array handed in, or the strides come from its shape.

The registry knows only the C form, so a stub derived from it alone reports an
error against the call the wrapper documents and implements.  Each row here is
the Pythonic form, which the stub emitter offers alongside -- or instead of --
the generated one.

Adding one: write the wrapper in ``OpenGL/GL/exceptional.py``, add it to that
module's ``__all__``, add a row here, and regenerate.
"""

from dataclasses import dataclass

__all__ = ['Exceptional', 'ENTRIES', 'lookup']


@dataclass(frozen=True)
class Exceptional:
    """One wrapper, and the call it takes that the C form does not."""

    #: The entry point it stands in front of.
    name: str
    #: Which API namespaces export the wrapper.  Only ``OpenGL.GL`` imports
    #: ``exceptional``; naming the namespace keeps a second one from
    #: inheriting a stub for a wrapper it does not have.
    apis: tuple
    #: The Pythonic parameter list, as ``name: annotation`` text.  The
    #: annotations are the stub's own array aliases, so the line reads as the
    #: generated one beside it does.
    parameters: tuple
    #: Its docstring's first line.
    signature: str
    #: What it returns, as an annotation.
    returns: str = 'None'
    #: Whether the wrapper also accepts the C form.  ``glDeleteTextures``
    #: passes a ``(size, array)`` pair straight through, so both calls are
    #: real and the stub offers both.  The ``glMap`` family does not: the
    #: wrapper computes the strides and takes the short call alone, so
    #: offering the C form would describe a call that raises ``TypeError``.
    keeps_c_form: bool = True


ENTRIES = (
    Exceptional(
        name='glDeleteTextures',
        apis=('GL',),
        parameters=('textures: UIntArray',),
        signature='glDeleteTextures(textures: GLuint[]) -> None',
    ),
    Exceptional(
        name='glCallLists',
        apis=('GL',),
        parameters=('lists: AnyArray',),
        signature='glCallLists(lists: bytes or GLuint[]) -> None',
    ),
    Exceptional(
        name='glAreTexturesResident',
        apis=('GL',),
        parameters=('textures: UIntArray',),
        signature='glAreTexturesResident(textures: GLuint[]) -> GLboolean[]',
        returns='UByteArrayResult',
    ),
    Exceptional(
        name='glMap1d',
        apis=('GL',),
        parameters=(
            'target: int',
            'u1: float',
            'u2: float',
            'points: DoubleArray',
        ),
        signature='glMap1d(target, u1, u2, points[][]) -> None',
        keeps_c_form=False,
    ),
    Exceptional(
        name='glMap1f',
        apis=('GL',),
        parameters=(
            'target: int',
            'u1: float',
            'u2: float',
            'points: FloatArray',
        ),
        signature='glMap1f(target, u1, u2, points[][]) -> None',
        keeps_c_form=False,
    ),
    Exceptional(
        name='glMap2d',
        apis=('GL',),
        parameters=(
            'target: int',
            'u1: float',
            'u2: float',
            'v1: float',
            'v2: float',
            'points: DoubleArray',
        ),
        signature='glMap2d(target, u1, u2, v1, v2, points[][][]) -> None',
        keeps_c_form=False,
    ),
    Exceptional(
        name='glMap2f',
        apis=('GL',),
        parameters=(
            'target: int',
            'u1: float',
            'u2: float',
            'v1: float',
            'v2: float',
            'points: FloatArray',
        ),
        signature='glMap2f(target, u1, u2, v1, v2, points[][][]) -> None',
        keeps_c_form=False,
    ),
)


def lookup(api, name):
    """The wrapper `api` exports under `name`, or None."""
    for entry in ENTRIES:
        if entry.name == name and api in entry.apis:
            return entry
    return None
