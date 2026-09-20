OpenGL on Windows
=================

Windows ships OpenGL and GLU -- ``opengl32.dll`` and ``glu32.dll`` are part of
the system -- so PyOpenGL reaches desktop GL with nothing installed.  GLUT and
GLE are not part of Windows and arrive separately, and neither are OpenGL ES
and EGL: :doc:`ANGLE <angle-gles>` supplies those.

Installing
----------

.. code-block:: console

   $ pip install PyOpenGL PyOpenGL_accelerate
   $ pip install PyOpenGL[glut]              # if you want GLUT or GLE

``PyOpenGL`` is a pure-Python wheel and installs anywhere.
``PyOpenGL_accelerate`` is compiled, and publishes ``win32`` and ``win_amd64``
wheels for every supported CPython, so a 32-bit or 64-bit interpreter installs
a binary and needs no compiler.  There is no Windows ARM64 wheel: an ARM
machine either builds it, which wants Visual Studio's C compiler and the Python
headers, or runs the x64 interpreter under emulation.  PyOpenGL itself works
without accelerate either way.

Which DLLs load is decided by the interpreter's word size: a 32-bit Python
loads only 32-bit DLLs.  Windows keeps the two sets apart -- 64-bit system DLLs
in ``System32``, 32-bit ones in ``SysWOW64``, with the redirector giving each
process the right set -- so the system libraries are correct for either
interpreter without anything being said.  A library you install yourself is
yours to match: a 64-bit ``freeglut.dll`` on a 32-bit Python does not load.

Where the GL library comes from
-------------------------------

``opengl32.dll`` is asked of Windows rather than looked for on ``PATH``: the
copy in ``System32`` is a trampoline to whatever the graphics driver installed,
and a directory on ``PATH`` is somewhere a different one arrives because
something else was installed.  A conda environment's ``Library\bin`` carries a
Mesa ``opengl32.dll`` and sits ahead of ``System32`` on ``PATH``, so a program
that asked for the driver got software rendering with nothing saying so.
``glu32`` is chosen the same way.

A copy *beside the running executable* is preferred to both, which is how a
machine with no vendor driver is given one.  Mesa's Windows build is
distributed to be unpacked next to the program that will use it, so putting its
``opengl32.dll`` in the directory holding ``python.exe`` -- the virtual
environment's ``Scripts``, for a virtual environment -- gives that interpreter
llvmpipe, with the pbuffer and create-context extensions that
:ref:`offscreen-wgl` needs.  The same directory holds the libraries Mesa's
``opengl32.dll`` loads in turn, and it is the first place they are looked for.

Everything that is *not* a system library -- GLUT, GLE, ANGLE's DLLs -- is
looked up the ordinary way instead, through ``ctypes.util.find_library`` and
then Windows' own search, so ``PATH`` is what points at those.

With no vendor driver and no Mesa, what answers is Microsoft's GDI generic
rasteriser: OpenGL 1.1, almost no extensions, and no pbuffers.

Entry points come from the driver, through the context
------------------------------------------------------

``opengl32.dll`` exports the OpenGL 1.1 entry points and no more.  Everything
above that -- every GL 1.2-and-later command, and every extension -- is
resolved through ``wglGetProcAddress``, which answers only while a context is
current and answers for the pixel format that context was made on.  A program
therefore creates its window and its context before it calls anything modern,
and PyOpenGL builds each entry point on first use for that reason.

Two consequences:

- An entry point resolved inside a ``glBegin`` block makes
  ``wglGetProcAddress`` record ``GL_INVALID_OPERATION``, which would surface
  out of ``glEnd`` for a call nobody wrote.  PyOpenGL notes the error against
  the lookup instead.
- ``ChoosePixelFormat``, ``SetPixelFormat``, ``SwapBuffers`` and the rest of
  that family are GDI entry points rather than GL ones.  ``OpenGL.WGL`` offers
  them, taking them from ``gdi32``, since ``opengl32`` exports none of them and
  ``wglGetProcAddress`` does not answer for them either.

Because an entry point belongs to the context it was resolved on, a program
with more than one context tells PyOpenGL when it changes which is current:
``OpenGL.dispatch.make_current(handle)``, and
``OpenGL.dispatch.forget_context(handle)`` when one is destroyed.
:doc:`c-dispatch` has the detail.

GLUT and GLE
------------

Neither is part of Windows, so ask for them:

.. code-block:: console

   $ pip install PyOpenGL[glut]

That pulls in `PyOpenGL-glut-binaries
<https://github.com/mcfletch/pyopengl-glut-binaries>`__, which carries builds
of both freeglut and GLE, in both word sizes.  It is a Windows-only download --
a Linux or macOS install never fetches it -- and nothing needs configuring
afterwards.  Installing it is agreeing to the licences of the GLUT and GLE
libraries, which ship beside the binaries.

A freeglut installed some other way wins over the bundled build.  The names are
tried in this order, and the first that loads is used:

``freeglut``, ``glut32``, ``glut``
    What the official freeglut Windows binaries, MSYS2 and vcpkg install.
    Yours is the build that gets fixes, so it is preferred.
``freeglut64.vc14``, ``glut64.vc14`` (``32`` on a 32-bit interpreter)
    The builds in ``PyOpenGL-glut-binaries``, which nothing else uses those
    names for.

A DLL of the wrong architecture, or one with a missing dependency, fails to
load and the next name is tried, so a 32-bit ``freeglut.dll`` on ``PATH`` does
not stop a 64-bit interpreter finding the bundled build.  With none of them, a
GLUT call raises ``NullFunctionError``.

OpenGL ES
---------

A Windows machine's OpenGL is desktop GL through WGL; there is no EGL and no
OpenGL ES behind it.  ANGLE supplies both, translating ES onto Direct3D 11, and
``PYOPENGL_PLATFORM=angle`` binds PyOpenGL to a copy of it.  :doc:`angle-gles`
covers where the DLLs come from and what that platform does and does not offer.

ANGLE is never installed system-wide: it travels inside applications, and every
Chromium browser and every Electron application carries one, so a machine may
hold several of different ages.  ``PYOPENGL_ANGLE_PATH`` names the directory
holding ``libEGL.dll`` and ``libGLESv2.dll``, and that directory goes on the
DLL search path before the load so ANGLE's own dependencies resolve beside it.

``OpenGL.EGL``, ``OpenGL.GLES1`` and ``OpenGL.GLES2`` also load an ANGLE or an
EGL-providing Mesa that is already reachable under its ordinary name, without
the platform being selected.  What selecting the platform adds is the search
path for a copy that is not.

Rendering with no window
------------------------

:ref:`offscreen-wgl` is the route for desktop GL: a **pbuffer**, a drawable the
display driver allocates out of its own memory, with a device context of its
own that belongs to no window and appears nowhere.  It is framebuffer zero for
the context that renders to it, so nothing in a program has to know where it
is.  The three extensions it needs have been in every hardware driver for
Windows since about 2009.

Two other routes work here:

- ANGLE's EGL makes a pbuffer surface the same way EGL does on Linux: see
  :doc:`angle-gles`, which is OpenGL ES rather than desktop GL.
- ``PYOPENGL_PLATFORM=osmesa`` with Mesa's ``osmesa.dll`` rasterises into an
  array the caller owns, needing no driver at all: :ref:`offscreen-osmesa`.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM`` has to be set before ``OpenGL`` is imported.  On Windows
the values that mean anything are:

``nt``
    Desktop GL through WGL, which is what PyOpenGL selects here anyway.
``angle``
    OpenGL ES and EGL through ANGLE, and no desktop GL at all.  Never selected
    automatically -- see :doc:`angle-gles`.
``osmesa``
    Mesa's off-screen interface, from ``osmesa.dll``.  See
    :ref:`offscreen-osmesa`.

Freezing an application
-----------------------

PyInstaller needs to collect the GLUT and GLE builds, and to put them where the
running loader looks for them.  PyOpenGL ships the hook that does it
(``OpenGL/__pyinstaller/``), so a frozen application picks it up with nothing
declared.
