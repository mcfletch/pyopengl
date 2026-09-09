"""Naming the difference between text and 8-bit strings.

An entry point that takes a ``const char *`` wants bytes, and a caller may
hand it either those or text; the conversions live here so that every wrapper
that has to make the distinction makes it the same way.

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

        Type names a wrapper can read for what it means rather than for what
        it is: `unicode` where text is wanted as against `bytes`, and `long`
        where a value may exceed a machine word.
"""
import sys

#: `str` holds text rather than bytes, so a caller handing an entry point a
#: `str` where an 8-bit string is wanted needs it encoded first.
STR_IS_BYTES = False
STR_IS_UNICODE = True

#: The aliases this module exists to provide.  `unicode` and `long` name the
#: same types as `str` and `int`; they are here because the modules that read
#: them say what they mean by the name -- text as against bytes, and a value
#: that may exceed a machine word.
bytes = bytes
unicode = str
long = int
integer_types = (int,)
maxsize = sys.maxsize

_NULL_8_BYTE = b'\000'


def as_8_bit( x, encoding='utf-8' ):
    """`x` as an 8-bit string, encoding it only if it is text."""
    if isinstance( x, unicode ):
        return x.encode(encoding)
    elif isinstance( x, bytes ):
        # Note: this can create an 8-bit string that is *not* in encoding,
        # but that is potentially exactly what we wanted, as these can
        # be arbitrary byte-streams being passed to C functions
        return x
    return str(x).encode( encoding )


def as_str( x, encoding='utf-8'):
    """`x` as a `str`, decoding it if it arrived as bytes."""
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

