"""Check github #43 import error on win32 nt"""

import sys
import logging

logging.basicConfig(level=logging.DEBUG)
from OpenGL.GLU import *

sys.stdout.write('OK\n')
sys.stdout.flush()
