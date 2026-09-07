"""Reading a size-1 GL query as a Python integer.

``SIZE_1_ARRAY_UNPACK`` decides whether a query that produces one value hands
back the value or a one-element array holding it, and it is the caller's to
set.  So the library cannot assume either shape when it reads such a query for
itself -- which it does whenever it sizes a buffer from one, as every info-log
and active-uniform helper here does.

``int()`` alone reads only the first shape, and what it does with the second
is not one thing: it cannot read a ctypes array at all, and for a numpy array
that is not zero-dimensional it raises on some versions of numpy and warns on
others.  So the shape is asked rather than inferred from how the conversion
fails.
"""


def as_int(value):
    """`value` as an ``int``, whether or not size-1 results were unpacked.

    What has a length holds the value; what does not is the value.  A ctypes
    scalar carries its number in ``.value``.
    """
    try:
        len(value)
    except TypeError:
        pass                            # a single value already
    else:
        value = value[0]
    return int(getattr(value, 'value', value))
