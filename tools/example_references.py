import token, tokenize, glob, os

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
		if name.startswith( prefix ) and name != 'global':
			return 1
	return 0

def glProcess( filename, tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText ):
	"""Process the name in some way"""
	print filename, sourceRow, tokenString, lineText.strip()
	

def generate_tokens_file( filename, filterFunction=glName, processFunction=glProcess ):
	"""Generate a set of tokens for the given filename"""
	file = open(filename)
	generator = tokenize.generate_tokens( file.readline )
	for (tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText) in generator:
##		print (tokenType,tokenString,(sourceRow,sourceCol),(endRow,endCol),lineText)
		if tokenType == token.NAME and filterFunction and filterFunction(tokenString):
			if processFunction:
				processFunction( filename, tokenType, tokenString, (sourceRow,sourceCol),(endRow,endCol),lineText )

def generate_tokens_dir( directory, filterFunction=glName, processFunction=glProcess ):
	"""Generate tokens for all Python files in a directory"""
	log.info( """Entering directory: %s""", directory )
	files = glob.glob( os.path.join(directory, '*.py'))
	for file in files:
		if os.path.isfile( file ):
			generate_tokens_file( file, filterFunction, processFunction )
	for file in os.listdir( directory ):
		file = os.path.join(directory,file)
		if os.path.isdir(file):
			generate_tokens_dir( file, filterFunction, processFunction )
	log.info( """Exiting directory: %s""", directory )

class SampleSource( object ):
	"""A source from which samples may be generated"""
	nameMapping = {}
	def __init__(
		self, localDir,
		baseURL = 'http://cvs.sourceforge.net/cgi-bin/viewcvs.cgi/pyopengl/OpenGLContext',
		urlTemplate = '%(baseURL)s/%(deltaPath)s?rev=HEAD&content-type=text/vnd.viewcvs-markup',
		projectName='OpenGLContext',
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
			self.nameMapping.setdefault(tokenString, []).append( (
				url,
				self.projectName,
				deltaPath,
				tokenString,
				(sourceRow,sourceCol),
				(endRow,endCol),
				lineText.strip(),
			))
	def deltaPath( self, filename ):
		"""Calculate path from root:filename"""
		deltaPath = filename[len(os.path.commonprefix( (self.localDir, filename))):]
		deltaPath = deltaPath.replace( '\\','/')
		if deltaPath[0] == '/':
			deltaPath= deltaPath[1:]
		return deltaPath
	def url( self, filename, (sourceRow,sourceCol),(endRow,endCol) ):
		"""Create a URL for the given filename"""
		deltaPath = self.deltaPath( filename )
		baseURL = self.baseURL
		if baseURL[-1] == '/':
			baseURL = baseURL[:-1]
		return self.urlTemplate %locals()
		

def loadData():
	"""Ugly global-data, assumes Mike's computer hack!"""
	for s in [
		SampleSource(
			'p:\\OpenGLContext\\',
			suppressed = {
				"debug/state.py":1,
				"tests/glget.py":1,
			},
		),
		SampleSource(
			'm:\\OpenGL\\Demo\\',
			baseURL = 'http://cvs.sourceforge.net/cgi-bin/viewcvs.cgi/pyopengl/PyOpenGL2/OpenGL/Demo/',
			projectName='OpenGL/Demo',
		),
		SampleSource(
			's:\\OpenGLApps\\kiva\\',
			baseURL = "http://scipy.net/cgi-bin/viewcvsx.cgi/kiva/",
			projectName='SciPy/kiva',
		),
## No longer using PyOpenGL
##		SampleSource(
##			's:\\OpenGLApps\\sandbox\\',
##			baseURL = "http://cvs.sourceforge.net/viewcvs.py/child/sandbox/",
##			projectName='Sandbox',
##		),
		SampleSource(
			's:\\OpenGLApps\\Glinter\\',
			baseURL = "http://cvs.sourceforge.net/viewcvs.py/glinter/Glinter/",
			projectName='Glinter',
		),
		SampleSource(
			's:\\OpenGLApps\\pymmlib\\',
			baseURL = "http://cvs.sourceforge.net/viewcvs.py/pymmlib/pymmlib/",
			projectName='{Artistic License} PymmLib',
		),
		SampleSource(
			's:\\OpenGLApps\\LGT',
			baseURL = "http://metaplay.com.au/svn/LGT/",
			projectName='LGT',
			urlTemplate = '%(baseURL)s/%(deltaPath)s',
		),
		
		SampleSource(
			's:\\OpenGLApps\\pybzedit\\',
			baseURL = "http://cvs.sourceforge.net/viewcvs.py/pybzedit/pybzedit/",
			projectName='pyBzEdit',
		),
		SampleSource(
			's:\\OpenGLApps\\PyUIcvs\\',
			baseURL = "http://cvs.sourceforge.net/cgi-bin/viewcvs.cgi/pyui/PyUIcvs/",
			projectName='{LGPL} PyUI',
		),
		SampleSource(
			's:\\OpenGLApps\\visionegg\\visionegg\\',
			baseURL = "http://cvs.sourceforge.net/cgi-bin/viewcvs.cgi/visionegg/visionegg/",
			projectName='{LGPL} VisionEgg',
		),
		
	]:
		generate_tokens_dir( s.localDir, processFunction = s.processEntry)
	result = SampleSource.nameMapping
	SampleSource.nameMapping = {}
	return result


if __name__ == "__main__":
	items = loadData()
	items = items.items()
	items.sort()
	for name, itemset in items:
		print name
		for item in itemset:
			url, project, filename = item[:3]
			text = item[-1]
			print ' ', project, filename, text
	