"""The friendly ``glGetUniformIndices``, which ``OpenGL.GL`` and ``OpenGL.GLES3`` share.

``glGetUniformIndices(program, uniformCount, uniformNames, uniformIndices)`` is
one entry point in GL 3.1, ``GL_ARB_uniform_buffer_object`` and OpenGL ES 3.0.
Its friendly form takes the names and answers the indices::

    indices = glGetUniformIndices(program, ['blockColor', 'blockEdge'])
    glGetUniformIndices(program, names, indices)        # into an array you own
    glGetUniformIndices(program, 2, prepared, indices)  # the C ordering

The C ordering is recognised by its second argument being a count rather than
names.  The names are required in either form, and a count larger than the
number of names is refused by the entry point itself, since the driver reads
that many pointers.
"""

from OpenGL._string_array import as_bytes_list
from OpenGL.lazywrapper import lazy

__all__ = ['wrap']


def _get_uniform_indices(
    baseOperation, program, uniformCount=None, uniformNames=None, uniformIndices=None
):
    """Look up the index within program of each of the named uniforms

    program -- the program object to ask
    uniformNames -- the names: a str, a bytes, or a sequence of either
    uniformIndices -- GLuint array of one entry per name to write into; one is
        allocated when it is not given

    Called as glGetUniformIndices( program, uniformNames[, uniformIndices] ),
    or in the C ordering, glGetUniformIndices( program, uniformCount,
    uniformNames[, uniformIndices] ), where uniformNames may also be a
    ``GLchar *const *`` the caller built.

    A name the program does not declare, or one its compiler removed, answers
    GL_INVALID_INDEX.

    returns the GLuint array of indices
    """
    names = as_bytes_list(uniformCount)
    if names is not None:
        # glGetUniformIndices(program, names[, indices]): every argument after
        # the program stands one place earlier than in the C ordering.
        if uniformNames is not None:
            if uniformIndices is not None:
                raise TypeError('glGetUniformIndices: uniformIndices given twice')
            uniformIndices = uniformNames
        uniformCount, uniformNames = len(names), names
    elif uniformCount is None:
        names = as_bytes_list(uniformNames)
        if names is None:
            raise TypeError(
                'glGetUniformIndices needs uniformNames: a str, a bytes, or a '
                'sequence of either'
            )
        uniformCount, uniformNames = len(names), names
    elif uniformNames is None:
        raise TypeError(
            'glGetUniformIndices(program, uniformCount, uniformNames): the names '
            'are required, since the driver reads uniformCount of them'
        )
    if uniformIndices is None:
        from OpenGL import arrays

        uniformIndices = arrays.GLuintArray.zeros((uniformCount,))
    baseOperation(program, uniformCount, uniformNames, uniformIndices)
    return uniformIndices


_get_uniform_indices.__name__ = 'glGetUniformIndices'
_get_uniform_indices.__qualname__ = 'glGetUniformIndices'


def wrap(entry_point):
    """``entry_point``, one API's ``glGetUniformIndices``, behind the friendly form."""
    return lazy(entry_point)(_get_uniform_indices)
