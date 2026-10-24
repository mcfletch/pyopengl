"""Reading a size-1 GL query as a Python integer.

``SIZE_1_ARRAY_UNPACK`` decides whether a query that produces one value
returns the value or a one-element array holding it.  The application sets
the flag, so library code that reads such a query cannot assume either shape.
Every info-log and active-uniform helper does this to size a buffer.

``int()`` reads only the first shape.  It cannot read a ctypes array at all.
For a numpy array that is not zero-dimensional, it raises on some numpy
versions and warns on others.  So :func:`as_int` checks the shape instead of
relying on how the conversion fails.
"""


def as_int(value):
    """Return `value` as an ``int``, whether or not size-1 results were unpacked.

    An object with a length holds the value as its first element.  Any other
    object is the value.  A ctypes scalar holds its number in ``.value``.
    """
    try:
        len(value)
    except TypeError:
        pass                            # a single value already
    else:
        value = value[0]
    return int(getattr(value, 'value', value))
