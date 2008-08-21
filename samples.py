#! /usr/bin/env python
import os

class CVSSource( object ):
	def __init__( self, root, project, dirname=None ):
		self.root = root 
		self.project = project 
		if dirname is None:
			dirname = project
		self.dirname = dirname 
	def checkout( self ):
		command = 'cvs -d%s co -d%s %s'%(
				self.root, self.dirname, self.project, 
			)
		print command
		os.system(
			command
		)
	def update( self ):
		if os.path.exists( self.dirname ):
			cwd = os.getcwd()
			try:
				os.chdir( self.dirname )
				command = 'cvs up -C'
				print command
				os.system( command )
			finally:
				os.chdir( cwd )
		else:
			self.checkout()


checkouts = [
	CVSSource(
		':pserver:anonymous@pyopengl.cvs.sourceforge.net:/cvsroot/pyopengl',
		'OpenGLContext',
	),
	CVSSource(
		':pserver:anonymous@pyopengl.cvs.sourceforge.net:/cvsroot/pyopengl',
		'Demo/PyOpenGL-Demo',
		'PyOpenGL-Demo',
	),
	CVSSource(
		':pserver:anonymous@glinter.cvs.sourceforge.net:/cvsroot/glinter',
		'Glinter',
	),
	CVSSource(
		':pserver:anonymous@pymmlib.cvs.sourceforge.net:/cvsroot/pymmlib',
		'pymmlib',
	),
	CVSSource(
		':pserver:anonymous@pybzedit.cvs.sourceforge.net:/cvsroot/pybzedit',
		'pybzedit',
	),
	CVSSource(
		':pserver:anonymous@pyui.cvs.sourceforge.net:/cvsroot/pyui',
		'PyUIcvs',
		'pyui',
	),
	CVSSource(
		':pserver:anonymous@visionegg.cvs.sourceforge.net:/cvsroot/visionegg',
		'visionegg',
	),
]

if __name__ == "__main__":
	os.chdir( '.samples' )
	for checkout in checkouts:
		checkout.update()
	
