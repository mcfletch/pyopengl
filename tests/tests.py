#! /usr/bin/env python
"""Overall test runner to test matrix of system options..."""
import os,sys,subprocess,logging, glob, shutil
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

def short_name( python ):
    if python.startswith( 'python' ):
        return 'cp' + python[6:].replace('.','')
    raise ValueError( "Don't know wheel format for %s"%(python,))
def have_wheel( package,python ):
    """Do we have this wheel built for the given package and python?"""
    current = os.listdir( WHEEL_DIR )
    short = short_name( python )
    for item in current:
        split = item.split('-')
        if package in item and short in item:
            return True 
    return False

def get_pygame():
    if os.path.exists( PYGAME_SOURCE ):
        subprocess.check_call( 'cd .pygame && hg pull && hg update', shell=True )
    else:
        subprocess.check_call( 'hg clone https://bitbucket.org/pygame/pygame .pygame', shell=True )
    return PYGAME_SOURCE
def pip_command( python, command, **named ):
    if python == 'python2.6':
        prefix = ['pip2.6']
    else:
        prefix = [
            python, '-m', 'pip'
        ]
    command = prefix + command 
    return subprocess.check_call( command, **named )
    
def build_pygame(pythons=PYTHONS):
    get_pygame()
    cwd = os.path.join( HERE, '.pygame' )
    
    for python in [p for p in pythons if have_python(p)]:
        for path in [
            os.path.join(cwd, 'Setup' ),
            os.path.join(cwd, 'build' ),
        ]:
            if os.path.isdir( path ):
                shutil.rmtree( path )
            elif os.path.exists( path ):
                os.remove( path )
        subprocess.check_call( [python,'config.py'], cwd=cwd )
        pip_command( python, [
            'install','--user','--upgrade','pip',
        ], cwd=cwd )
        pip_command( python, [
            'install', '--upgrade','--user','wheel',
        ], cwd=cwd )
        
        if not have_wheel( 'pygame', python ):
            pip_command( python, [
                'wheel','--wheel-dir',WHEEL_DIR, '.pygame',
            ], cwd=HERE )
        if not have_wheel( 'numpy', python ):
            pip_command( python, [
                'wheel','--wheel-dir',WHEEL_DIR, '.numpy',
            ], cwd=HERE )

def have_python( python ):
    try:
        subprocess.check_call( ['which',python])
    except subprocess.CalledProcessError as err:
        log.error( "Unable to find %s", python )
        return None
    else:
        return python 

def has_module( python, module ):
    try:
        subprocess.check_call( [python, '-c', 'import %s'%(module)])
        return True 
    except subprocess.CalledProcessError as err:
        return False 
def has_pygame( python ):
    return has_module( python, 'pygame' )
def has_numpy( python ):
    return has_module( python, 'numpy' )
        
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
    target_python = os.path.join( bin_path, 'python' )
    to_install = []
    if not has_pygame( target_python ):
        to_install.append( 'pygame' )
    if numpy and not has_numpy( target_python ):
        to_install.append( 'numpy' )
    if to_install:
        subprocess.check_call([
            os.path.join( bin_path, 'pip' ),
            'install',
            '-f', WHEEL_DIR,
            '--pre',
            '--no-index',
        ]+to_install)
    
    subprocess.check_call([
        os.path.join( bin_path, 'python' ),
        'setup.py',
        'build_ext', '--force',
        'install',
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
    env_setup()
    our_pythons = glob.glob( os.path.join( TEST_ENVS, '*','bin','python' ))
    our_pythons.sort()
    our_pythons.reverse()
    for flag in FLAGS:
        for python in our_pythons:
            for b in [True,False]:
                env = os.environ.copy()
                env['PYOPENGL_'+ flag] = str(b)
                command = [python,'test_core.py', '-v']
                if 'python2.6' not in python:
                    command.append( '-f')
                log.info( 'Starting PYOPENGL_%s=%s %s',flag, b, ' '.join(command))
                subprocess.check_call( command, env=env)

if __name__ == "__main__":
    logging.basicConfig( level = logging.INFO )
    main()
