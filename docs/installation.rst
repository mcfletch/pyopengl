Installation
============

Install PyOpenGL and its accelerators from PyPI, into the system Python or a
virtual environment:

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate
   $ uv add PyOpenGL PyOpenGL_accelerate

You can, if desired, just specify `PyOpenGL_accelerate` as it will pull in
the corresponding PyOpenGL version.  The versions of the two must
match.  The two share the dispatch extension's generated tables, so
``PyOpenGL_accelerate`` requires the exact ``PyOpenGL`` it was released with.
Installing or upgrading accelerate also installs the matching ``PyOpenGL``.
Upgrading ``PyOpenGL`` on its own leaves the older accelerate in place.
PyOpenGL detects a mismatched pair when it builds the first entry point, and
raises an error naming both versions.

You can ask PyOpenGL to ignore the installed accelerate by setting an 
environment variable:

   ``PYOPENGL_USE_ACCELERATE=0``

to disable the attempt to use the accelerate module, while the module 
is optional on CPython (and not used on PyPy), it is generally important 
to use it if you are doing more than trivial work with PyOpenGL.

.. note::

   On common platforms, a pre-built `PyOpenGL_accelerate`` should be available
   as the project uses CIBuildWheel to create binary package builds for Linux,
   Windows and MacOS.

GLUT and GLE on Windows
-----------------------

OpenGL and GLU are part of Windows.  GLUT and GLE are not, so install them
with the ``glut`` extra:

.. code-block:: console

   $ pip install PyOpenGL[glut]
   $ uv add PyOpenGL[glut] PyOpenGL_accelerate

The extra installs ``PyOpenGL-glut-binaries``, which contains builds of
freeglut and GLE.  It is a Windows-only download.  A Linux or macOS install of
PyOpenGL never fetches it.  PyOpenGL finds the libraries without any
configuration.  Installing the package means accepting the licences of the
GLUT and GLE libraries, which ship beside the binaries.

A freeglut you installed yourself takes priority over the bundled build.  A
freeglut on ``PATH`` (from the official Windows binaries, MSYS2 or vcpkg) is
the one PyOpenGL uses.  With neither installed, a GLUT call raises an error
naming the command above.

.. note::

   Most Linux distributions package both (``freeglut3``/``libglut``, ``libgle3``).
   On macOS, GLUT is part of the system frameworks. However, note that on Linux 
   you will not generally have GLUT or GLE installed by default, that is, you will 
   need to use your package manager to install them.

Other useful packages
---------------------

These packages will be used by PyOpenGL if they are installed:

`NumPy <https://numpy.org/>`__
    PyOpenGL passes NumPy arrays directly to the driver.  Array
    handling works without NumPy, but every geometry path is faster with it.
    Note that on PyPy NumPy is generally *slower* than a ctypes array,
    so you likely do not want to use NumPy with PyPy.

`Pillow <https://python-pillow.org/>`__
    Reads and writes the image files that textures are loaded from.

Installing from a checkout
--------------------------

.. code-block:: console

   $ git clone https://github.com/mcfletch/pyopengl.git
   $ cd pyopengl
   $ git checkout develop
   $ pip install -e . ./accelerate

Install both packages in one command, because their versions must match.
Between releases, the version in the tree is not on any package index.
Installing accelerate on its own asks PyPI for that version, and the resolver
fails.  Installing both from the checkout in one command resolves each against
the other.

Compiling ``accelerate`` needs a working Python extension-building environment:
a C compiler and the Python development headers.
