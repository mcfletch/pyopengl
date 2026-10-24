OpenGL on Windows
=================

Windows ships OpenGL and GLU as system libraries, ``opengl32.dll`` and
``glu32.dll``, so PyOpenGL can use desktop GL with nothing installed.  GLUT and
GLE are not part of Windows and are installed separately.  Windows also has no
OpenGL ES or EGL; :doc:`ANGLE <angle-gles>` provides those.

Installing
----------

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate
   $ pip install PyOpenGL[glut]              # if you want GLUT or GLE

``PyOpenGL`` is a pure-Python wheel and installs anywhere.
``PyOpenGL_accelerate`` is compiled, and publishes ``win32`` and ``win_amd64``
wheels for every supported CPython, so 32-bit and 64-bit interpreters install
a binary and need no compiler.  There is no Windows ARM64 wheel.  An ARM
machine either builds it, which needs Visual Studio's C compiler and the
Python headers, or runs the x64 interpreter under emulation.  PyOpenGL works
without accelerate in both cases.

The interpreter's word size decides which DLLs it can load: a 32-bit Python
loads only 32-bit DLLs.  Windows keeps 64-bit system DLLs in ``System32`` and
32-bit ones in ``SysWOW64``, and the file system redirector gives each process
the matching set.  The system libraries therefore load correctly in either
interpreter with no configuration.  A library you install yourself must match
the interpreter: a 64-bit ``freeglut.dll`` does not load into a 32-bit Python.

Where the GL library comes from
-------------------------------

PyOpenGL loads ``opengl32.dll`` through the Windows system library search
instead of searching ``PATH``.  The copy in ``System32`` forwards to whatever
the graphics driver installed.  A directory on ``PATH`` can hold a different
``opengl32.dll`` installed by some other software.  For example, a conda
environment's ``Library\bin`` contains a Mesa ``opengl32.dll`` and comes before
``System32`` on ``PATH``.  A program loading from ``PATH`` there would get
software rendering with no warning.  ``glu32`` is loaded the same way.

A copy *beside the running executable* takes priority over both.  This lets
you give a machine with no vendor driver an OpenGL implementation.  Mesa's
Windows build is meant to be unpacked next to the program that uses it.  Put
its ``opengl32.dll`` in the directory holding ``python.exe`` (the ``Scripts``
directory, for a virtual environment), and that interpreter gets llvmpipe.
llvmpipe provides the pbuffer and create-context extensions that
:ref:`offscreen-wgl` needs.  The libraries Mesa's ``opengl32.dll`` loads in
turn go in the same directory, which is the first place they are searched for.

Libraries that are *not* part of Windows (GLUT, GLE, ANGLE's DLLs) are found
the ordinary way, through ``ctypes.util.find_library`` and then the Windows
DLL search.  ``PATH`` is how to point PyOpenGL at those.

With no vendor driver and no Mesa, Windows uses Microsoft's GDI generic
rasteriser: OpenGL 1.1, almost no extensions, and no pbuffers.

Entry points come from the driver, through the context
------------------------------------------------------

``opengl32.dll`` exports only the OpenGL 1.1 entry points.  Everything newer,
meaning every GL 1.2 and later command and every extension, is resolved through
``wglGetProcAddress``.  ``wglGetProcAddress`` works only while a context is
current, and returns entry points for that context's pixel format.  A program
therefore creates its window and context before calling anything newer than
1.1.  PyOpenGL resolves each entry point on first use for the same reason.

Two consequences follow:

- Resolving an entry point inside a ``glBegin`` block makes
  ``wglGetProcAddress`` record ``GL_INVALID_OPERATION``.  That error would
  then be reported by ``glEnd``, for a call the program never made.  PyOpenGL
  attributes the error to the lookup instead.
- ``ChoosePixelFormat``, ``SetPixelFormat``, ``SwapBuffers`` and related
  functions are GDI entry points, not GL ones.  ``opengl32`` exports none of
  them and ``wglGetProcAddress`` does not resolve them.  ``OpenGL.WGL``
  provides them, loaded from ``gdi32``.

Each entry point belongs to the context it was resolved on.  A program with
more than one context tells PyOpenGL when it changes the current one, with
``OpenGL.dispatch.make_current(handle)``.  It calls
``OpenGL.dispatch.forget_context(handle)`` when it destroys a context.
:doc:`c-dispatch` has the details.

GLUT and GLE
------------

Neither is part of Windows.  Install them with:

.. code-block:: console

   $ pip install PyOpenGL[glut]

That installs `PyOpenGL-glut-binaries
<https://github.com/mcfletch/pyopengl-glut-binaries>`__, which contains
freeglut and GLE builds for both word sizes.  The package downloads only on
Windows; a Linux or macOS install never fetches it.  It needs no configuration
after installation.  Installing it means accepting the GLUT and GLE licences,
which ship beside the binaries.

A freeglut installed some other way takes priority over the bundled build.
PyOpenGL tries these names in order and uses the first that loads:

``freeglut``, ``glut32``, ``glut``
    The names the official freeglut Windows binaries, MSYS2 and vcpkg
    install.  These come first because those builds receive fixes.
``freeglut64.vc14``, ``glut64.vc14`` (``32`` on a 32-bit interpreter)
    The builds in ``PyOpenGL-glut-binaries``.  No other package uses these
    names.

A DLL with the wrong architecture or a missing dependency fails to load, and
PyOpenGL tries the next name.  A 32-bit ``freeglut.dll`` on ``PATH`` therefore
does not stop a 64-bit interpreter from finding the bundled build.  If no name
loads, a GLUT call raises ``NullFunctionError``.

OpenGL ES
---------

Windows OpenGL is desktop GL through WGL, with no EGL or OpenGL ES.  ANGLE
provides both, translating ES calls to Direct3D 11.
``PYOPENGL_PLATFORM=angle`` binds PyOpenGL to a copy of ANGLE.
:doc:`angle-gles` covers where the DLLs come from and what that platform
supports.

ANGLE is never installed system-wide.  Applications ship their own copy:
every Chromium browser and every Electron application includes one, so a
machine may hold several of different ages.  ``PYOPENGL_ANGLE_PATH`` names the
directory holding ``libEGL.dll`` and ``libGLESv2.dll``.  PyOpenGL adds that
directory to the DLL search path before loading, so ANGLE's own dependencies
load from the same directory.

``OpenGL.EGL``, ``OpenGL.GLES1`` and ``OpenGL.GLES2`` also load an ANGLE, or a
Mesa that provides EGL, if one is already reachable under its ordinary name.
This works without selecting the ``angle`` platform.  Selecting the platform
adds the search path for a copy that is not reachable that way.

Rendering with no window
------------------------

:ref:`offscreen-wgl` is the route for desktop GL.  It uses a *pbuffer*, a
drawable that the display driver allocates in its own memory.  A pbuffer has
its own device context, belongs to no window and is never displayed.  It is
framebuffer zero for the context that renders to it, so a program draws to it
as it would to a window.  Every hardware driver for Windows since about 2009
has the three extensions it needs.

Two other routes work on Windows:

- ANGLE's EGL creates a pbuffer surface the same way EGL does on Linux.  This
  gives OpenGL ES, not desktop GL; see :doc:`angle-gles`.
- ``PYOPENGL_PLATFORM=osmesa`` with Mesa's ``osmesa.dll`` rasterises into an
  array the caller owns, and needs no driver at all: :ref:`offscreen-osmesa`.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM`` must be set before ``OpenGL`` is imported.  The values
that have an effect on Windows are:

``nt``
    Desktop GL through WGL.  PyOpenGL selects this on Windows by default.
``angle``
    OpenGL ES and EGL through ANGLE, with no desktop GL.  Never selected
    automatically; see :doc:`angle-gles`.
``osmesa``
    Mesa's off-screen interface, from ``osmesa.dll``.  See
    :ref:`offscreen-osmesa`.

Freezing an application
-----------------------

PyInstaller has to collect the GLUT and GLE builds and place them where the
loader looks at run time.  PyOpenGL ships a PyInstaller hook that does this
(``OpenGL/__pyinstaller/``).  PyInstaller finds the hook automatically, so a
frozen application needs no extra declarations.
