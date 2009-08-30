from ctypes import _CFuncPtr
from OpenGL import wrapper
def isCtypesFunction( target ):
    """Is this a ctypes function pointer?"""
    return isinstance( target, _CFuncPtr )
def isWrapperFunction( target ):
    """Is this an OpenGL wrapper instance?"""
    return isinstance( target, wrapper.Wrapper )

from epydoc import docintrospecter, apidoc, markup
def ctypesIntrospecter(value, value_doc):
    """Add ctypes documentation to the given value's documentation"""
    value_doc.specialize_to(apidoc.RoutineDoc)
    value_doc.is_imported = False
    value_doc.is_public = True
    if hasattr( value, 'argNames' ):
        value_doc.posargs = value.argNames
        value_doc.posarg_defaults = [None] * len(value.argNames)
    if hasattr( value, '__doc__' ):
        value_doc.docstring = docintrospecter.get_docstring(value)
    value_doc.return_type = markup.parse( str(value.restype) )
    
    return value_doc 

def wrapperInstrospecter( value, value_doc ):
    """Add wrapper-specific documentation to the value_doc
    
    Wrappers should have at least this information:
        
        pyConverters 
        cConverters
        cResolvers
        storeValues
        returnValues
        
        wrappedOperation signature
    
    and each of the registered values should be providing
    the information required to determine what they are
    actually doing...
    """
    value_doc.specialize_to(apidoc.RoutineDoc)
    value_doc.is_imported = False
    value_doc.is_public = True
    if hasattr( value,' pyConverterNames' ):
        value_doc.posargs = value.pyConverterNames
    else:
        value_doc.posargs = value.wrappedOperation.argNames
    value_doc.posarg_defaults = [None]*len(value_doc.posargs)
    if hasattr( value, '__doc__' ):
        value_doc.docstring = docintrospecter.get_docstring(value)
    return value_doc

docintrospecter.register_introspecter(
    isCtypesFunction, ctypesIntrospecter,
)
docintrospecter.register_introspecter(
    isWrapperFunction, wrapperInstrospecter,
)

from epydoc.cli import cli
cli()