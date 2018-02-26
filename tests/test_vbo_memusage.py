import pygamegltest
import os
# We have to import at least *one* VBO implementation...
from OpenGL import GL
assert GL
from OpenGL.arrays import vbo
try:
    import psutil
except ImportError:
    psutil = None
import pytest
try:
    import numpy as np
except ImportError:
    np = None

def get_current_memory():
    return psutil.Process(os.getpid()).memory_info().rss

@pytest.mark.skipif(not psutil,reason='No psutil available')
@pytest.mark.skipif(not np,reason='No Numpy available')
@pygamegltest.pygametest()
def test_memory_usage():
    """Test allocation as reported in Github #5"""
    start = get_current_memory()
    np_array = np.zeros( (120000, 1,6),dtype='f')
    after_np = get_current_memory()
    buffer = vbo.VBO( np_array )
    with buffer:
        after_transfer = get_current_memory()
    
    # 2.8MB buffer, on Python 2.7 is around 2.9MB usage, but on 
    # Python 3.6 we see a consistently higher memory usage (3.1MB),
    # somewhat disturbing...
    assert (after_np - start) <= 3200000, (after_np-start)
    assert (after_transfer - after_np) <= 3200000, (after_transfer-after_np)

@pytest.mark.skipif(not psutil,reason='No psutil available')
@pytest.mark.skipif(not np, reason="No numpy available")
@pygamegltest.pygametest()
def test_sf_2980896():
    """Test SF#2980896 report of memory leak on VBO transfer"""
    from OpenGL.arrays import vbo

    data = np.arange(1000).astype(np.float32)
    memory = get_current_memory()
    for i in range(100): 
        new_vbo = vbo.VBO(data)
        with new_vbo:
            # data is transferred to the VBO
            assert new_vbo is not None, new_vbo
        new_vbo.delete()
        del new_vbo 
        if i  < 1: 
            # the *first* call can load lots of libraries, etc...
            memory = get_current_memory()
        else:
            assert get_current_memory() - memory < 200, """Shouldn't have any (or at least much) extra RAM allocated..."""
