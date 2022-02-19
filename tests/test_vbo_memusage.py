import pygamegltest
import os

# We have to import at least *one* VBO implementation...
from OpenGL import GL, arrays
from OpenGL.arrays import vbo

try:
    import psutil
except ImportError:
    psutil = None
try:
    unicode
except NameError:
    unicode = str
    long = int
import pytest
import gc

try:
    import numpy as np
except ImportError:
    np = None


def get_current_memory():
    return psutil.Process(os.getpid()).memory_info().rss


@pytest.mark.skipif(not psutil, reason="No psutil available")
@pytest.mark.skipif(not np, reason="No Numpy available")
@pygamegltest.pygametest()
def test_sf_2980896():
    """Test SF#2980896 report of memory leak on VBO transfer"""
    data = arrays.GLfloatArray.zeros((1000,))
    memory = get_current_memory()
    for i in range(100):
        new_vbo = vbo.VBO(data)
        with new_vbo:
            # data is transferred to the VBO
            assert new_vbo is not None, new_vbo
        new_vbo.delete()
        del new_vbo
        gc.collect()
        GL.glFinish()
        if i < 1:
            # the *first* call can load lots of libraries, etc...
            memory = get_current_memory()
        else:
            current = get_current_memory()
            assert current - memory < 200, (
                """Shouldn't have any (or at least much) extra RAM allocated, lost: %s"""
                % (current - memory)
            )  # fails only when run in the whole suite...
