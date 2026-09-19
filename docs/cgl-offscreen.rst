Offscreen OpenGL on macOS
=========================

``OpenGL.CGL`` creates an OpenGL context on macOS with no window and no window server. CGL is the layer NSGL and AGL are built on, and the only one of the three that will do this — which makes it what an offscreen renderer, a batch tool, a remote shell or a CI job needs.

::

   from OpenGL.CGL import OffscreenTarget, headless_context
   from OpenGL.GL import *

   with headless_context(profile='core3') as context:
       target = OffscreenTarget(256, 256)
       try:
           glClearColor(0.0, 0.0, 0.25, 1.0)
           glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
           pixels = glReadPixels(0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE)
       finally:
           target.release()

There is no default framebuffer
-------------------------------

Framebuffer zero belongs to a drawable, and a context made this way has none. A ``glClear`` or a ``glReadPixels`` against it draws nowhere and reads nothing — it does not fail, which is the trap. Render into a framebuffer object instead.

``OffscreenTarget`` is one, built and bound inside a current context: an ``GL_RGBA8`` colour attachment and a ``GL_DEPTH24_STENCIL8`` depth/stencil one at the size asked for, with the viewport set to match. While it is bound, drawing and reading back behave as they do on a window, so nothing else in a program has to know. ``release()`` gives the names back.

Which renderer answers
----------------------

A Mac with a GPU has an accelerated renderer. A virtual machine, or a session with no window server, has only Apple's CPU renderer — and asking for acceleration there *fails* rather than falling back, which is why a library that requires the accelerated attribute cannot get a context on such a machine at all.

``headless_context`` and ``choose_pixel_format`` therefore try three kinds in order and take the first the machine offers:

``accelerated``
   Asks for ``kCGLPFAAccelerated``: a GPU, where there is one.
``any``
   Names no renderer at all and lets CGL answer with what it has. This is what a machine with no accelerated renderer needs.
``software``
   Names ``kCGLRendererGenericFloatID``, Apple's CPU renderer, by id. There is no "not accelerated" attribute, so asking for it explicitly means naming it.

``choose_pixel_format`` returns the kind it settled on alongside the format, so a program can report what it got. Pass ``renderer=`` to try one kind and no other.

Profiles
--------

macOS gives a legacy 2.1 context unless asked otherwise, and it has no compatibility profile above that: ``PROFILES`` holds the three CGL offers.

+------------+------------------------------+-----------------------------------------------------------------+
| Name       | CGL profile                  | What it is                                                      |
+============+==============================+=================================================================+
| ``legacy`` | ``kCGLOGLPVersion_Legacy``   | GL 2.1, and the only one with the fixed-function pipeline in it |
+------------+------------------------------+-----------------------------------------------------------------+
| ``core3``  | ``kCGLOGLPVersion_3_2_Core`` | GL 3.2 core                                                     |
+------------+------------------------------+-----------------------------------------------------------------+
| ``core4``  | ``kCGLOGLPVersion_GL4_Core`` | GL 4.1 core, which is as far as macOS goes                      |
+------------+------------------------------+-----------------------------------------------------------------+

Building the attribute list yourself
------------------------------------

``pixel_format_attributes`` is the list ``CGLChoosePixelFormat`` takes, as plain integers, and it is pure: what a call asked for can be read off without a Mac to ask. A program driving CGL directly can build the list with it and make its own call.

::

   from OpenGL.CGL import pixel_format_attributes

   pixel_format_attributes(profile='core4', renderer='software',
                           color_size=24, alpha_size=8,
                           depth_size=24, stencil_size=8)

Errors
------

Every call answers with a ``CGLError`` value, and a failure raises ``OpenGL.CGL.CGLError`` carrying it. ``code`` is the number and ``operation`` the call, so "this machine offers no such pixel format" (``kCGLBadPixelFormat``) and "the arguments were wrong" (``kCGLBadAttribute``) can be told apart without reading the message.

Checking a machine
------------------

``tests/report_cgl_context.py`` reports whether a context can be made here and by which renderer, for each of the three profiles, and exits non-zero when none can. It is the first thing to run when a suite skips every GL case on a Mac.

::

   python tests/report_cgl_context.py

Where this works
----------------

CGL is macOS only. The module imports anywhere — the attribute-building half is arithmetic and has no platform in it — and the first call that needs the framework raises ``CGLError`` elsewhere. The Linux and Android counterpart is EGL: see :doc:`egl-devices` for rendering on a named device with no display server there.
