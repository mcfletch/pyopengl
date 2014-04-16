#! /usr/bin/env python
"""Overall test runner to test matrix of system options..."""
import os,sys,subprocess,logging 
log = logging.getLogger( 'overallrunner' )
PYTHONS = [
    'python2.6', 
    'python2.7',
    'python3.3', # Don't have pygame for python3.3 on Ubuntu
    'python3.4',
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
    for python in [p for p in PYTHONS if have_python(p)]:
        for flag in FLAGS:
            for b in [True,False]:
                env = os.environ.copy()
                env['PYOPENGL_'+ flag] = str(b)
                log.info( 'Starting PYOPENGL_%s=%s %s test_core.py -f',flag, b, python)
                subprocess.check_call( [python,'test_core.py','-f'], env=env)

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO )
    main()
