#! /usr/bin/env python
"""Collects sample-code references from file-system"""
import token, tokenize, glob, os
from directdocs.model import Sample

try:
    import logging
    log = logging.getLogger( 'samplemerge' )
    logging.basicConfig()
    log.setLevel( logging.INFO )
except ImportError:
    log = None

def glName( name ):
    """Is this a GL name?
    """
    for prefix in [
        'glut','gle','glu','gl','wgl',
        'GLUT_','GLE_','GLU_','GL_','WGL_',
    ]:
        if name.startswith( prefix ):
            name = name[len(prefix):]
            if name and name[0].isupper():
                return 1
    return 0

def glProcess( filename, tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText ):
    """Process the name in some way"""
    print filename, sourceRow, tokenString, lineText.strip()
    

def generate_tokens_file( filename, filterFunction=glName, processFunction=glProcess ):
    """Generate a set of tokens for the given filename"""
    file = open(filename)
    try:
        generator = tokenize.generate_tokens( file.readline )
        for (tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText) in generator:
    ##      print (tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText)
            if tokenType == token.NAME and filterFunction and filterFunction(tokenString):
                if processFunction:
                    processFunction( filename, tokenType, tokenString, (sourceRow,sourceCol),(endRow,endCol),lineText )
    except Exception, err:
        pass

def generate_tokens_dir( directory, filterFunction=glName, processFunction=glProcess ):
    """Generate tokens for all Python files in a directory"""
    log.info( """Entering directory: %s""", directory )
    files = glob.glob( os.path.join(directory, '*.py'))
    for file in files:
        if os.path.isfile( file ):
            generate_tokens_file( file, filterFunction, processFunction )
    for file in os.listdir( directory ):
        if file in ('.svn','CVS'):
            continue
        file = os.path.join(directory,file)
        if os.path.islink( file ):
            continue
        elif os.path.isdir(file):
            generate_tokens_dir( file, filterFunction, processFunction )
    log.info( """Exiting directory: %s""", directory )

VIEWCVS =  '%(baseURL)s/%(deltaPath)s?rev=HEAD&content-type=text/vnd.viewcvs-markup'
RAWSVN = '%(baseURL)s/%(deltaPath)s'
VIEWSVN = '%(baseURL)s/%(deltaPath)s?view=markup'


class SampleSource( object ):
    """A source from which samples may be generated"""
    nameMapping = {}
    def __init__(
        self, localDir,
        baseURL = '',
        urlTemplate = VIEWCVS,
        projectName='',
        suppressed = None,
    ):
        self.localDir = localDir
        self.projectName = projectName
        self.urlTemplate = urlTemplate
        self.baseURL = baseURL
        self.suppressed = suppressed or {}
    def processEntry( self, filename, tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText ):
        """Record an entry from the scanner"""
        url = self.url( filename, (sourceRow,sourceCol),(endRow,endCol) )
        deltaPath = self.deltaPath( filename )
        if not self.suppressed.has_key( deltaPath ):
            self.nameMapping.setdefault(tokenString, []).append( Sample(
                url=url,
                projectName=self.projectName,
                deltaPath=deltaPath,
                tokenString=tokenString,
                sourceRow=sourceRow,
                sourceCol=sourceCol,
                endRow=endRow,
                endCol=endCol,
                lineText=lineText.strip(),
            ))
    def deltaPath( self, filename ):
        """Calculate path from root:filename"""
        deltaPath = filename[len(os.path.commonprefix( (self.localDir, filename))):]
        deltaPath = deltaPath.replace( '\\','/').lstrip( '/' )
        return deltaPath
    def url( self, filename, (sourceRow,sourceCol),(endRow,endCol) ):
        """Create a URL for the given filename"""
        deltaPath = self.deltaPath( filename )
        baseURL = self.baseURL.rstrip( '/' )
        return self.urlTemplate %locals()
        

def loadData():
    """Samples are downloaded/updated with ./samples.py"""
    SAMPLES = '.samples'
    for s in [
        SampleSource(
            os.path.join(SAMPLES,'OpenGLContext'),
            suppressed = {
                "debug/state.py":1,
                "tests/glget.py":1,
            },
            baseURL = 'http://pyopengl.cvs.sourceforge.net/pyopengl/OpenGLContext',
            projectName = 'OpenGLContext',
        ),
        SampleSource(
            os.path.join(SAMPLES,'PyOpenGL-Demo'),
            baseURL = 'http://pyopengl.cvs.sourceforge.net/pyopengl/Demo/PyOpenGL-Demo',
            projectName='OpenGL-Demo',
        ),

        SampleSource(
            os.path.join(SAMPLES,'Glinter'),
            baseURL = "http://glinter.cvs.sourceforge.net/glinter/Glinter/",
            projectName='Glinter',
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pymmlib' ),
            baseURL = "http://pymmlib.svn.sourceforge.net/viewvc/pymmlib/trunk/pymmlib",
            projectName='{Artistic License} PymmLib',
            urlTemplate = VIEWSVN,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pybzedit' ),
            baseURL = "http://pybzedit.cvs.sourceforge.net/pybzedit/pybzedit/",
            projectName='pyBzEdit',
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pyui' ),
            baseURL = "http://pyui.cvs.sourceforge.net/pyui/PyUIcvs/",
            projectName='{LGPL} PyUI',
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pyui2' ),
            baseURL = "http://pyui2.cvs.sourceforge.net/pyui2/pyui2/",
            projectName='{LGPL} PyUI2',
        ),
        SampleSource(
            os.path.join( SAMPLES, 'visionegg' ),
            baseURL ='http://visionegg.org/trac/browser/trunk/visionegg',
            projectName='{LGPL} VisionEgg',
            urlTemplate = RAWSVN,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'glchess' ),
            baseURL ='http://svn.gnome.org/viewvc/gnome-games/trunk/glchess',
            projectName='{GPL} GLChess',
            urlTemplate = VIEWSVN,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'kamaelia' ),
            baseURL ='http://kamaelia.svn.sourceforge.net/viewvc/kamaelia/trunk/',
            projectName='{LGPL or GPL or MPL} Kamaelia',
            urlTemplate = VIEWSVN,
        ),
        
    ]:
        generate_tokens_dir( s.localDir, processFunction = s.processEntry)
    result = SampleSource.nameMapping
    SampleSource.nameMapping = {}
    return result

CACHE_FILE = '.reference_cache.pkl'

if __name__ == "__main__":
    import pickle
    items = loadData()
    open( CACHE_FILE, 'wb').write(
        pickle.dumps( items )
    )
    items = items.items()
    items.sort()
    for name, itemset in items:
        print name
        for item in itemset:
            print ' ', item.projectName, item.deltaPath, item.lineText
    
