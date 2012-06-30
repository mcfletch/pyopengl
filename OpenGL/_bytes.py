"""8-bit string definitions for Python 2/3 compatibility

Defines the following which allow for dealing with Python 3 breakages:

    STR_IS_BYTES
    STR_IS_UNICODE
    
        Easily checked booleans for type identities
    
    _NULL_8_BYTE
    
        An 8-bit byte with NULL (0) value 
    
    as_8_bit( x, encoding='utf-8')
    
        Returns the value as the 8-bit version
    
    unicode -- always pointing to the unicode type 
    bytes -- always pointing to the 8-bit bytes type
"""
import sys

STR_IS_BYTES = True

if sys.version_info[:2] < (2,6):
    # no bytes, traditional setup...
    bytes = str 
else:
    bytes = bytes
if sys.version_info[:2] < (3,0):
    # traditional setup, with bytes defined...
    unicode = unicode
    _NULL_8_BYTE = '\000'
    def as_8_bit( x, encoding='utf-8' ):
        if isinstance( x, unicode ):
            return x.encode( encoding )
        return bytes( x ) 
else:
    # new setup, str is now unicode...
    STR_IS_BYTES = False
    _NULL_8_BYTE = bytes( '\000','latin1' )
    def as_8_bit( x, encoding='utf-8' ):
        if isinstance( x,unicode ):
            return x.encode(encoding)
        return str(x).encode( encoding )
    unicode = str

STR_IS_UNICODE = not STR_IS_BYTES
