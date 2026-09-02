PyOpenGL and PyOpenGL_Accelerate
=================================

PyOpenGL is normally distributed via PyPI using standard pip::

    $ pip install PyOpenGL PyOpenGL_accelerate

You can install this repository by branching/cloning and running
``pip``::

    $ cd pyopengl
    $ pip install -e .
    $ cd accelerate
    $ pip install -e .

Note that to compile PyOpenGL_accelerate you will need to have 
a functioning Python extension-compiling environment.

Freezing an application
------------------------

PyOpenGL chooses its platform module and its array format handlers through a
plug-in registry (``OpenGL.plugins``), which names each one as a string and
imports it when something matches. A tool that follows import statements sees
none of them, and freezes an application that cannot load a platform at all.

PyOpenGL therefore ships its own PyInstaller hook, which PyInstaller finds by
itself through the ``pyinstaller40`` entry point: there is nothing to configure
and nothing to list. It reports the modules the registries would import --
read from the registries themselves, so a plug-in added by another package is
carried too -- and on Windows the GLUT and GLE DLLs, which
``OpenGL.platform.ctypesloader`` opens by path.

For another freezer, ``OpenGL.plugins.registered_modules()`` is the same answer
without PyInstaller in the way::

    >>> from OpenGL import plugins
    >>> plugins.registered_modules('OpenGL')
    ['OpenGL.arrays.buffers', 'OpenGL.arrays.ctypesarrays', ...]

Learning PyOpenGL
-----------------

If you are new to PyOpenGL, you likely want to start with the OpenGLContext `tutorial page`_.
Those tutorials require OpenGLContext, (which is a big wrapper including a whole
scenegraph engine, VRML97 parser, lots of demos, etc) you can install that with::

    $ pip2.7 install "OpenGLContext-full==3.1.1"

Or you can clone it (including the tutorial sources) with::

    $ git clone https://github.com/mcfletch/openglcontext.git

or (for GitHub usage)::

    $ git clone https://github.com/mcfletch/pyopengl.git
    
The `documentation pages`_ are useful for looking up the parameters and semantics of 
PyOpenGL calls.

.. _`tutorial page`: http://pyopengl.sourceforge.net/context/tutorials/index.html
.. _`documentation pages`: https://mcfletch.github.io/pyopengl/documentation/index.html


Choosing a dispatch implementation
-----------------------------------

PyOpenGL has two implementations of the OpenGL entry points.  The C
implementation is generated from the Khronos registry and reaches the driver
roughly seven times faster -- eleven times for a call that passes an array.
Being compiled, it ships in ``PyOpenGL_accelerate``::

    $ pip install PyOpenGL PyOpenGL_accelerate

``pip install PyOpenGL`` on its own gives the ctypes implementation, which is
the one PyOpenGL has always had.  Where both are installed the C
implementation is used, and the ctypes one is selected with::

    $ PYOPENGL_DISPATCH=ctypes python yourprogram.py

Both implement the same API and the test suite runs under both.  The C
implementation additionally gives each OpenGL context its own function pointer
for every entry point, which matters in a process holding contexts of differing
capability.  See `the C dispatch layer`_ for what it covers, what differs, and
how to tell it that the current context changed.

.. _`the C dispatch layer`: https://mcfletch.github.io/pyopengl/documentation/c-dispatch.html


Running Tests
--------------

You can run the PyOpenGL test suite from a source-code checkout, the easiest
way to run the tests with the uv runner:


* git (for the checkout)
* GLUT (FreeGLUT)
* GLExtrusion library (libgle)
* GLU (normally available on any OpenGL-capable machine)
* [uv](https://docs.astral.sh/uv/)

Running the test suite from a top-level checkout looks like::

    $ uv run --with tox,tox-uv tox

The result being a lot of tests being run in a matrix of environments.
All of the environments will pull in glfw, some will also pull in 
numpy. Some will have accelerate, and some will not.

Test Suite Concerns
....................

The test suite takes a long time to complete due to the matrix of 
supported configurations; it will open *many* windows, so it will be
difficult to interact with your machine's keyboard as it runs.

On a powerful linux machine a single test run when uv has already cached 
all dependencies is around 90s (i.e. just for actually running the tests).
There is a matrix of 6 python versions, 2 numpy conditions, and 2 
acceleration conditions for around 40 minutes to run the full tox suite
if you already have all dependencies built and cached.

You can run parallel test suites with tox's -p flag, but beware that
you can crash your desktop that way.

The glfw window generally will not proceed if your Wayland session
has locked or is otherwise preventing display of the windows.

You can set `TEST_VISIBLE=false` in your environment and many of the
tests will run "headless" (i.e. will not create an on-screen display)::

    $ TEST_VISIBLE=false uv run --with tox,tox-uv tox

there are, however, a number of tests which do not respect this flag
(mostly the test_checks.py suite which runs out-of-process scripts),
for those which do the speedup and ergonimic improvement is considerable.

You can control the inter-test pause (dwell time) by setting the 
environment variable TEST_DWELL to a floating point value. Note that
there is no point having a long dwell on non-visible runs, since the
rendered frames will not be visible to you anyway.

You can use the pygame context for many test cases, to do so::

    $ TEST_WINDOWING=pygame uv run --with tox,tox-uv tox

Keep in mind that pygame versions for python3.9 often do not support
Wayland desktops.

The ``TEST_WINDOWING`` flag selects the windowing backend used by the
``tests/gl``, ``tests/gles`` and ``tests/glu`` suites:

* ``glfw`` (the default) and ``pygame`` create an on-screen window.  On a
  desktop these render on your GPU; inside a container whose compositor is
  software-rendered they will use llvmpipe regardless of the GPU present.
* ``egl`` is a *headless* backend that renders directly on a GPU through the
  ``EGL_EXT_platform_device`` extension, with no window system at all::

      $ TEST_WINDOWING=egl uv run --with tox,tox-uv tox

  This is the right choice for CI / containers (e.g. with the NVIDIA container
  runtime), where it reaches the real GPU even though the on-screen path would
  fall back to llvmpipe.  It forces ``PYOPENGL_PLATFORM=egl`` and serves both
  desktop OpenGL and OpenGL-ES contexts via an offscreen pbuffer; because there
  is no window, ``TEST_VISIBLE`` and the inter-test dwell do not apply.  By
  default it picks the first non-software EGL device; set ``TEST_EGL_DEVICE=<n>``
  to pin a specific device index.  The legacy root-level ``tests/*.py`` have no
  headless equivalent and fall back to a windowed backend under this setting.

.. image:: https://travis-ci.org/mcfletch/pyopengl.svg?branch=master
    :target: https://travis-ci.org/mcfletch/pyopengl
    :alt: Travis Tests

.. image:: https://ci.appveyor.com/api/projects/status/github/mcfletch/pyopengl
    :target: https://ci.appveyor.com/project/MikeCFletcher/pyopengl
    :alt: Appveyor Build

.. image:: https://img.shields.io/pypi/v/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Latest PyPI Version

.. image:: https://img.shields.io/pypi/dm/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Monthly download counter
