#! /usr/bin/env python
# Test SF#2980896

def test_sf_2980896():
    from OpenGL.arrays import vbo
    import numpy as np

    data = np.arange(1000).astype(np.float32)
    for i in range(1000000): 
        new_vbo = vbo.VBO(data)
        # optional: new_vbo.delete

if __name__ == "__main__":
    test_sf_2980896()
