#! /usr/bin/env python
"""Overall test runner to test matrix of system options..."""
import os,sys,subprocess,logging 
log = logging.getLogger( 'overallrunner' )
PYTHONS = [
    'python2.7',
    'python3.3',
    'python3.4',
    # python2.6 support is less important than the above at this point,
    # and doing a --user install clobbers 2.7's version of the packages
    #'python2.6', 
]
FLAGS = [
    'USE_ACCELERATE',
    'ERROR_ON_COPY',
    'ARRAY_SIZE_CHECKING',
    'ERROR_CHECKING',
    'STORE_POINTERS',
    'CONTEXT_CHECKING',
    'ALLOW_NUMPY_SCALARS',
    'UNSIGNED_BYTE_IMAGES_AS_STRING',
]
def have_python( python ):
    try:
        subprocess.check_call( ['which',python])
    except subprocess.CalledProcessError as err:
        log.error( "Unable to find %s", python )
        return None
    else:
        return python 
    

def main():
    for flag in FLAGS:
        for python in [p for p in PYTHONS if have_python(p)]:
            for b in [True,False]:
                env = os.environ.copy()
                env['PYOPENGL_'+ flag] = str(b)
                command = [python,'test_core.py']
                if python != 'python2.6':
                    command.append( '-f')
                log.info( 'Starting PYOPENGL_%s=%s %s',flag, b, ' '.join(command))
                subprocess.check_call( command, env=env)

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO )
    main()
