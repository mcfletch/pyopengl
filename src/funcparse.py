"""Helper to parse limited subset of C for wrapper operations"""
import re,logging,keyword
from ctypetopytype import ctype_to_pytype
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
        self.name = name
        self.returnType = self.parseReturnType(returnType)
        try:
            self.argTypes, self.argNames = self.parseArguments( signature )
        except Exception, err:
            log.error( """Error parsing arguments for %s %s: %s""", name, signature, err )
            self.argTypes, self.argNames = (), ()
    findName = re.compile( '[a-zA-z0-9]+$' )
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
        for i,item in enumerate(signature.split( ',' )):
            # TODO: have to hack around the official header having junk here...
            if item.strip() == 'EGLSyncKHR':
                item = 'EGLSyncKHR sync'
            item = item.strip()
            nameMatch = self.findName.search( item )
            if not nameMatch:
                name = 'arg_%i'%i
                rest = item
            else:
                name = nameMatch.group(0)
                rest = item[:nameMatch.start(0)].strip()
                if not rest:
                    rest = name 
                    name = 'arg_%i'%i
            if name in reserved_names:
                name = name + '_'
            types.append( self.cTypeToPyType( rest ) )
            names.append( name )
        return types, names
    cTypeToPyType = staticmethod( ctype_to_pytype )
    
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
def %(name)s(%(argNames)s):pass"""
