# Acceleration code for PyOpenGL

This set of C (Cython) extensions provides acceleration of common operations
for slow points in PyOpenGL 3.x. It is not a requirement for using PyOpenGL
but performance without it will be poor.

## The PyOpenGL it pairs with

`PyOpenGL_accelerate` and `PyOpenGL` are released together, carry the same
version number, and have to be equal. They share the dispatch extension's
generated tables, where the slot numbering of one release is meaningless to
another, so this package requires the exact `PyOpenGL` it was built against:

    pip install PyOpenGL PyOpenGL_accelerate

Installing or upgrading `PyOpenGL_accelerate` brings the matching `PyOpenGL`
with it. Upgrading `PyOpenGL` on its own does not go the other way — it leaves
the older accelerate installed — so name both packages when you upgrade either.
A pair that has come apart is refused when the first entry point is built, in a
message naming both versions; `PYOPENGL_USE_ACCELERATE=0` in the environment
runs on ctypes until it is put right.

## Build Process

Cython is updated frequently to support newer versions of Python. As of
release 3.1.9 we no longer check in the Cython generated code for the
wrapper modules, relying on the build machines to generate the wrappers.

The Github CI Pipeline should generate and release binary builds for most
major platforms (Windows, Linux, Mac), but if you need to build from source,
a `pip install .` **should** work from the PyOpenGL repository.
