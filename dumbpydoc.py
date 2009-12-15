#! /usr/bin/env python
"""Extremely dumb replacement for pydoc"""
from directdocs import model,references
from OpenGL.extensions import _Alternate as Alternate
from OpenGL.GLUT.special import GLUTCallback
from OpenGL.wrapper import Wrapper
from OpenGL.constant import Constant
from OpenGL.lazywrapper import _LazyWrapper as Lazy
from ctypes import _CFuncPtr as CFunctionType
from OpenGL.error import glCheckError
from OpenGL.platform.baseplatform import _NullFunctionPointer as NullFunc
from OpenGL import platform

CythonMethod = type( glCheckError )

import types,os,textwrap,glob,logging,pickle,inspect
from genshi.template import TemplateLoader
loader = TemplateLoader(['templates'])
log = logging.getLogger( 'dumbpydoc' )

FUNCTION_MAPPING = pickle.load( open( '.pyfunc-urls.pkl' ))

class PyModule( object ):
    OPENGL_FUNCS = (
        NullFunc,
        Alternate,
        Wrapper,
        GLUTCallback,
        Lazy,
        CFunctionType,
        CythonMethod,
        #platform.PLATFORM.DEFAULT_FUNCTION_TYPE,
    )
    INTERESTING_TYPES = OPENGL_FUNCS + (
        Constant,
        types.FunctionType,
        type,
        types.ModuleType,
    )
    FUNCTIONAL_TYPES = OPENGL_FUNCS + (types.FunctionType,)
    CLASS_TYPES = (type,)
    CONSTANT_TYPES = (Constant,)
    MODULE_TYPES = (types.ModuleType,)
    FT_MAP = [
        ('functions',FUNCTIONAL_TYPES),
        ('constants',CONSTANT_TYPES),
        ('imports',MODULE_TYPES),
        ('classes',CLASS_TYPES),
    ]
    def __init__( self, name ):
        self.name = name
        self.basename = name.split( '.' )[-1]
        self.functions = []
        self.constants = []
        self.classes = []
        self.imports = []
        self.modules = []
    @property
    def target( self ):
        return self.mod
    @property
    def is_package( self ):
        base = os.path.splitext(os.path.basename( self.mod.__file__ ))[0]
        if base == "__init__":
            return True
        return False
    _mod = None
    @property
    def mod( self ):
        if not self._mod:
            self._mod = __import__(
                self.name, {}, {},
                self.name.split('.'),
            )
        return self._mod
    @property
    def docstring( self ):
        if self.mod.__doc__:
            return textwrap.dedent( self.mod.__doc__ )
        else:
            return None
    @property
    def parents( self ):
        """Yield parents in closest-to-farthest order"""
        names = self.name.split('.')
        for i in range(1,len(names)):
            yield PyModule( ".".join( names[:i] ))
        yield self

    @property
    def title( self ):
        return 'Module: %s'%( self.name, )
    @property
    def outfile( self ):
        return '%s.html'%( self.name, )

    _inspected = False
    def inspect( self ):
        """Inspect the module"""
        if self._inspected:
            return
        self._inspected = True
        for key,value in sorted( self.mod.__dict__.items()):
            if self.interesting( value ):
                for attr,types in self.FT_MAP:
                    if isinstance( value, types ):
                        collection = getattr( self, attr )
                        is_duplicate = False
                        for (k,v) in collection:
                            if getattr(v,'target',v) is value:
                                if not hasattr( v, 'aliases' ):
                                    v.aliases = []
                                v.aliases.append( key )
                                is_duplicate = True
                        if not is_duplicate:
                            inspector = getattr( self, 'inspect_%s'%(attr,),None)
                            if inspector:
                                value = inspector( value, key )
                            collection.append( (key,value))
            else:
                if not isinstance( value, (str,unicode,int,long,dict)):
                    print 'not interesting', key, type(value)
        if self.is_package:
            dirname = os.path.dirname( self.mod.__file__ )
            for name in sorted(os.listdir( dirname )):
                other = os.path.join( dirname, name )
                if os.path.isdir( other ) and os.path.exists( os.path.join( other, '__init__.py' )):
                    mod = self.sub_module(name)
                    if mod:
                        self.modules.append( mod )
            for name in sorted(glob.glob(os.path.join( dirname, '*.py' ))):
                basename = os.path.splitext( os.path.basename( name ))[0]
                if basename != '__init__':
                    mod = self.sub_module(basename)
                    if mod:
                        self.modules.append( mod )
    def sub_module( self, name ):
        mod = PyModule( ".".join( [self.name,name] ))
        try:
            mod.inspect()
        except Exception, err:
            log.warn( 'Unable to import %s: %s'%( mod.name, err ))
            return None
        else:
            return mod

    def doc_as_link( self, obj ):
        """Should we document this thing as a link?"""

    def interesting( self, obj ):
        """Whether this object is interesting for documentation"""
        if isinstance( obj, self.INTERESTING_TYPES):
            module = getattr(obj, '__module__',None)
            if module is not None:
                if not module == self.name:
                    # only document where defined for functions...
                    log.warn( 'Filtering %s by module exclusion: %s', obj, module )
                    return False
                    # Need to figure out how to restrict...
            return True
        return False
    def inspect_functions( self, func, name ):
        return model.PyFunction( None, func, alias=name )
    def inspect_classes( self, cls, name ):
        """Inspect the classes given"""
        return Class( cls, self )
    def link( self, func, name=None ):
        """Should we do a link to the manual page instead of local description?"""
        return FUNCTION_MAPPING.get( name or func.name )

class Class( object ):
    """Metadata describing a class to be documented"""
    def __init__( self, cls, module=None ):
        self.cls = cls
        self.basename = cls.__name__
        self.module = module or self.find_module( cls )
        self.name = '%s.%s'%( self.module.name, cls.__name__ )
        self.functions = []
        self.properties = []
        self.inspect()
    @property
    def target( self ):
        return self.cls
    @classmethod
    def find_module( cls, target ):
        if target.__module__:
            return PyModule( target.__module__ )
        raise RuntimeError('blah')
    @property
    def bases( self ):
        return [Class( x ) for x in self.cls.__bases__]

    @property
    def docstring( self ):
        if self.cls.__doc__:
            try:
                return textwrap.dedent( self.cls.__doc__ or '' )
            except TypeError, err:
                return None
        else:
            return None

    def inspect( self ):
        """Introspect to find methods, properties, etceteras"""
        for key,value in sorted(self.cls.__dict__.items()):
            if isinstance( value, (
                types.FunctionType,
                types.MethodType,
                types.UnboundMethodType,
                types.BuiltinFunctionType,
                types.BuiltinMethodType,
                classmethod,
                staticmethod,
            )):
                self.functions.append( (key,model.PyFunction( None, value, alias=key )))
            elif hasattr( value, '__get__' ):
                self.properties.append( (key,Property(value,key,self)))

class Property( object ):
    def __init__( self, target, name, cls ):
        self.cls = cls
        self.target = target
        self.name = name
    @property
    def docstring( self ):
        if self.target.__doc__:
            try:
                return textwrap.dedent( self.target.__doc__ or '' )
            except TypeError, err:
                return None
        else:
            return None



def render( mod ):
    if not isinstance( mod, PyModule ):
        mod = PyModule( mod )
    mod.inspect()
    if mod.modules:
        mod.next = mod.modules[0]
        mod.modules[0].previous = mod
        mod.modules[-1].next = mod
    for child,next in zip(mod.modules,mod.modules[1:]):
        child.next = next
    for child,previous in zip(mod.modules[1:],mod.modules[:-1]):
        child.previous = previous
    tmpl = loader.load('module.html')
    stream = tmpl.generate(
        module = mod,
        FUNCTION_MAPPING=FUNCTION_MAPPING,
    )
    output = stream.render()
    if output:
        open( os.path.join('pydoc',mod.outfile), 'w').write( output )
    for child in mod.modules:
        render( child )


if __name__ == '__main__':
    logging.basicConfig( level=logging.DEBUG )
    for mod in [
        'OpenGL.GL.ARB',
#        'OpenGLContext',
#        'vrml',
    ]:
        render( mod )
