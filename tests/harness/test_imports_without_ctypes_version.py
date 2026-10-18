"""Importing OpenGL does not read ``ctypes.__version__``.

Python 3.15 deprecates that attribute for removal in 3.20, and the suite
runs with warnings as errors, so a read during import is a collection error
on 3.15 and an ``AttributeError`` for every user once it is gone.  The child
imports the two modules that once read it with the attribute taken away.
"""

from childenv import run_in_child

WITHOUT_CTYPES_VERSION = r'''
import ctypes

ctypes.__dict__.pop('__version__', None)


def _absent(name):
    raise AttributeError(name)


ctypes.__getattr__ = _absent

import OpenGL.platform.ctypesloader
import OpenGL.raw.GL._types
'''


def test_platform_and_types_import_without_the_attribute():
    run_in_child(WITHOUT_CTYPES_VERSION)
