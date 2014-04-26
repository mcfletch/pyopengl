#! /usr/bin/env python
"""Overall test runner to test matrix of system options..."""
import os,sys,subprocess,logging, glob
log = logging.getLogger( 'overallrunner' )
HERE = os.path.abspath(os.path.dirname( __file__ ))
TEST_ENVS = os.path.join( HERE, '.test-envs' )
WHEEL_DIR = os.path.join( HERE, '.wheels' )

PYTHONS = [
    # order is so that most-important platforms are checked first
    'python2.7',
    'python3.4',
    'python3.3',
    # python2.6 support is less important than the above at this point,
    # and doing a --user install clobbers 2.7's version of the packages
    # should use a virtualenv for all of them, really...
    'python2.6', 
]
PYGAME_SOURCE = os.path.join( HERE, '.pygame' )

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

def get_pygame():
    if os.path.exists( PYGAME_SOURCE ):
        subprocess.check_call( 'cd .pygame && hg pull && hg update', shell=True )
    else:
        subprocess.check_call( 'hg clone https://bitbucket.org/pygame/pygame .pygame', shell=True )
    return PYGAME_SOURCE

def have_python( python ):
    try:
        subprocess.check_call( ['which',python])
    except subprocess.CalledProcessError as err:
        log.error( "Unable to find %s", python )
        return None
    else:
        return python 
def ensure_virtualenv( python, numpy=True ):
    """Check/create virtualenv using our naming scheme"""
    expected_name = os.path.join( TEST_ENVS, python+['-nonum','-num'][bool(numpy)])
    log.info( 'Ensuring %s', expected_name )
    bin_path = os.path.join( expected_name, 'bin' )
    if not os.path.exists( expected_name ):
        if not os.path.exists( TEST_ENVS ):
            os.makedirs( TEST_ENVS )
        subprocess.check_call([
            'virtualenv', '-p', python, expected_name
        ])
    
    to_install = ['pygame']
    if numpy:
        to_install.append( 'numpy' )
    if to_install:
        subprocess.check_call([
            os.path.join( bin_path, 'pip' ),
            'install',
            '-f', WHEEL_DIR,
            '--pre',
            '--no-index',
        ]+to_install)
    
    # Now install PyOpenGL and OpenGL_accelerate...
    subprocess.check_call([
        os.path.join( bin_path, 'python' ),
        'setup.py',
        'develop',
    ], cwd = os.path.join( HERE, '..','OpenGL_accelerate' ))
    subprocess.check_call([
        os.path.join( bin_path, 'python' ),
        'setup.py',
        'develop',
    ], cwd = os.path.join( HERE, '..' ))

def env_setup():
    our_pythons = [p for p in PYTHONS if have_python(p)]
    for p in our_pythons:
        for numpy in [True,False]:
            ensure_virtualenv(p,numpy)

def main():
    #env_setup()
    our_pythons = glob.glob( os.path.join( TEST_ENVS, '*','bin','python' ))
    our_pythons.sort()
    our_pythons.reverse()
    for flag in FLAGS:
        for python in our_pythons:
            for b in [True,False]:
                env = os.environ.copy()
                env['PYOPENGL_'+ flag] = str(b)
                command = [python,'test_core.py']
                if 'python2.6' not in python:
                    command.append( '-f')
                log.info( 'Starting PYOPENGL_%s=%s %s',flag, b, ' '.join(command))
                subprocess.check_call( command, env=env)

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO )
    main()
