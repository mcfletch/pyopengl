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
    
    assert (after_np - start) <= 3000000, (after_np-start) # it's a 2.8MB buffer...
    assert (after_transfer - after_np) <= 3000000, (after_transfer-after_np) # again, should be about 2.8 extra MB used
