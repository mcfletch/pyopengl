"""Extension module support methods

This module provides the tools required to check whether
an extension is available
"""
from OpenGL.latebind import LateBind
import logging
log = logging.getLogger( 'OpenGL.extensions' )
VERSION_PREFIX = 'GL_VERSION_GL_'
CURRENT_GL_VERSION = None
AVAILABLE_GL_EXTENSIONS = []
AVAILABLE_GLU_EXTENSIONS = []

def getGLVersion( ):
    """Retrieve 2-int declaration of major/minor GL version

    returns [int(major),int(minor)] or False if not loaded
    """
    global CURRENT_GL_VERSION
    if not CURRENT_GL_VERSION:
        from OpenGL.GL import glGetString, GL_VERSION
        new = glGetString( GL_VERSION )
        log.info( 'OpenGL Version: %s', new )
        if new:
            CURRENT_GL_VERSION = [
                int(x) for x in new.split(' ',1)[0].split( '.' )
            ]
        else:
            return False # not yet loaded/supported
    return CURRENT_GL_VERSION


def hasGLExtension( specifier ):
    """Given a string specifier, check for extension being available"""
    global AVAILABLE_GL_EXTENSIONS
    specifier = specifier.replace('.','_')
    if specifier.startswith( VERSION_PREFIX ):
        specifier = [
            int(x)
            for x in specifier[ len(VERSION_PREFIX):].split('_')
        ]
        version = getGLVersion()
        if not version:
            return version
        return specifier <= version
    else:
        from OpenGL.GL import glGetString, GL_EXTENSIONS
        if not AVAILABLE_GL_EXTENSIONS:
            AVAILABLE_GL_EXTENSIONS[:] = glGetString( GL_EXTENSIONS ).split()
        result = specifier in AVAILABLE_GL_EXTENSIONS
        log.info(
            'GL Extension %s %s',
            specifier,
            ['unavailable','available'][bool(result)]
        )
        return result

def hasGLUExtension( specifier ):
    """Given a string specifier, check for extension being available"""
    from OpenGL.GLU import gluGetString, GLU_EXTENSIONS
    if not AVAILABLE_GLU_EXTENSIONS:
        AVAILABLE_GLU_EXTENSIONS[:] = gluGetString( GLU_EXTENSIONS )
    return specifier.replace('.','_') in AVAILABLE_GLU_EXTENSIONS

class _Alternate( LateBind ):
    def __init__( self, name, *alternates ):
        """Initialize set of alternative implementations of the same function"""
        self.__name__ = name
        self._alternatives = alternates
    def __nonzero__( self ):
        from OpenGL import error
        try:
            return bool( self.getFinalCall())
        except error.NullFunctionError, err:
            return False
    def finalise( self ):
        """Call, doing a late lookup and bind to find an implementation"""
        for alternate in self._alternatives:
            if alternate:
                log.info(
                    """Chose alternate: %s from %s""",
                    alternate.__name__,
                    ", ".join([x.__name__ for x in self._alternatives])
                )
                return alternate
        from OpenGL import error
        raise error.NullFunctionError(
            """Attempt to call an undefined alternate function (%s), check for bool(%s) before calling"""%(
                ', '.join([x.__name__ for x in self._alternatives]),
                self.__name__,
            )
        )
def alternate( name, *functions ):
    """Construct a callable that functions as the first implementation found of given set of alternatives

    if name is a function then its name will be used....
    """
    if not isinstance( name, (str,unicode)):
        functions = (name,)+functions
        name = name.__name__
    return type( name, (_Alternate,), {} )( name, *functions )
