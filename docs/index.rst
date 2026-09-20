PyOpenGL
========

PyOpenGL is the cross-platform `Python <https://www.python.org/>`__ binding to
`OpenGL <https://www.opengl.org/>`__ and related APIs.  The binding is built on
ctypes, with an optional compiled dispatch layer beside it, and is provided
under a BSD-style licence.

.. carousel::
   :source: _static/screenshots.json
   :height: 340

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate

:doc:`installation` covers the rest, including what Windows needs for GLUT and
GLE.

The APIs
--------

PyOpenGL includes bindings for these APIs:

.. list-table::
   :widths: auto
   :header-rows: 1
   :class: entry-point-index

   * - Package
     - What it is
   * - :doc:`OpenGL.GL <reference/gl/index>`
     - Core desktop GL, 1.1 through 4.6
   * - :doc:`OpenGL.GLES1 <reference/gles1/index>`
     - Core embedded GL, version 1
   * - :doc:`OpenGL.GLES2 <reference/gles2/index>`
     - Core embedded GL, version 2
   * - :doc:`OpenGL.GLES3 <reference/gles3/index>`
     - Core embedded GL, version 3
   * - :doc:`OpenGL.GLU <reference/glu/index>`
     - Traditional utility library
   * - :doc:`OpenGL.GLUT <reference/glut/index>`
     - Traditional GL windowing library
   * - :doc:`OpenGL.GLE <reference/gle/index>`
     - Extrusion and tubing library
   * - :doc:`OpenGL.EGL <reference/egl/index>`
     - Embedded (modern) GL interfaces
   * - :doc:`OpenGL.WGL <reference/wgl/index>`
     - Windows GL interfaces
   * - :doc:`OpenGL.GLX <reference/glx/index>`
     - X Window System GL interfaces
   * - :py:mod:`OpenGL.CGL`
     - macOS GL interfaces, with or without a window
   * - :py:mod:`OpenGL.AGL`
     - macOS GL interfaces, the older Carbon ones
   * - :py:mod:`OpenGL.Tk`
     - An OpenGL widget for Tkinter

Hundreds of extensions to GL, GLES, EGL, WGL and GLX come with each package;
each reference lists them.

The packages
------------

`PyOpenGL <https://github.com/mcfletch/pyopengl>`__
    The ``OpenGL`` package, everything in the table above.

`PyOpenGL_accelerate <https://github.com/mcfletch/pyopengl>`__
    Cython-coded accelerators and the C dispatch layer.  Optional, and worth
    having: a call reaches the driver several times faster through it.  Its
    source is in the PyOpenGL repository and it releases at the same version.
    See :doc:`c-dispatch`.

`PyOpenGL-glut-binaries <https://github.com/mcfletch/pyopengl-glut-binaries>`__
    Windows builds of freeglut and GLE, pulled in by
    ``pip install PyOpenGL[glut]``.

`OpenGLContext <https://github.com/mcfletch/openglcontext>`__
    A game engine and 3D viewer built on PyOpenGL, and the suite PyOpenGL is
    tested and validated against.  A separate project with its own
    documentation; PyOpenGL does not require it.

Getting a window
----------------

PyOpenGL draws into a context; something else has to create one.  If you want
something simple and cross-platform, `GLFW <https://pypi.org/project/glfw/>`__
is a strong choice: its portability and feature coverage are wide, including on
modern Wayland Linux systems, and it is what PyOpenGL's own test suite uses.

.. code-block:: console

   $ pip install glfw

Any of these works as well, and PyOpenGL draws into whatever is current:

- `PyGame <https://www.pygame.org/>`__
- `PyQt <https://riverbankcomputing.com/software/pyqt/>`__ and
  `PySide <https://doc.qt.io/qtforpython/>`__
- `wxPython <https://wxpython.org/>`__
- PyGTK
- Tkinter, through :py:mod:`OpenGL.Tk`
- GLUT, through :doc:`OpenGL.GLUT <reference/glut/index>`, for a program that
  wants no other toolkit
- raw Xlib

Or no window at all: :doc:`egl-devices` on Linux and Android,
:doc:`cgl-offscreen` on macOS, :doc:`wgl-offscreen` on Windows, and OSMesa
anywhere, all render into an offscreen surface.

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Using PyOpenGL

   installation
   using
   opengl-programmers
   tk-widget
   reading

.. toctree::
   :maxdepth: 2
   :caption: Offscreen and platform notes

   egl-devices
   angle-gles
   cgl-offscreen
   wgl-offscreen

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/index
   api/index

.. toctree::
   :maxdepth: 2
   :caption: Working on PyOpenGL

   development
   wrapping
   c-dispatch
   building-docs

The :doc:`reference <reference/index>` pages are the OpenGL man pages with
PyOpenGL's call signatures added to them.  The :doc:`API pages <api/index>`
describe every module, class and entry point the packages define, and both are
written from this checkout each time the set is built.

Source and support
------------------

.. code-block:: console

   $ git clone https://github.com/mcfletch/pyopengl.git

Bugs and feature requests go to the
`issue tracker <https://github.com/mcfletch/pyopengl/issues>`__.
:doc:`development` describes the layout of the code and how to run the suite.

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
