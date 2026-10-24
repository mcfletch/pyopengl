"""Conversions between text and 8-bit strings.

An entry point that takes a ``const char *`` needs bytes, and a caller may
pass bytes or text.  Every wrapper uses the conversions in this module, so
they all treat the two the same way.

    STR_IS_BYTES
    STR_IS_UNICODE

        Whether `str` holds bytes or text.  `False` and `True` here.

    _NULL_8_BYTE

        An 8-bit byte with NULL (0) value.

    as_8_bit( x, encoding='utf-8' )
    as_str( x, encoding='utf-8' )
    as_unicode( x, encoding='utf-8' )

        The value as bytes, as `str`, and as text.

    bytes, unicode, long, integer_types, maxsize

        Type names that say what a wrapper expects: `unicode` where text is
        expected instead of `bytes`, and `long` where a value may exceed a
        machine word.
"""
import sys

#: `str` holds text rather than bytes, so a caller handing an entry point a
#: `str` where an 8-bit string is wanted needs it encoded first.
STR_IS_BYTES = False
STR_IS_UNICODE = True

#: Type aliases.  `unicode` and `long` are the same types as `str` and `int`.
#: Modules use the names to say what they expect: text instead of bytes, and
#: a value that may exceed a machine word.
bytes = bytes
unicode = str
long = int
integer_types = (int,)
maxsize = sys.maxsize

_NULL_8_BYTE = b'\000'


def as_8_bit( x, encoding='utf-8' ):
    """Return `x` as an 8-bit string, encoding it only if it is text."""
    if isinstance( x, unicode ):
        return x.encode(encoding)
    elif isinstance( x, bytes ):
        # Note: this can create an 8-bit string that is *not* in encoding,
        # but that is potentially exactly what we wanted, as these can
        # be arbitrary byte-streams being passed to C functions
        return x
    return str(x).encode( encoding )


def as_str( x, encoding='utf-8'):
    """Return `x` as a `str`, decoding it if it is bytes."""
    if isinstance(x,unicode):
        return x
    elif isinstance(x,bytes):
        return x.decode(encoding)
    else:
        return str(x)

def as_unicode(x,encoding='utf-8'):
    """Ensure is a unicode object given default encoding"""
    if isinstance(x,unicode):
        return x
    elif isinstance(x,bytes):
        try:
            return x.decode(encoding)
        except UnicodeDecodeError as err:
            return x.decode('latin-1')
    else:
        return unicode(x)



#: How much of one argument an error message may show.  Enough to recognise
#: what was passed; far short of printing a mesh.
ARGUMENT_REPR_LIMIT = 100


def short_repr(value, limit=ARGUMENT_REPR_LIMIT):
    """Return ``repr(value)``, shortened, for use in an error message.

    The arguments of a GL call are often large (a vertex buffer, a texture, a
    mesh), and an exception that formats one in full produces megabytes of
    digits.  IDLE hangs on such a message, and other terminals scroll the
    useful part of the message out of view.

    The value is shortened when the message is built.  Logging, `repr` and
    the traceback machinery all call `str(error)` before anything decides
    whether to show it, so shortening at print time would not avoid the cost.

    https://github.com/mcfletch/pyopengl/issues/114
    """
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001 a __repr__ may raise anything  # pragma: no cover
        return '<%s, whose repr raised>' % (type(value).__name__,)
    if len(text) <= limit:
        return text
    return '%s... (%s of %d characters)' % (
        text[:limit], type(value).__name__, len(text))


def short_repr_tuple(values, limit=ARGUMENT_REPR_LIMIT):
    """Return a tuple of arguments as ``(a, b, c)``, each one shortened."""
    return '(%s)' % (', '.join(short_repr(one, limit) for one in values),)
