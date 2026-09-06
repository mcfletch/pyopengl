"""The argument type for a ``GLchar *const *`` parameter.

An entry point that takes several strings -- ``glShaderSource``,
``glTransformFeedbackVaryings``, ``glCreateShaderProgramv`` and their
neighbours -- is declared as an array of pointers to nul-terminated strings.
The bare ctypes type for that accepts only a pointer array the caller has
already built, so this one converts as well: a string, a bytes, or a sequence
of either becomes the array, and a pointer array is passed through.

What counts as one of those strings is decided here for every implementation
of every such entry point -- this argument type, the ctypes wrapper's string
converter, and what the C dispatch layer calls back into -- so that which forms
work does not depend on which of them a call goes through.
"""

import ctypes

__all__ = ['CHAR_POINTER_ARRAY', 'StringArray', 'as_bytes', 'as_bytes_list']

#: The declared type of such a parameter, ``ctypes.POINTER(ctypes.POINTER(
#: ctypes.c_char))``.  ctypes hands out one class per pointed-to type, so this
#: is the same object every API's declaration resolves to.
CHAR_POINTER_ARRAY = ctypes.POINTER(ctypes.POINTER(ctypes.c_char))


def as_bytes(value):
    """One string as the bytes the driver reads, or None where it is not one.

    A ``str`` is UTF-8, which is what GLSL source and GLSL names are; a
    ``bytes`` or ``bytearray`` is already the bytes and is taken as it stands,
    since a caller who assembled one meant those bytes rather than whatever
    encoding this would otherwise impose.
    """
    if isinstance(value, str):
        return value.encode('utf-8')
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return None


def as_bytes_list(value):
    """The strings, as bytes, or None where `value` is not a set of strings."""
    one = as_bytes(value)
    if one is not None:
        return [one]
    if not isinstance(value, (list, tuple)):
        return None
    strings = []
    for index, item in enumerate(value):
        text = as_bytes(item)
        if text is None:
            raise TypeError(
                'string %d is %s, not a string' % (index, type(item).__name__)
            )
        strings.append(text)
    return strings


class StringArray(CHAR_POINTER_ARRAY):
    """A ``char **`` argument, from strings or from a prepared array."""

    #: What it points to.  A ctypes pointer subclass states this itself; the
    #: base class's is not inherited, and an instance cannot be made without
    #: it -- which is what a cast to this class asks for.
    _type_ = ctypes.POINTER(ctypes.c_char)

    @classmethod
    def from_param(cls, value):
        """The array of pointers ctypes should pass for `value`.

        The array of ``c_char_p`` holds a reference to each bytes object it
        points into, and the cast result holds the array, so the text stays
        alive for as long as ctypes keeps what this returns -- which is the
        duration of the call.
        """
        strings = as_bytes_list(value)
        if strings is None:
            # A pointer array the caller built for themselves, or None for a
            # null pointer: what the declared type takes, taken as it was.
            # Named rather than reached through super(), because ctypes defines
            # from_param on the metaclass and super() searches the class.
            return CHAR_POINTER_ARRAY.from_param(value)
        if not strings:
            # No strings is a null pointer, as it is in the C layer: an empty
            # array would hand the driver an address to read no items from,
            # which is a distinction without a difference until the count says
            # otherwise.
            return None
        block = (ctypes.c_char_p * len(strings))(*strings)
        return ctypes.cast(block, cls)
