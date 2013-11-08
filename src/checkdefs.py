#! /usr/bin/env python
import logging, os, subprocess
log = logging.getLogger( 'checker' )
def main():
    for path,dirs,files in os.walk( os.path.join('OpenGL','raw') ):
        for file in files:
            if file.endswith( '.py' ):
                log.info( 'Check: %s', file )
                try:
                    subprocess.check_call( ['python', os.path.join( path, file )] )
                except subprocess.CalledProcessError as err:
                    log.error( 'Failure loading: %s/%s', path, file )

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO )
    main()
