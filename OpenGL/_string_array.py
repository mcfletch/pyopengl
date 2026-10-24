"""The argument type for a ``GLchar *const *`` parameter.

Entry points that take several strings, such as ``glShaderSource``,
``glTransformFeedbackVaryings`` and ``glCreateShaderProgramv``, are declared
with an array of pointers to nul-terminated strings.  The bare ctypes type
accepts only a pointer array the caller has already built.  This type also
converts a string, a bytes object, or a sequence of either into the array,
and passes a pointer array through.

This module defines which values count as strings for all such entry
points.  The argument type, the ctypes wrapper's string converter and the C
dispatch layer's callback all use it, so each implementation accepts the
same forms.
"""

import ctypes

__all__ = ['CHAR_POINTER_ARRAY', 'StringArray', 'as_bytes', 'as_bytes_list']

#: The declared type of such a parameter, ``ctypes.POINTER(ctypes.POINTER(
#: ctypes.c_char))``.  ctypes hands out one class per pointed-to type, so this
#: is the same object every API's declaration resolves to.
CHAR_POINTER_ARRAY = ctypes.POINTER(ctypes.POINTER(ctypes.c_char))


def as_bytes(value):
    """Return one string as the bytes the driver reads, or None if it is not a string.

    A ``str`` is encoded as UTF-8, the encoding of GLSL source and GLSL
    names.  A ``bytes`` or ``bytearray`` is used unchanged, since the caller
    chose those bytes.
    """
    if isinstance(value, str):
        return value.encode('utf-8')
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    return None


def as_bytes_list(value):
    """Return the strings as a list of bytes, or None if `value` is not a set of strings."""
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

    #: The pointed-to type.  A ctypes pointer subclass must set this itself,
    #: because the base class's value is not inherited.  Without it no
    #: instance can be made, and a cast to this class makes one.
    _type_ = ctypes.POINTER(ctypes.c_char)

    @classmethod
    def from_param(cls, value):
        """Return the array of pointers ctypes should pass for `value`.

        The array of ``c_char_p`` holds a reference to each bytes object it
        points into, and the cast result holds the array.  ctypes keeps the
        returned object for the duration of the call, so the text stays alive
        until the call returns.
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
