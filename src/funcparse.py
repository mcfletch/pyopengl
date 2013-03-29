"""Helper to parse limited subset of C for wrapper operations"""
import re,logging,keyword
log = logging.getLogger( __name__ )

reserved_names = set(keyword.kwlist)

class Helper( object ):
    def __getitem__( self, key ):
        item = getattr( self, key, None )
        if item is None:
            raise KeyError( key )
        if callable( item ):
            return item()
        else:
            return item

class Function( Helper ):
    """Parse function parameters from C-style declaration"""
    def __init__( self, returnType, name, signature):
        """Parse definition into our various elements"""
        self.returnType = self.parseReturnType(returnType)
        self.name = name
        try:
            self.argTypes, self.argNames = self.parseArguments( signature )
        except Exception, err:
            log.error( """Error parsing arguments for %s %s: %s""", name, signature, err )
            self.argTypes, self.argNames = (), ()
    findName = re.compile( '[a-zA-z0-9]*$' )
    def parseReturnType( self, returnType ):
        return self.cTypeToPyType( returnType )
    def parseArguments( self, signature ):
        """Parse a C argument-type declaration into a ctypes-style argTypes and argNames"""
        signature = signature.strip()
        if signature.startswith('(') and signature.endswith(')'):
            signature = signature[1:-1]
        # first and easiest case is a void call...
        if not signature.strip() or signature.strip() == 'void':
            return (), ()
        types, names = [], []
        for item in signature.split( ',' ):
            # TODO: have to hack around the official header having junk here...
            if item.strip() == 'EGLSyncKHR':
                item = 'EGLSyncKHR sync'
            item = item.strip()
            nameMatch = self.findName.search( item )
            if not nameMatch:
                raise ValueError( item )
            name = nameMatch.group(0)
            if name in reserved_names:
                name = name + '_'
            rest = item[:nameMatch.start(0)].strip()
            types.append( self.cTypeToPyType( rest ) )
            names.append( name )
        return types, names
    def cTypeToPyType( self, base ):
        """Given a C declared type for an argument/return type, get Python/ctypes version"""
        base = base.strip()
        for strip in ('const','struct'):
            if base.endswith( strip ):
                return self.cTypeToPyType( base[:-len(strip)] )
            elif base.startswith( strip ):
                return self.cTypeToPyType( base[len(strip):] )
        if base.endswith( '*' ):
            new = self.cTypeToPyType( base[:-1] )
            if new == '_cs.GLvoid':
                return 'ctypes.c_void_p'
            elif new == 'ctypes.c_void_p':
                return 'arrays.GLvoidpArray'
            elif new in self.CTYPE_TO_ARRAY_TYPE:
                return 'arrays.%s'%(self.CTYPE_TO_ARRAY_TYPE[new])
            elif new in ( 'arrays.GLcharArray','arrays.GLcharARBArray'):
                # can't have a pointer to these...
                return 'ctypes.POINTER( ctypes.POINTER( _cs.GLchar ))'
            elif new in ( '_cs.GLcharARB',):
                return 'ctypes.POINTER( ctypes.c_char_p )'
            else:
                log.warn( 'Unconverted pointer type in %s: %r', self.name, new )
                return 'ctypes.POINTER(%s)'%(new)
        else:
            return '_cs.%s'%(base,)
    def errorReturn( self ):
        return '0'
    def declaration( self ):
        """Produce a declaration for this function in ctypes format"""
        returnType = self.returnType
        if self.argTypes:
            argTypes = ','.join(self.argTypes)
        else:
            argTypes = ''
        if self.argNames:
            argNames = ','.join(self.argNames)
        else:
            argNames = ''
        arguments = ', '.join([
            '%(type)s(%(name)s)'%locals()
            for (type,name) in [
                (type.split('.',1)[1],name)
                for type,name in zip( self.argTypes,self.argNames )
            ]
        ])
        name = self.name 
        if returnType.strip() in ('_cs.GLvoid', '_cs.void'):
            returnType = pyReturn = 'None'
        else:
            pyReturn = self.returnType
        log.info( 'returnType %s -> %s', self.returnType, pyReturn )
        doc = '%(name)s(%(arguments)s) -> %(pyReturn)s'%locals()
        return self.TEMPLATE%locals()
    TEMPLATE = """@_f
@_p.types(%(returnType)s,%(argTypes)s)
def %(name)s( %(argNames)s ):pass"""
    CTYPE_TO_ARRAY_TYPE = {
        '_cs.GLfloat': 'GLfloatArray',
        '_cs.float': 'GLfloatArray',
        '_cs.GLclampf': 'GLclampfArray',
        '_cs.GLdouble': 'GLdoubleArray',
        '_cs.double': 'GLdoubleArray',
        '_cs.int': 'GLintArray',
        '_cs.GLint': 'GLintArray',
        '_cs.GLuint': 'GLuintArray',
        '_cs.unsigned int':'GLuintArray',
        '_cs.unsigned char': 'GLbyteArray',
        '_cs.uint': 'GLuintArray',
        '_cs.GLshort': 'GLshortArray',
        '_cs.GLushort': 'GLushortArray',
        '_cs.short unsigned int':'GLushortArray',
        '_cs.GLubyte': 'GLubyteArray',
        '_cs.GLbool': 'GLbooleanArray',
        '_cs.GLboolean': 'GLbooleanArray',
        'arrays.GLbooleanArray': 'GLbooleanArray',
        '_cs.GLbyte': 'GLbyteArray',
        '_cs.char': 'GLbyteArray',
        '_cs.gleDouble': 'GLdoubleArray',
        '_cs.GLchar': 'GLcharArray',
        '_cs.GLcharARB': 'GLcharARBArray',
        '_cs.GLhalfNV': 'GLushortArray',
        '_cs.GLhandle': 'GLuintArray',
        '_cs.GLhandleARB': 'GLuintArray',
        '_cs.GLenum': 'GLuintArray',
        # following should all have special sub-classes that enforce dimensions
        '_cs.gleDouble * 4': 'GLdoubleArray',
        '_cs.gleDouble * 3': 'GLdoubleArray',
        '_cs.gleDouble * 2': 'GLdoubleArray',
        '_cs.c_float * 3': 'GLfloatArray',
        '_cs.gleDouble * 3 * 2': 'GLdoubleArray',
        '_cs.GLsizei': 'GLsizeiArray',
        '_cs.GLint64': 'GLint64Array',
        '_cs.GLint64EXT': 'GLint64Array',
        '_cs.GLuint64': 'GLuint64Array',
        '_cs.GLuint64EXT': 'GLuint64Array',
        
        '_cs.EGLint':'GLintArray',
        '_cs.EGLConfig':'GLvoidpArray',
        '_cs.EGLuint64KHR':'GLuint64Array',
        '_cs.EGLNativeDisplayType':'GLvoidpArray',
        '_cs.EGLNativeWindowType': 'GLvoidpArray',
        '_cs.EGLNativePixmapType': 'GLvoidpArray',
        '_cs.EGLTimeKHR': 'GLuint64Array',
    }
