#! /usr/bin/env python
# Test SF#2980896
try:
    import numpy as np
except ImportError:
    np = None
import pytest

@pytest.mark.skipif(not np, reason="No numpy available")
def test_sf_2980896():
    from OpenGL.arrays import vbo

    data = np.arange(1000).astype(np.float32)
    for i in range(1000000): 
        new_vbo = vbo.VBO(data)
        # optional: new_vbo.delete
        assert new_vbo

if __name__ == "__main__":
    test_sf_2980896()
