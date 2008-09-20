"""Script to download Win32 DLLs for GLUT and GLE"""
import urllib, logging, zipfile, os
log = logging.getLogger( 'win32install' )
log.setLevel( logging.INFO )

FILE_DATA = [
	("http://www.xmission.com/~nate/glut/glut-3.7.6-bin.zip",'glut.zip','glut-3.7.6-bin/glut32.dll','glut32.dll'),
	("http://www.vrplumber.com/gle32.zip",'gle32.zip','gle32.dll','gle32.dll'),
]

def retrieveFile( url, file ):
	urllib.urlretrieve( url, file )
	return file

def install():
	TARGET_DIRECTORY = os.path.join( os.environ['WINDIR'], 'system32' )
	log.info( 'Target directory: %r', TARGET_DIRECTORY )
	for (url,archive,path,filename) in FILE_DATA:
		target = os.path.join( TARGET_DIRECTORY, filename )
		if not os.path.isfile( target ):
			if not os.path.isfile( archive ):
				log.info( 'Downloading: %r into %r', url, archive )
				retrieveFile( url, archive )
			log.info( 'Reading archive: %r', archive )
			z = zipfile.ZipFile( archive )
			bytes = z.read(path)
			log.info( 'Writing %s bytes to %r', len(bytes), target )
			open( target, 'wb' ).write( bytes )
		else:
			log.info( 'Target file exists, not replacing' )

if __name__ == "__main__":
	logging.basicConfig()
	install()
