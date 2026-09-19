# Porting to OS-X (Core GL)

In theory PyOpenGL should work on OS-X, and it has worked in the past,
but we haven't yet tested the modern rewrite. PyOpenGL has an off-screen 
context using the CGL (Core GL) API, and the test suite passes with that
off-screen context.

What we need to test is:

* does PyOpenGL work with e.g. glfw or pygame or GLUT contexts?
* can OpenGLContext develop work on OS-X with any of those contexts

## Setup Process

* PyOpenGL 4.0.0a4 should have a binary release on PyPI
* The dependent sub-modules for OpenGLContext should also
  have published builds

## Biggest Test Suites

* PyOpenGL's own (tox) test suite
* OpenGLContext's base test suite
* OpenGLContext's gltf regression passes
* OpenGLContext's scripts regression passes
