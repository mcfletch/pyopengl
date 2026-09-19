Offscreen OpenGL on Windows
===========================

``OpenGL.WGL.offscreen`` creates an OpenGL context on Windows with nothing on screen. WGL binds a context to a *device context*, and Windows hands those out for things it can draw on — there is no "give me a context on this adapter" call as EGL has, and no windowless context as CGL has. What Windows offers instead is the **pbuffer**: a drawable the display driver allocates out of its own memory, with a device context of its own that belongs to no window and appears nowhere.

::

   from OpenGL.WGL.offscreen import headless_context
   from OpenGL.GL import *

   with headless_context(width=256, height=256) as context:
       glClearColor(0.0, 0.0, 0.25, 1.0)
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       pixels = glReadPixels(0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE)

The pbuffer is the default framebuffer
--------------------------------------

Unlike the macOS path, this needs no framebuffer object: framebuffer zero is the pbuffer, so ``glClear``, ``glReadPixels`` and anything else drawing to it behave as they do on a window and nothing in a program has to know where it is.

It is **single-buffered**, since nothing presents it, so the finished frame is in ``GL_FRONT`` and not ``GL_BACK``. Naming a buffer a framebuffer does not have is ``GL_INVALID_OPERATION`` rather than a quiet fallback, so a program reading the frame back asks ``glGetIntegerv(GL_DOUBLEBUFFER)`` rather than assuming. Pass ``double_buffer=True`` for a pbuffer with a back buffer.

One window, created and never shown
-----------------------------------

The calls that build all of this — ``wglChoosePixelFormatARB``, ``wglCreatePbufferARB``, ``wglCreateContextAttribsARB`` — are WGL extensions, and an extension entry point is resolved through ``wglGetProcAddress``, which answers only while a context is current. That is a chicken and egg, and Windows gives one way out of it: a window, a pixel format on its device context, and an OpenGL 1.1 context on that, used for nothing but resolving the entry points that build the real thing.

``bootstrap()`` makes one of those per process — 1×1, ``WS_POPUP``, never shown, never given a message loop — and the pbuffer outlives it. What it costs is a window station and a desktop, which a service running in session 0 has. What it does not need is anything on screen, a compositor, a logged-in session, or a remote-desktop connection that stays open. ``release_bootstrap()`` gives the window back; contexts already made are unaffected, because a pbuffer is not tied to the window it was created through.

Which pixel formats are accepted
--------------------------------

By default only a fully accelerated format is taken, since that is what anything caring about speed wants. An unusual or virtualised adapter may advertise no pbuffer format calling itself fully accelerated, and rendering slowly beats refusing:

::

   from OpenGL.WGL.offscreen import OffscreenContext

   context = OffscreenContext(640, 480, acceleration='any')

Profiles
--------

``profile`` is one of ``PROFILES``, and ``version`` the GL version asked for.

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name              | What it asks for                                                                                                                                                                      |
+===================+=======================================================================================================================================================================================+
| ``core``          | ``WGL_CONTEXT_CORE_PROFILE_BIT_ARB``; the default, at GL 3.3                                                                                                                          |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``compatibility`` | ``WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB``: the fixed-function pipeline alongside the modern one                                                                                   |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``legacy``        | No profile bit at all, which is what a request below GL 3.2 must do — the profile mask did not exist there, and a driver handed one refuses the whole request rather than ignoring it |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Resizing
--------

A pbuffer is created at a fixed size and cannot be resized, so ``resize()`` builds a replacement on the same pixel format and drops the old one. The GL context survives — textures, buffers and programs are all still there afterwards — because a context binds to any drawable sharing its format.

``context.lost`` reports the one case where Windows discards what a pbuffer held, on a display-mode change or a remote-desktop disconnect. The pbuffer is still there and still the right size; the answer is to draw the frame again rather than to rebuild anything.

Building the attribute lists yourself
-------------------------------------

``pixel_format_attributes`` and ``context_attributes`` are the lists ``wglChoosePixelFormatARB`` and ``wglCreateContextAttribsARB`` take, as plain integers, and both are pure: what a call asked for can be read off without a Windows machine to ask. A program driving WGL directly can build the lists with them and make its own calls.

::

   from OpenGL.WGL.offscreen import context_attributes, pixel_format_attributes

   pixel_format_attributes(color_bits=24, alpha_bits=8,
                           depth_bits=24, stencil_bits=8, samples=4)
   context_attributes(profile='core', version=(4, 6), debug=True)

Where this works
----------------

``WGL_ARB_pbuffer``, ``WGL_ARB_pixel_format`` and ``WGL_ARB_create_context`` are what a driver has to offer, and every hardware OpenGL driver for Windows has offered them since about 2009. Microsoft's own fallback rasteriser — the GDI generic implementation, which is what a machine with no vendor driver installed has — offers none of them and is OpenGL 1.1 besides.

``available()`` answers before anything is created, returning the names of the extensions this machine lacks, so a program can choose between this and a window before committing to either. Construction raises ``WGLError`` naming what is missing rather than failing obscurely.

::

   from OpenGL.WGL.offscreen import available, wgl_extensions

   if available():
       print('no offscreen GL here:', ', '.join(available()))
   print(len(wgl_extensions()), 'WGL extensions')

The module imports anywhere — the attribute-building half is arithmetic and has no platform in it — and the first call that needs the Win32 API raises ``WGLError`` elsewhere. The Linux and Android counterpart is EGL: see :doc:`egl-devices`. The macOS one is :doc:`cgl-offscreen`. The Mesa and ANGLE builds shipped for Windows provide EGL instead, and ``OpenGL.EGL`` reaches those; ANGLE offers OpenGL ES rather than desktop GL.

Where the GL library comes from
-------------------------------

``opengl32.dll`` is asked of Windows rather than looked for on ``PATH``: the copy in ``System32`` is a trampoline to whatever the graphics driver installed, and a directory on ``PATH`` — a conda environment's ``Library\bin``, say — is somewhere a different one arrives because something else was installed.

A copy *beside the running executable* is preferred to both, which is how a machine with no vendor driver is given one. Mesa's Windows build is distributed to be unpacked next to the program that will use it, so putting its ``opengl32.dll`` in the directory holding ``python.exe`` — the virtual environment's ``Scripts``, for a virtual environment — gives that interpreter llvmpipe, with the pbuffer and create-context extensions this module needs. The same directory holds the libraries Mesa's ``opengl32.dll`` loads in turn, and it is the first place they are looked for. ``glu32`` is chosen the same way.

Checking a machine
------------------

``tests/test_wgl_offscreen.py`` holds the cases: the attribute lists run on any platform, and the rendering ones on Windows, skipping where the driver offers no pbuffers.
