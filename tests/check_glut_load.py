# requires: glut
from __future__ import print_function
import ctypes, sys

try:
    from ctypes.util import find_library
except ImportError as err:
    from ctypes.util import findLib

    def find_library(string):
        return findLib(string)[0]


import checkutils

# The Unix library names: this check is that a plain ctypes load of them works,
# which is a question only a system that has them under those names can answer.
for _wanted in ('GL', 'GLU', 'glut'):
    if find_library(_wanted) is None:
        checkutils.skip('no library named %r on this system' % (_wanted,))

GL = OpenGL = ctypes.CDLL(find_library('GL'), mode=ctypes.RTLD_GLOBAL)
GLU = ctypes.CDLL(find_library('GLU'), mode=ctypes.RTLD_GLOBAL)
# glut shouldn't need to be global IIUC
GLUT = ctypes.CDLL(find_library('glut'), mode=ctypes.RTLD_GLOBAL)
print('GL', GL)
print('GLU', GLU)
print('GLUT', GLUT)
print(GLUT.glutSolidTeapot)
sys.stdout.write('OK\n')
sys.stdout.flush()
