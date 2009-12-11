#! /usr/bin/env python
import unittest

class TestFCO( unittest.TestCase ):
    def test_fco_import( self ):
        import OpenGL
        OpenGL.FORWARD_COMPATIBLE_ONLY = True
        from OpenGL import GL, GLU, GLUT

if __name__ == "__main__":
    unittest.main()
