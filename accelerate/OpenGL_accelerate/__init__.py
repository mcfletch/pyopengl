"""Cython-coded accelerators for the PyOpenGL wrapper

This package contains Cython accelerator modules which
attempt to speed up certain aspects of the PyOpenGL 3.x
wrapper mechanism.  The source code is part of the
PyOpenGL package and is built via the setupaccel.py
script in the top level of the PyOpenGL source package.
"""

#: The version this was built as, which is also the PyOpenGL it pairs with:
#: the two share generated tables, the dependency is pinned to this number,
#: and the extension refuses a PyOpenGL stating another.  A release bumps
#: both this and ``OpenGL/version.py``.
__version__ = "4.0.0a6"
__version_tuple__ = (4, 0, 0)
