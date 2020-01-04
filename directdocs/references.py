#! /usr/bin/env python3
"""Collects sample-code references from file-system"""
from __future__ import absolute_import
from __future__ import print_function
import token, tokenize, glob, os
from directdocs.model import Sample

try:
    import logging
    log = logging.getLogger( 'samplemerge' )
    logging.basicConfig()
    log.setLevel( logging.INFO )
except ImportError:
    log = None

special_names = set([
    'compileShader',
    'compileProgram',
    'VBO',
])

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
    if name in special_names:
        return True
    return 0

def glProcess( filename, tokenType, tokenString, sourceStart, sourceEnd, lineText ):
    """Process the name in some way"""
    (sourceRow,sourceCol) = sourceStart
    (endRow,endCol) = sourceEnd
    print(filename, sourceRow, tokenString, lineText.strip())
    

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
    except Exception as err:
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
LOGGERHEAD = '%(baseURL)s/view/head:/%(deltaPath)s'
GOOGLECODE = '%(baseURL)s/source/browse/trunk/%(deltaPath)s'
GOOGLECODE_HG = '%(baseURL)s/source/browse/%(deltaPath)s'
GITHUB = '%(baseURL)s/blob/master/%(deltaPath)s#L%(sourceRow)s'
BITBUCKET = '%(baseURL)s/src/tip/%(deltaPath)s#lines-%(sourceRow)s'

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
    def processEntry( self, filename, tokenType,tokenString, xxx_todo_changeme, xxx_todo_changeme1,lineText ):
        """Record an entry from the scanner"""
        (sourceRow,sourceCol) = xxx_todo_changeme
        (endRow,endCol) = xxx_todo_changeme1
        url = self.url( filename, (sourceRow,sourceCol),(endRow,endCol) )
        deltaPath = self.deltaPath( filename )
        if deltaPath not in self.suppressed:
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
    def url( self, filename, xxx_todo_changeme2, xxx_todo_changeme3 ):
        """Create a URL for the given filename"""
        (sourceRow,sourceCol) = xxx_todo_changeme2
        (endRow,endCol) = xxx_todo_changeme3
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
            baseURL = 'http://github.com/mcfletch/openglcontext',
                       
            projectName = 'OpenGLContext',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join(SAMPLES,'PyOpenGL-Demo'),
            baseURL = 'http://github.com/mcfletch/pyopengl-demo',
            projectName='OpenGL-Demo',
            urlTemplate = GITHUB,
        ),

        # SampleSource(
        #     os.path.join(SAMPLES,'Glinter'),
        #     baseURL = "http://glinter.cvs.sourceforge.net/glinter/Glinter/",
        #     projectName='Glinter',
        # ),
        SampleSource(
            os.path.join( SAMPLES, 'mmlib' ),
            baseURL = "https://github.com/masci/mmLib",
            projectName='{Artistic License} PymmLib',
            urlTemplate = GITHUB,
        ),
        # SampleSource(
        #     os.path.join( SAMPLES, 'pybzedit' ),
        #     baseURL = "http://pybzedit.cvs.sourceforge.net/pybzedit/pybzedit/",
        #     projectName='pyBzEdit',
        # ),
        # SampleSource(
        #     os.path.join( SAMPLES, 'pyui' ),
        #     baseURL = "http://pyui.cvs.sourceforge.net/pyui/PyUIcvs/",
        #     projectName='{LGPL} PyUI',
        # ),
        SampleSource(
            os.path.join( SAMPLES, 'pyui2' ),
            baseURL = "https://github.com/Ripsnorta/pyui2",
            projectName='{LGPL} PyUI2',
            urlTemplate=GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'visionegg' ),
            baseURL ='http://github.com/visionegg/visionegg',
            projectName='{LGPL} VisionEgg',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pymt' ),
            baseURL ='http://github.com/tito/pymt',
            projectName='{LGPL} PyMT',
            urlTemplate = GITHUB,
        ),
#        SampleSource(
#            os.path.join( SAMPLES, 'glchess' ),
#            baseURL ='http://svn.gnome.org/viewvc/gnome-games/trunk/glchess',
#            projectName='{GPL} GLChess',
#            urlTemplate = VIEWSVN,
#        ),
        SampleSource(
            os.path.join( SAMPLES, 'pyggel' ),
            baseURL ='https://github.com/philippTheCat/pyggel',
            projectName='{LGPL} Pyggel',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'pygl2d' ),
            baseURL ='https://github.com/RyanHope/PyGL2D',
            projectName='{LGPL} pygl2d',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join(SAMPLES,'scocca'),
            baseURL = 'http://bazaar.launchpad.net/~bebraw/scocca/devel',
            projectName='{GPL} Scocca',
            urlTemplate = LOGGERHEAD,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'kamaelia' ),
            baseURL ='https://github.com/sparkslabs/kamaelia',
            projectName='{LGPL or GPL or MPL} Kamaelia',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'agog' ),
            baseURL='https://github.com/tartley/algorithmic-generation-of-opengl-geometry',
            projectName = 'AGoG',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'gloopy' ),
            baseURL = 'https://github.com/tartley/gloopy',
            projectName = 'Gloopy',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'gltutpy' ),
            baseURL = 'https://github.com/tartley/gltutpy',
            projectName = 'OpenGL Tutorial (Python Translation)',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join( SAMPLES, 'visvis' ),
            baseURL = 'https://github.com/almarklein/visvis',
            projectName = 'Visvis',
            urlTemplate = GITHUB,
        ),
        SampleSource(
            os.path.join(SAMPLES,'programmable'),
            baseURL = 'https://bitbucket.org/rndblnch/opengl-programmable/',
            projectName = '{GPL3} OpenGL-Programmable',
            urlTemplate = BITBUCKET,
        ),
        SampleSource(
            os.path.join(SAMPLES,'pyrender'),
            baseURL='https://github.com/mmatl/pyrender',
            projectName='Pyrender',
            urlTemplate=GITHUB,
        )
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
    items = list(items.items())
    items.sort()
    for name, itemset in items:
        print(name)
        for item in itemset:
            print(' ', item.projectName, item.deltaPath, item.lineText)
    
