"""Entry points exported through a wrapper whose call reading cannot recover.

``OpenGL/GL/__init__.py`` ends with ``from OpenGL.GL.exceptional import *``, so
for most of the names below the callable a program reaches is the wrapper
written in ``OpenGL/GL/exceptional.py`` rather than the entry point the
registry describes.  Each wrapper exists in order to take a call the C form
cannot: the count comes from the array handed in, or the strides come from its
shape.

The registry knows only the C form, so a stub derived from it alone reports an
error against the call the wrapper documents and implements.  Each row here is
the Pythonic form, which the stub emitter offers alongside -- or instead of --
the generated one.

Adding one: write the wrapper, add it to its module's ``__all__`` where that
module is ``OpenGL/GL/exceptional.py``, add a row here, and regenerate.

The other wrapper mechanism -- ``OpenGL.lazywrapper.lazy``, used across the
friendly modules -- is read out of the source by
:mod:`cdispatch.lazy_wrappers`, which recovers each one's parameter names and
types them ``Any``.  A ``lazy`` wrapper with a row here is stubbed from the row
instead.  These rows are written by hand because they carry what
reading cannot see: the parameters' types, a return type the wrapper changes,
and whether the C form still works.
"""

from dataclasses import dataclass

__all__ = ['Exceptional', 'ENTRIES', 'GL_EXCEPTIONAL', 'lookup']

#: Where most rows' wrappers are written.  ``OpenGL.GL`` exports them from its
#: namespace; the friendly modules do not bind them.
GL_EXCEPTIONAL = 'OpenGL.GL.exceptional'


@dataclass(frozen=True)
class Exceptional:
    """One wrapper, and the call it takes that the C form does not."""

    #: The entry point it stands in front of.
    name: str
    #: Which API namespaces export the wrapper.  Naming them keeps another
    #: namespace declaring the same entry point from inheriting a stub for a
    #: wrapper it does not have.
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
    #: The module that defines the wrapper, dotted.
    module: str = GL_EXCEPTIONAL
    #: The function in ``module`` that implements it, where that is not
    #: ``name``.
    function: str = ''
    #: Whether ``lazy`` binds the entry point as the function's first
    #: parameter without decorating it.  A function two APIs share is wrapped
    #: once per API's entry point, so its ``def`` carries no decorator to say
    #: so.
    bound: bool = False


ENTRIES = (
    Exceptional(
        name='glGetUniformIndices',
        apis=('GL', 'GLES3'),
        parameters=(
            'program: int',
            'uniformNames: str | bytes | Sequence[str | bytes]',
            'uniformIndices: UIntArray | None = None',
        ),
        signature='glGetUniformIndices(program, uniformNames) -> uniformIndices: GLuint[]',
        returns='UIntArrayResult',
        module='OpenGL._uniform_indices',
        function='_get_uniform_indices',
        bound=True,
    ),
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
