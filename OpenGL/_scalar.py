"""Reading a size-1 GL query as a Python integer.

``SIZE_1_ARRAY_UNPACK`` decides whether a query that produces one value hands
back the value or a one-element array holding it, and it is the caller's to
set.  So the library cannot assume either shape when it reads such a query for
itself -- which it does whenever it sizes a buffer from one, as every info-log
and active-uniform helper here does.

``int()`` alone reads only the first shape: numpy refuses to convert an array
that is not zero-dimensional, so ``int(glGetProgramiv(program, ...))`` raises
``TypeError`` the moment a caller turns the flag off.
"""


def as_int(value):
    """`value` as an ``int``, whether or not size-1 results were unpacked."""
    try:
        return int(value)
    except TypeError:
        return int(value[0])
