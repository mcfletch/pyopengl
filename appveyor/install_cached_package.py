#! /usr/bin/env python
from __future__ import print_function
import os,sys,subprocess
HERE = os.path.dirname(__file__)

def run_pip_command( *args ):
    python_path = os.path.dirname(sys.executable)
    pip = os.path.join( python_path, 'Scripts','pip.exe')
    command = [
        'cmd',
        '/E:ON','/V:ON','/C',
        os.path.join( HERE,'run_with_compiler.cmd'),
        pip,
    ] + list( args )
    print( 'Running: %s'%( ' '.join(command)))
    subprocess.check_call(command)

WHEEL_HOUSE = 'c:\\projects\\pyopengl\\wheelhouse'

def main():
    package = sys.argv[1]
    if not os.path.exists( WHEEL_HOUSE ):
        os.mkdir(WHEEL_HOUSE)
    try:
        run_pip_command(
            'install',
                '-f',
                WHEEL_HOUSE,
                '--no-index',
                '--only-binary',':all:',
                package,
        )
    except subprocess.CalledProcessError:
        run_pip_command(
            'wheel',
                '-w',
                WHEEL_HOUSE,
                package,
        )
        run_pip_command(
            'install',
                '-f',
                WHEEL_HOUSE,
                '--no-index',
                '--only-binary',':all:',
                package,
        )
        
if __name__ == "__main__":
    main()
