#! /usr/bin/env python
"""Extremely dumb replacement for pydoc"""
from directdocs import model,references
from OpenGL.extensions import _Alternate as Alternate
from OpenGL.GLUT.special import GLUTCallback
from OpenGL.wrapper import Wrapper
from OpenGL.constant import Constant
from OpenGL.platform.baseplatform import _NullFunctionPointer as NullFunc
import types,os,textwrap,glob,logging
from genshi.template import TemplateLoader
loader = TemplateLoader(['templates'])
log = logging.getLogger( 'dumbpydoc' )

class PyModule( object ):
    OPENGL_FUNCS = (
        NullFunc,
        Alternate,
        Wrapper,
        GLUTCallback,
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
                        inspector = getattr( self, 'inspect_%s'%(attr,),None)
                        if inspector:
                            value = inspector( value, key )
                        getattr( self, attr ).append( (key,value))
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

    def interesting( self, obj ):
        """Whether this object is interesting for documentation"""
        if isinstance( obj, self.INTERESTING_TYPES):
            return True
        return False
    def inspect_functions( self, func, name ):
        return model.PyFunction( None, func, alias=name )


def render( mod ):
    if not isinstance( mod, PyModule ):
        mod = PyModule( mod )
    mod.inspect()
    tmpl = loader.load('module.html')
    stream = tmpl.generate(module = mod )
    output = stream.render()
    if output:
        open( os.path.join('pydoc',mod.outfile), 'w').write( output )
    for child in mod.modules:
        render( child )


if __name__ == '__main__':
    logging.basicConfig( level=logging.INFO )
    for mod in [
        'OpenGL.raw',
    ]:
        render( mod )
