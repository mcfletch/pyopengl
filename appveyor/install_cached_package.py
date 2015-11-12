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

def main():
    package = sys.argv[1]
    try:
        run_pip_command(
            'install',
                '-f',
                'c:\\tmp\\wheelhouse',
                '--no-index',
                '--only-binary',
                package,
        )
    except subprocess.CalledProcessError:
        run_pip_command(
            'wheel',
                '-w',
                'c:\\tmp\\wheelhouse',
                package,
        )
        run_pip_command(
            'install',
                '-f',
                'c:\\tmp\\wheelhouse',
                '--no-index',
                '--only-binary',
                package,
        )
        
if __name__ == "__main__":
    main()
