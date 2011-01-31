"""Refactored version of the opengl generator using ctypeslib
"""
try:
    from ctypeslib.codegen import codegenerator
    from ctypeslib import xml2py
except ImportError, err:
    try:
        from ctypes_codegen import codegenerator, xml2py
    except ImportError, err:
        from ctypes.wrap import codegenerator, xml2py
try:
    from cStringIO import StringIO
except ImportError, err:
    from StringIO import StringIO

import sys, logging
log = logging.getLogger( 'openglgenerator' )
import ctypes
from OpenGL.platform import GL, GLU, GLUT, GLE
from OpenGL import constant

def indent( code, indentation='\t' ):
    """Indent given code by given indentation"""
    lines = code.splitlines()
    return "\n".join( [ '%s%s'%(indentation,line) for line in lines] )

class OpenGLGenerator( codegenerator.Generator ):
    """Subclass of code generator providing PyOpenGL integration"""
    _super = codegenerator.Generator
    MODULE_HEADER = """from ctypes import *
from OpenGL import platform, arrays
from OpenGL.constant import Constant
from OpenGL import constants as GLconstants
GLvoid = GLconstants.GLvoid
"""
    def defaultEmitters( cls ):
        """Produce the set of default emitter classes
        """
        return [
            OpenGLFunction(),
            OpenGLConstant(),
        ] + cls._super.defaultEmitters()
    def importAble( cls, name, value ):
        """Determine whether this name/object should be imported from known symbols"""
        return (
            isinstance( value, type ) or 
            isinstance( value, constant.Constant ) or 
            value.__class__.__name__.endswith( 'CFunctionType') # this should be available *somewhere*!
        )
    importAble = classmethod( importAble )

    def filter_items( self, items, expressions=None,symbols=None, types=None ):
        """Filter out PFN functions"""
        items = [
            i for i in items 
            # skip the pointer-to-function meta-types...
            if not getattr( i,'name','').startswith( 'PFN' )
        ]
        return self._super.filter_items( self, items, expressions=expressions, symbols=symbols, types=types )
    def get_sharedlib(self, dllname, cc):
        """Override so that all references to shared libraries go through "platform" module"""
        if dllname in ('libGL','GL','libGL.so.1'):
            return 'platform.GL'
        elif dllname in ('libGLU','GLU','libGLU.so.1'):
            return 'platform.GLU'
        elif dllname in ('libglut','glut','libglut.so.3'):
            return 'platform.GLUT'
        elif dllname in ('libgle','gle','libgle.so.3' ):
            return 'platform.GLE'
        else:
            raise NotImplementedError( """Haven't done %s yet!"""%(dllname) )
    def cmpitems( self, a, b ):
        """Dumb sorting helper to order by name instead of position"""
        try:
            return cmp( (a.name,getattr(a, "location", -1), a.__class__), (b.name,getattr(b, "location", 1),b.__class__))
        except (AttributeError,TypeError,ValueError), err:
            return cmp( a, b )

        

class OpenGLFunction( codegenerator.Function ):
    """Replaces the ctypes default code generator for functions"""
    TEMPLATE = """%(location)s%(name)s = platform.createBaseFunction( 
    %(name)r, dll=%(libname)s, resultType=%(returnType)s, 
    argTypes=[%(argTypes)s],
    doc=%(documentation)r, 
    argNames=%(argNames)r,
)
"""
    def emit(self, generator, func):
        """Produce a function via a call to platform-provided function"""
        result = []
        libname = self.libName( generator, func )
        if libname:
            self.increment()
            result.append( self.generateHeader( generator, func ))
            args = self.getArgs( generator, func )
            argTypes  = ",".join( args )
            argNames = self.getArgNames( generator, func )
            location = self.locationComment( generator, func )
            name = func.name
            returnType = generator.type_name(func.returns)

            documentation = self.documentFunction( generator, func )

            generator.names.add(func.name)
            result.append( self.TEMPLATE %locals() )
            return result
        elif not func.name.startswith( '__builtin_' ):
            log.warn( """Could not find DLL name for function: %r""", func.name )
            return ''

    def arrayTypeName( self, generator, argType ):
        """Retrieve the array type name for argType or None"""
        if generator.type_name(argType).startswith( 'POINTER' ):
            # side effect should be to make the type available,
            # but doesn't work with GLvoid
            typeName = generator.type_name(argType.typ)
            if typeName in self.CTYPE_TO_ARRAY_TYPE:
                return 'arrays.%s'%(self.CTYPE_TO_ARRAY_TYPE[typeName])
            elif (typeName == 'GLvoid'):
                # normal to not have pointers to it...
                log.info( 'GLvoid pointer %r, using POINTER(%s)', typeName, typeName )
            else:
                log.warn( 'No mapping for %r, using POINTER(%s)', typeName, typeName )
        return None
    def getArgs( self, generator, func ):
        """Retrieve arg type-names for all arguments in function typedef"""
        return [
            self.arrayTypeName( generator, a ) or generator.type_name(a) 
            for a in func.iterArgTypes()
        ]
    def documentFunction( self, generator, func ):
        """Customisation point for documenting a given function"""
        args = self.getArgs(generator,func)
        argnames = self.getArgNames( generator, func )
        return str("%s( %s ) -> %s"%(
            func.name,
            ", ".join(
                [ '%s(%s)'%( name, typ) for (name,typ) in zip(args,argnames) ]
            ),
            generator.type_name(func.returns),
        ))
    SUFFIX_TO_ARRAY_DATATYPE = [
        ('ub','GLconstants.GL_UNSIGNED_BYTE'),
        ('us','GLconstants.GL_UNSIGNED_SHORT'),
        ('ui','GLconstants.GL_UNSIGNED_INT'),
        ('f','GLconstants.GL_FLOAT'),
        ('d','GLconstants.GL_DOUBLE'),
        ('i','GLconstants.GL_INT'),
        ('s','GLconstants.GL_SHORT'),
        ('b','GLconstants.GL_BYTE'),
    ]
    CTYPE_TO_ARRAY_TYPE = {
        'GLfloat': 'GLfloatArray',
        'float': 'GLfloatArray',
        'GLclampf': 'GLclampfArray',
        'GLdouble': 'GLdoubleArray',
        'double': 'GLdoubleArray',
        'int': 'GLintArray',
        'GLint': 'GLintArray',
        'GLuint': 'GLuintArray',
        'unsigned int':'GLuintArray',
        'unsigned char': 'GLbyteArray',
        'uint': 'GLuintArray',
        'GLshort': 'GLshortArray',
        'GLushort': 'GLushortArray',
        'short unsigned int':'GLushortArray',
        'GLubyte': 'GLubyteArray',
        'GLbyte': 'GLbyteArray',
        'char': 'GLbyteArray',
        'gleDouble': 'GLdoubleArray',
        # following should all have special sub-classes that enforce dimensions
        'gleDouble * 4': 'GLdoubleArray',
        'gleDouble * 3': 'GLdoubleArray',
        'gleDouble * 2': 'GLdoubleArray',
        'c_float * 3': 'GLfloatArray',
        'gleDouble * 3 * 2': 'GLdoubleArray',
    }

class OpenGLConstant( codegenerator.Variable ):
    """Override to produce OpenGL.constant.Constant instances"""
    TEMPLATE = """%(name)s = Constant( %(name)r, %(value)r)"""
    def emit( self, generator, typedef ):
        """Filter out constants that don't have all-uppercase names"""
        if typedef.name.upper() != typedef.name:
            return ""
        return super( OpenGLConstant, self ).emit( generator, typedef )

class OpenGLDecorator( OpenGLFunction ):
    """Produces decorated versions of the functions in a separate module
    
    This is passed in as an emitter for a separate pass, so that only the
    annotations get into the separate module.
    """
    def isPointer( self, generator, arg ):
        """Is given arg-type a pointer?"""
        return generator.type_name( arg ).startswith( 'POINTER' )
    def hasPointer( self, generator, args ):
        """Given set of arg-types, is one a pointer?"""
        return [ arg for arg in args if self.isPointer( generator, arg ) ]
    def emit( self, generator, func ):
        """Emit code to create a copy of the function with pointer-size annotations"""
        name = func.name 
        size = None 
        typ = None
        if not self.hasPointer( generator, func.iterArgTypes() ):
            return None
        libname = self.libName( generator, func )
        if not libname:
            return None
        base = name 
        if name.endswith( 'ARB' ):
            base = base[:-3]
        if base.endswith( 'v' ):
            base = base[:-1]
            found = 0
            for suffix,typ in self.SUFFIX_TO_ARRAY_DATATYPE:
                if base.endswith(suffix):
                    found = 1
                    base = base[:-len(suffix)]
                    try:
                        size = int(base[-1])
                    except ValueError, err:
                        size = None
                    break
        elif base[:-1].endswith( 'Matrix' ):
            # glLoadMatrix, glMultMatrix
            for suffix,typ in self.SUFFIX_TO_ARRAY_DATATYPE:
                if name.endswith( suffix ):
                    size = 16
                    break
        result = ''
        for index,(arg,argName) in enumerate( zip(func.iterArgTypes(),func.iterArgNames()) ):
            type = self.arrayTypeName( generator, arg )
            argName = str(argName )
            if type:
                generator.names.add(func.name)
            if result:
                previous = indent( result, '\t' )
            else:
                previous = '\traw.%(name)s'%locals()
            if type and size is None:
                # should only print this if it's a normal array type...
                result = """arrays.setInputArraySizeType(
%(previous)s,
    None, # XXX Could not determine size of argument %(argName)s for %(name)s %(type)s
    %(type)s, 
    %(argName)r,
)
"""%locals()
            elif type:
                result = """arrays.setInputArraySizeType(
%(previous)s,
    %(size)s,
    %(type)s,
    %(argName)r,
)
"""%locals()
        if result:
            return '%(name)s = %(result)s'%locals()
        return None
    

if __name__ == "__main__":
    import sys, logging
    logging.basicConfig()
    codegenerator.Generator = OpenGLGenerator
    sys.exit(xml2py.main())
