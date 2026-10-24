Installation
============

Install PyOpenGL and its accelerators from PyPI, into the system Python or a
virtual environment:

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate

Name both packages.  They carry the same version number, and the versions must
match.  The two share the dispatch extension's generated tables, so
``PyOpenGL_accelerate`` requires the exact ``PyOpenGL`` it was released with.
Installing or upgrading accelerate also installs the matching ``PyOpenGL``.
Upgrading ``PyOpenGL`` on its own leaves the older accelerate in place.
PyOpenGL detects a mismatched pair when it builds the first entry point, and
raises an error naming both versions.  Until the versions match,
``PYOPENGL_USE_ACCELERATE=0`` in the environment makes PyOpenGL use ctypes.
:doc:`c-dispatch` describes what each package does.

``PyOpenGL_accelerate`` is optional.  PyOpenGL runs on ctypes without it.  On
a platform with no published wheel, installing it needs a C compiler.

GLUT and GLE on Windows
-----------------------

OpenGL and GLU are part of Windows.  GLUT and GLE are not, so install them
with the ``glut`` extra:

.. code-block:: console

   $ pip install PyOpenGL[glut]

The extra installs ``PyOpenGL-glut-binaries``, which contains builds of
freeglut and GLE.  It is a Windows-only download.  A Linux or macOS install of
PyOpenGL never fetches it.  PyOpenGL finds the libraries without any
configuration.  Installing the package means accepting the licences of the
GLUT and GLE libraries, which ship beside the binaries.

A freeglut you installed yourself takes priority over the bundled build.  A
freeglut on ``PATH`` (from the official Windows binaries, MSYS2 or vcpkg) is
the one PyOpenGL uses.  With neither installed, a GLUT call raises an error
naming the command above.

Most Linux distributions package both (``freeglut3``/``libglut``, ``libgle3``).
On macOS, GLUT is part of the system frameworks.

Other useful packages
---------------------

`NumPy <https://numpy.org/>`__
    PyOpenGL passes NumPy arrays to the driver without copying them.  Array
    handling works without NumPy, but every geometry path is faster with it.

`Pillow <https://python-pillow.org/>`__
    Reads and writes the image files that textures are loaded from.

Installing from a checkout
--------------------------

.. code-block:: console

   $ git clone https://github.com/mcfletch/pyopengl.git
   $ cd pyopengl
   $ pip install -e . ./accelerate

Install both packages in one command, because their versions must match.
Between releases, the version in the tree is not on any package index.
Installing accelerate on its own asks PyPI for that version, and the resolver
fails.  Installing both from the checkout in one command resolves each against
the other.

Compiling ``accelerate`` needs a working Python extension-building environment:
a C compiler and the Python development headers.
