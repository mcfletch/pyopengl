"""Instally Togl on Win32 Python"""
import sys, urllib, zipfile, logging, os, shutil
import Tkinter
log = logging.getLogger( 'ToglInstaller' )
log.setLevel( logging.INFO )

tk = Tkinter.Tk()
path = tk.getvar( 'tcl_libPath' )[0]

TARGET_DIRECTORY = os.path.join( path, 'Togl2.0' )
FILENAME = "Togl2.0-8.4-Windows.zip"
BASE_URL = "http://internap.dl.sourceforge.net/sourceforge/togl"

def main():
	if not os.path.isdir( TARGET_DIRECTORY ):
		log.info( """Togl directory: %s not found, will attempt installation""", TARGET_DIRECTORY )
		if not os.path.isfile( FILENAME ):
			URL = '%s/%s'%( BASE_URL, FILENAME )
			log.info( """%s not found, downloading %s""", FILENAME, URL )
			urllib.urlretrieve( URL, FILENAME )
			if not os.path.isfile( FILENAME ):
				sys.exit( 1 )
		
		fh = zipfile.ZipFile( FILENAME )

		os.makedirs( TARGET_DIRECTORY )
		try:
			for name in fh.namelist():
				parts = name.split( '/' )
				if len(parts) > 1 and parts[1] == 'lib' and parts[4:]:
					# wanted name...
					target = os.path.join( TARGET_DIRECTORY, *parts[4:] )
					log.info( 'Reading file from zip: %s', name )
					data = fh.read( name )
					log.info( 'Writing file: %s', target )
					open( target, 'wb' ).write( data )
		except Exception, err:
			log.warn( """Failure during installation""" )
			shutil.rmtree( TARGET_DIRECTORY )
			raise
		log.info( 'Installation complete' )
	# now test...
	log.info( 'Attempting to load the Togl module' )
	tk.call('package', 'require', 'Togl')

if __name__ == "__main__":
	logging.basicConfig()
	main()
