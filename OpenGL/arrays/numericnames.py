"""Module to provide numeric-module name for current version"""
def moduleName( module ):
    """Given a numpy, numeric or numarray module, calculate helper module name"""
    name = module.__name__.lower()
    version = '_'.join( module.__version__.split('.'))
    return 'OpenGL.arrays._%(name)s_%(version)s'%locals()
def loadModule( name ):
    """Load the current C module for our numeric version"""
    return __import__( name, {}, {}, name.split( '.' ))