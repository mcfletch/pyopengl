Installation
============

Install PyOpenGL and its accelerators from PyPI, into the system Python or a
virtual environment:

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate

Name both packages.  They carry the same version number and have to be equal:
they share the dispatch extension's generated tables, so ``PyOpenGL_accelerate``
requires the exact ``PyOpenGL`` it was released with.  Installing or upgrading
accelerate brings the matching ``PyOpenGL`` with it, while upgrading
``PyOpenGL`` on its own leaves the older accelerate in place.  A pair that has
come apart is refused when the first entry point is built, in a message naming
both versions; ``PYOPENGL_USE_ACCELERATE=0`` in the environment runs on ctypes
until it is put right.  :doc:`c-dispatch` describes what the two halves do.

``PyOpenGL_accelerate`` is optional.  It needs a C compiler where no wheel is
published for the platform, and PyOpenGL runs on ctypes without it.

GLUT and GLE on Windows
-----------------------

OpenGL and GLU are part of Windows.  GLUT and GLE are not, so ask for them:

.. code-block:: console

   $ pip install PyOpenGL[glut]

That pulls in ``PyOpenGL-glut-binaries``, which carries builds of both freeglut
and GLE.  It is a Windows-only download: a Linux or macOS install of PyOpenGL
never fetches it.  Nothing needs configuring afterwards -- PyOpenGL finds the
libraries itself.  Installing it is agreeing to the licences of the GLUT and
GLE libraries, which ship beside the binaries.

A freeglut you installed yourself still wins over the bundled build, so a
freeglut on ``PATH`` -- from the official Windows binaries, MSYS2 or vcpkg --
is the one PyOpenGL uses.  With neither, a GLUT call raises an error naming the
command above.

Most Linux distributions package both (``freeglut3``/``libglut``, ``libgle3``),
and on macOS GLUT is part of the system frameworks.

Other packages worth having
---------------------------

`NumPy <https://numpy.org/>`__
    The array type PyOpenGL passes to the driver without copying.  Array
    handling works without it, but every geometry path is better with it.

`Pillow <https://python-pillow.org/>`__
    Reading and writing the image files a texture is loaded from.

Installing from a checkout
--------------------------

.. code-block:: console

   $ git clone https://github.com/mcfletch/pyopengl.git
   $ cd pyopengl
   $ pip install -e . ./accelerate

Both at once, for the reason above.  Between releases the version in the tree
is on no index, so installing accelerate on its own asks PyPI for a version
that is not there yet and the resolver refuses; installing both from the
checkout in one command resolves them against each other.

Compiling ``accelerate`` needs a working Python extension-building environment:
a C compiler and the Python development headers.

Building the documentation
--------------------------

``build-docs.py`` at the top of the checkout writes this documentation set.  It
generates the :doc:`reference pages <reference/index>` from the Khronos DocBook
sources, the :doc:`API pages <api/index>` from the installed packages, and then
runs Sphinx over the lot:

.. code-block:: console

   $ pip install -e .[docs]
   $ python build-docs.py

The result is in ``docs/_build/html``.  ``python build-docs.py --help`` lists
the rest, including how to rebuild one half without the other and how to
publish the built set.
