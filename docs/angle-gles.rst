OpenGL ES through ANGLE
=======================

Windows has no EGL and no OpenGL ES of its own: its OpenGL is desktop GL through WGL, and an ES program has nothing to bind to. **ANGLE** supplies both, translating OpenGL ES onto Direct3D 11, and ``PYOPENGL_PLATFORM=angle`` is the platform module that binds PyOpenGL to it.

::

   set PYOPENGL_PLATFORM=angle
   set PYOPENGL_ANGLE_PATH=C:\path\to\angle

With those set, ``OpenGL.EGL`` and ``OpenGL.GLES2`` behave as they do on Linux — choose a config, make a pbuffer current, render and read back, with no window anywhere:

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

It is asked for, never guessed at
---------------------------------

Nothing selects this platform on its own. A Windows machine's OpenGL is WGL's, and a program that did not ask for ES should go on getting desktop GL from the driver — so naming it in ``PYOPENGL_PLATFORM`` is the whole of how it is chosen. That is also why it is safe for it to supply no desktop GL at all: nothing lands here by accident.

OpenGL ES, and only OpenGL ES
-----------------------------

ANGLE is an ES implementation. It advertises an ``EGL_CLIENT_APIS`` of ``OpenGL_ES``, offers no framebuffer config carrying ``EGL_OPENGL_BIT``, and answers ``eglBindAPI(EGL_OPENGL_API)`` with ``EGL_BAD_PARAMETER``.

So this platform's ``GL`` is ``None``, which is what PyOpenGL means by "this platform has no such library": ``OpenGL.GL`` still imports, and calling a desktop-only entry point raises ``NullFunctionError`` naming the function. A platform that answered ``opengl32`` for ``GL`` instead would hand back a desktop entry point from a binding that had promised ES, and the mismatch would surface somewhere far away from the cause.

::

   >>> from OpenGL.GL import glBegin, GL_TRIANGLES     # imports
   >>> glBegin(GL_TRIANGLES)
   NullFunctionError: Attempt to call an undefined function glBegin

ES 1, ES 2 and ES 3 are one library here. ``libGLESv2.dll`` carries ``glCreateShader`` and ``glDrawArraysInstanced`` as expected, and ``glAlphaFunc`` and ``glMatrixMode`` besides — ANGLE's ES 1 emulation lives in the same file — so ``GLES1``, ``GLES2`` and ``GLES3`` all answer with it.

Where the DLLs come from
------------------------

ANGLE is not installed system-wide on any platform. It travels inside applications — every Chromium browser and every Electron application carries a copy — so one machine may hold several, of different ages and built against different Direct3D feature levels. There is therefore no sensible default, and ``PYOPENGL_ANGLE_PATH`` names the directory holding ``libEGL.dll`` and ``libGLESv2.dll``. That directory is added to the DLL search path before the load, so ANGLE's own dependencies — its Direct3D shader compiler, and the SwiftShader library it falls back to — resolve beside it rather than against whatever is on ``PATH``.

Without the variable the ordinary library search runs, which finds an ANGLE that has been put on ``PATH`` and nothing otherwise. Asking for the platform on a machine with no ANGLE fails when the platform is selected, naming the variable to set: every entry point this platform has comes out of those two files, so there is nothing it could usefully do instead.

Those two files are Windows DLLs, and an ANGLE built for Linux or macOS installs neither, so selecting this platform elsewhere fails at selection too, naming the machine. A machine that has an EGL of its own reaches OpenGL ES through the platform PyOpenGL guesses for it, which is what leaving ``PYOPENGL_PLATFORM`` unset asks for.

What it reports
---------------

A context from a recent ANGLE on ordinary integrated hardware:

::

   EGL         1.5 (ANGLE 2.1)
   GL_VENDOR   Google Inc. (Intel)
   GL_RENDERER ANGLE (Intel, Intel(R) UHD Graphics 630, Direct3D11 vs_5_0 ps_5_0)
   GL_VERSION  OpenGL ES 3.0 (ANGLE 2.1)
   GLSL        OpenGL ES GLSL ES 3.00

The ES version depends on the ANGLE build and on what the Direct3D feature level beneath it supports; ask ``glGetString(GL_VERSION)`` rather than assuming.

Desktop GL on Windows
---------------------

This platform is for ES. For desktop OpenGL on Windows, use WGL, which is the platform PyOpenGL selects there by default; for desktop OpenGL with nothing on screen, see :doc:`wgl-offscreen`, which renders into a pbuffer the display driver allocates.
