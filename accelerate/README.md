# Acceleration code for PyOpenGL

This set of C (Cython) extensions provides acceleration of common operations
for slow points in PyOpenGL 3.x. It is not a requirement for using PyOpenGL
but performance without it will be poor.

## Build Process

Cython is updated frequently to support newer versions of Python. As of 
release 3.1.9 we no longer check in the Cython generated code for the 
wrapper modules, relying on the build machines to generate the wrappers.

The Github CI Pipeline should generate and release binary builds for most 
major platforms (Windows, Linux, Mac), but if you need to build from source,
a `pip install .` **should** work from the PyOpenGL repository.
