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

What is wrapped
---------------

- OpenGL 1.1 through 4.6
- OpenGL ES 1.1, 2.0, 3.0, 3.1 and 3.2
- GLU
- EGL, WGL, GLX, CGL
- GLUT and FreeGLUT
- GLE 3, the GL extrusion library
- hundreds of extensions to GL, GLES, EGL, WGL and GLX

PyOpenGL renders into a window any of these toolkits creates:

- `wxPython <https://wxpython.org/>`__
- `PyGame <https://www.pygame.org/>`__
- `PyQt <https://riverbankcomputing.com/software/pyqt/>`__ and
  `PySide <https://doc.qt.io/qtforpython/>`__
- PyGTK
- raw Xlib
- OSMesa
- Raspberry Pi BCM
- Tkinter, with the Togl widget installed

It also runs without a window, drawing into an offscreen surface: see
:doc:`egl-devices`, :doc:`cgl-offscreen` and :doc:`wgl-offscreen`.

The packages
------------

``PyOpenGL``
    The ``OpenGL`` package: ``GL``, ``GLES1``, ``GLES2``, ``GLES3``, ``GLU``,
    ``GLUT``, ``GLE``, ``WGL``, ``EGL`` and ``GLX``.

``PyOpenGL_accelerate``
    Cython-coded accelerators and the C dispatch layer.  Its source is in the
    PyOpenGL repository and it releases with, and at the same version as,
    PyOpenGL.  See :doc:`c-dispatch`.

``PyOpenGL-glut-binaries``
    Windows builds of freeglut and GLE, pulled in by
    ``pip install PyOpenGL[glut]``.

`OpenGLContext <https://github.com/mcfletch/openglcontext>`__ is a separate
project: a scenegraph and testing toolkit built on PyOpenGL, with its own
documentation.  PyOpenGL does not require it.

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Using PyOpenGL

   installation
   using
   opengl-programmers
   tk-widget

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
   reading

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
