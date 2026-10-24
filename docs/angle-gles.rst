OpenGL ES through ANGLE
=======================

Windows has no EGL and no OpenGL ES of its own. Its OpenGL is desktop GL through WGL, so an ES program has no library to bind to. ANGLE provides both EGL and OpenGL ES, translating OpenGL ES calls to Direct3D 11. ``PYOPENGL_PLATFORM=angle`` selects the platform module that binds PyOpenGL to ANGLE.

::

   set PYOPENGL_PLATFORM=angle
   set PYOPENGL_ANGLE_PATH=C:\path\to\angle

With those set, ``OpenGL.EGL`` and ``OpenGL.GLES2`` work as they do on Linux. A program chooses a config, makes a pbuffer current, renders and reads back, with no window:

::

   from OpenGL.EGL import (
       EGL_DEFAULT_DISPLAY, EGL_OPENGL_ES_API, eglBindAPI, eglGetDisplay,
       eglInitialize, eglMakeCurrent,
   )
   from OpenGL.GLES2 import GL_COLOR_BUFFER_BIT, glClear, glClearColor

   display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
   eglInitialize(display, major, minor)
   eglBindAPI(EGL_OPENGL_ES_API)
   ...                                  # config, pbuffer surface, context
   glClearColor(0.25, 0.5, 0.75, 1.0)
   glClear(GL_COLOR_BUFFER_BIT)

Selecting ANGLE
---------------

PyOpenGL never selects this platform automatically. It is used only when ``PYOPENGL_PLATFORM`` names it. A Windows program that did not ask for ES keeps getting desktop GL from the driver through WGL. Because only an explicit request selects this platform, it can safely provide no desktop GL at all.

OpenGL ES, and only OpenGL ES
-----------------------------

ANGLE implements OpenGL ES only. It reports ``EGL_CLIENT_APIS`` as ``OpenGL_ES``, offers no framebuffer config with ``EGL_OPENGL_BIT``, and returns ``EGL_BAD_PARAMETER`` from ``eglBindAPI(EGL_OPENGL_API)``.

This platform's ``GL`` library is therefore ``None``, which is how PyOpenGL marks a library a platform does not have. ``OpenGL.GL`` still imports, and calling a desktop-only entry point raises ``NullFunctionError`` naming the function. If the platform returned ``opengl32`` for ``GL``, a program that chose ES would get desktop entry points from it, and the resulting errors would appear far from their cause.

::

   >>> from OpenGL.GL import glBegin, GL_TRIANGLES     # imports
   >>> glBegin(GL_TRIANGLES)
   NullFunctionError: Attempt to call an undefined function glBegin

ES 1, ES 2 and ES 3 come from one library. ``libGLESv2.dll`` contains ``glCreateShader`` and ``glDrawArraysInstanced``, and also ``glAlphaFunc`` and ``glMatrixMode``, because ANGLE's ES 1 emulation is in the same file. ``GLES1``, ``GLES2`` and ``GLES3`` all load from it.

Where the DLLs come from
------------------------

ANGLE is not installed system-wide on any platform. Applications ship their own copy: every Chromium browser and every Electron application includes one. A single machine may therefore hold several copies, of different ages and built for different Direct3D feature levels. PyOpenGL has no default location, so ``PYOPENGL_ANGLE_PATH`` names the directory holding ``libEGL.dll`` and ``libGLESv2.dll``. PyOpenGL adds that directory to the DLL search path before loading. ANGLE's own dependencies (its Direct3D shader compiler, and the SwiftShader fallback library) then load from the same directory instead of from ``PATH``.

Without the variable, the ordinary library search runs. It finds an ANGLE placed on ``PATH``, and nothing otherwise. Selecting the platform on a machine with no ANGLE fails at selection, with an error naming the variable to set. Every entry point this platform provides comes from those two files, so there is no fallback.

Those two files are Windows DLLs, and an ANGLE built for Linux or macOS includes neither. Selecting this platform on another system also fails at selection, with an error naming the system. A system with its own EGL gets OpenGL ES through the platform PyOpenGL selects by default, with ``PYOPENGL_PLATFORM`` unset.

What it reports
---------------

A context from a recent ANGLE on ordinary integrated hardware:

::

   EGL         1.5 (ANGLE 2.1)
   GL_VENDOR   Google Inc. (Intel)
   GL_RENDERER ANGLE (Intel, Intel(R) UHD Graphics 630, Direct3D11 vs_5_0 ps_5_0)
   GL_VERSION  OpenGL ES 3.0 (ANGLE 2.1)
   GLSL        OpenGL ES GLSL ES 3.00

The ES version depends on the ANGLE build and on the Direct3D feature level of the hardware. Read it with ``glGetString(GL_VERSION)`` instead of assuming one.

Desktop GL on Windows
---------------------

This platform provides ES only. For desktop OpenGL on Windows, use WGL, which PyOpenGL selects there by default. For desktop OpenGL with nothing on screen, see :ref:`offscreen-wgl`, which renders into a pbuffer allocated by the display driver. :doc:`platform-windows` covers the rest.
