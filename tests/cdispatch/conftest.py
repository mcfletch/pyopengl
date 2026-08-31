"""Make the build-time generator package importable from the test suite.

``src/cdispatch`` is a build-time tool rather than an installed package, so it
is not on ``sys.path`` by virtue of PyOpenGL being installed.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_ROOT, 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
