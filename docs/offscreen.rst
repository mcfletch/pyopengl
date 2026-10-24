Offscreen rendering
===================

Offscreen rendering runs OpenGL code into a buffer with no relationship to the
screen, or into a hidden window that is never displayed.  Common uses include
rendering images for a web server on GPU hardware, test suites that run in the
background, and rendering directly to video.

In each case, the GL draws into a backing "surface" in graphics memory, and the
application then reads that surface back.  The details differ by platform, but
the mechanism is broadly the same.

Platform implementations
------------------------

.. list-table::
   :widths: auto
   :header-rows: 1
   :class: entry-point-index

   * - Platform
     - Module
     - Where the frame lands
   * - :ref:`Linux, Android <offscreen-egl>`
     - :py:mod:`OpenGL.EGL.devices`
     - A pbuffer surface, or a framebuffer object
   * - :ref:`macOS <offscreen-cgl>`
     - :py:mod:`OpenGL.CGL`
     - A framebuffer object, because there is no default one
   * - :ref:`Windows <offscreen-wgl>`
     - :py:mod:`OpenGL.WGL.offscreen`
     - A pbuffer, which *is* framebuffer zero
   * - :ref:`Anywhere Mesa is <offscreen-osmesa>`
     - :py:mod:`OpenGL.osmesa.offscreen`
     - An array the caller owns

Where a machine offers more than one, try them in the order of the table: the
system's own interface first, and OSMesa last, because OSMesa rasterises on the
CPU.  Each module provides ``available()``, or an empty device list, before
anything is created.  A program can therefore choose between them without
catching a construction failure.

:doc:`platform-linux`, :doc:`platform-macos` and :doc:`platform-windows` cover
the rest of getting OpenGL on each system.

Reading the frame back
----------------------

``glReadPixels`` returns the image **bottom-up** on every route, and image
files expect top-down rows.  The OSMesa context's :py:meth:`read` takes
``top_down=True`` to flip it.  On the other routes, flip the array with
``[::-1]``.

Rows are padded to ``GL_PACK_ALIGNMENT``, which is 4 unless something changes
it.  An RGBA read is unaffected at any width, because four bytes per pixel is
already aligned.  An RGB or single-channel read, at a width that is not a
multiple of four, has padding at the end of every row unless the alignment is
first set to 1.

The finished frame is in the buffer the context draws to, which is not always
``GL_BACK``.  A pbuffer is single-buffered unless it was requested with a back
buffer.  Reading a buffer the framebuffer does not have produces
``GL_INVALID_OPERATION`` instead of falling back to another buffer.
``glGetIntegerv`` with ``GL_DOUBLEBUFFER`` reports whether the framebuffer has
a back buffer.

The frame does not have to be copied back to the application.  It is already
in GPU memory, and the GPU can process it further before any data crosses the
bus.  `pyopengl-video <https://github.com/mcfletch/pyopengl-video>`__ passes
the colour buffer to the video encoder on the same chip: a texture goes in and
an H.264 stream comes out.  A recorder, a streamer or a render farm node that
reads frames back only to compress them can use it instead.

.. _offscreen-egl:

EGL, on Linux and Android
-------------------------

``EGL_EXT_device_enumeration`` lets a program render on a device it names,
with no display server.  :py:mod:`OpenGL.EGL.devices` reports those devices:
which exist, which extensions each advertises, its driver name, and whether it
rasterises on the CPU.  Selecting a device handle takes three separate
extensions and two string queries, and the module wraps those steps.

::

   from OpenGL.EGL import devices

   for device in devices.devices():
       print(device.index, device.driver, device.software)

What it reports
~~~~~~~~~~~~~~~

``devices(query=...)``
   Every device, in the order EGL reports them, as a tuple of ``DeviceInfo``.
   Empty where the system cannot enumerate devices at all, either because
   ``EGL_EXT_device_enumeration`` is missing or because it reports no devices.
   A caller that needs a display in that case falls back to ``eglGetDisplay``
   with ``EGL_DEFAULT_DISPLAY``.  ``query`` is the enumeration function, and
   tests can replace it.
``DeviceInfo.handle``
   The ``EGLDeviceEXT`` that
   ``eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)`` takes.
   The handle identifies the device: two ``DeviceInfo`` compare equal when they
   hold the same handle, regardless of their indexes.
``DeviceInfo.index``
   The device's position in this enumeration.  Use it to name a device to a
   user or in an environment variable.  It does not identify the device,
   because another enumeration may number the devices differently.
``DeviceInfo.extensions``
   The extensions the device reports, as a tuple.  Empty when the device does
   not support the optional extension behind this query.  An empty tuple is
   not an error.
``DeviceInfo.driver``
   The driver's name, from ``EGL_DRIVER_NAME_EXT``.  ``''`` when the device
   does not support the query.
``DeviceInfo.software``
   Whether this device rasterises on the CPU.  See below.

Which device is software
~~~~~~~~~~~~~~~~~~~~~~~~

The module decides in two steps, in this order:

#. ``EGL_MESA_device_software`` among the device's extensions.  It is
   definitive where present, so it is checked first.
#. Otherwise the driver name, matched case-insensitively as a substring against
   ``SOFTWARE_DRIVER_NAMES``: ``llvmpipe``, ``swrast``, ``softpipe``, ``swr``,
   ``lavapipe``.  The match uses substrings because drivers append versions and
   build details to the name.

A device that matches neither test is reported as hardware.  Treating a real
GPU as software only costs performance.  Treating a software device as
hardware can select a device that cannot do the work.

Requesting a display on a *hardware* device while ``LIBGL_ALWAYS_SOFTWARE``
forces software rendering makes Mesa print a warning and then crash inside
``driCreateNewScreen3``.  A program that takes device 0 without checking which
devices are software therefore crashes on any machine that has both a GPU and
a software rasteriser.

Choosing a device
~~~~~~~~~~~~~~~~~

The module reports what is available; the application picks the device with the
features it needs and stops if there is none.  Where
``LIBGL_ALWAYS_SOFTWARE`` is set, the application should pick a software
device.

::

   from OpenGL.EGL import devices
   from OpenGL.EGL.EXT.platform_base import eglGetPlatformDisplayEXT
   from OpenGL.EGL.EXT.platform_device import EGL_PLATFORM_DEVICE_EXT

   usable = [device for device in devices.devices() if not device.software]
   if not usable:
       raise SystemExit('this machine has no hardware rendering device')

   display = eglGetPlatformDisplayEXT(
       EGL_PLATFORM_DEVICE_EXT, usable[0].handle, None
   )

The offscreen backend of `OpenGLContext
<https://github.com/mcfletch/openglcontext>`__ follows this pattern.  It
honours ``LIBGL_ALWAYS_SOFTWARE`` and ``GALLIUM_DRIVER``, and reads a device
index from an environment variable to pin a run to one GPU of several.  PyOpenGL's own
headless test backend (``tests/glcontext_egl.py``) does the same.

Render nodes, through GBM
~~~~~~~~~~~~~~~~~~~~~~~~~

:py:mod:`OpenGL.EGL.gbmdevice` is the second way to reach a GPU with no
display server.  It opens a DRM render node from ``/dev/dri`` through libgbm
and returns a device EGL can create a display for.  It needs the gbm library,
and importing it raises ``ImportError`` naming the library when it is missing.
Try device enumeration first, because it needs no extra library.  Use GBM on
driver stacks that enumerate no EGL devices.

Where this works
~~~~~~~~~~~~~~~~

EGL is the GL binding on Linux and Android.  Windows has no EGL of its own,
though an installed ANGLE or Mesa provides one.  macOS has no EGL at all.
``devices()`` returns an empty tuple wherever the enumeration extension is
missing, and a program should then fall back to another route.

A machine can also lack the EGL *library* itself, which is common.  EGL ships
with the graphics driver, so a machine with no driver installed (a virtual
machine, a container, a build runner) has no EGL for the bindings to call.
macOS and Windows without ANGLE are in the same position.  Importing then
raises ``ImportError`` naming what is missing.  A program tests for EGL by
attempting the import:

::

   try:
       from OpenGL.EGL import devices
   except ImportError:
       devices = None      # no EGL here: render through GLX, WGL or CGL instead

:doc:`platform-linux` covers the rest of getting OpenGL on Linux, including
how PyOpenGL determines whether a context came from GLX or EGL.

.. _offscreen-cgl:

CGL, on macOS
-------------

:py:mod:`OpenGL.CGL` creates an OpenGL context on macOS with no window and no
window server.  CGL is the lowest-level OpenGL interface on macOS.  NSGL, the
AppKit interface that GUI toolkits use, is built on CGL and creates contexts
only for windows.  :doc:`platform-macos` describes both.

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An offscreen context created with CGL has no default framebuffer, because
framebuffer zero belongs to a window drawable.  A ``glClear`` or
``glReadPixels`` on framebuffer zero draws nothing, reads nothing and raises no
error.  Rendering must target a framebuffer object instead.

``OffscreenTarget`` creates and binds a framebuffer object inside the current
context.  It has a ``GL_RGBA8`` colour attachment and a
``GL_DEPTH24_STENCIL8`` depth/stencil attachment at the requested size, and
sets the viewport to match.  While it is bound, drawing and reading back work
as they do on a window, with no other changes to the program.  ``release()``
deletes the framebuffer and its attachments.

Choosing the renderer
~~~~~~~~~~~~~~~~~~~~~

A Mac with a GPU has an accelerated renderer.  A virtual machine, or a session
with no window server, has only Apple's CPU renderer.  On such a machine, a
request for acceleration *fails* instead of falling back.  A library that
requires the accelerated attribute gets no context at all there.

``headless_context`` and ``choose_pixel_format`` therefore try three kinds of
renderer in order, and use the first the machine offers:

``accelerated``
   Requests ``kCGLPFAAccelerated``: a GPU, where there is one.
``any``
   Names no renderer and accepts whichever renderer CGL selects.  A machine
   with no accelerated renderer needs this.
``software``
   Names Apple's CPU renderer by its id, ``kCGLRendererGenericFloatID``.  CGL
   has no "not accelerated" attribute, so the software renderer can only be
   requested by id.

``choose_pixel_format`` returns the kind it used alongside the format, so a
program can report what it got.  Pass ``renderer=`` to try one kind and no
other.

Profiles
~~~~~~~~

macOS creates a legacy 2.1 context unless a profile is requested, and has no
compatibility profile above 2.1.  ``PROFILES`` holds the three profiles CGL
offers.

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - CGL profile
     - What it is
   * - ``legacy``
     - ``kCGLOGLPVersion_Legacy``
     - GL 2.1, and the only one with the fixed-function pipeline in it
   * - ``core3``
     - ``kCGLOGLPVersion_3_2_Core``
     - GL 3.2 core
   * - ``core4``
     - ``kCGLOGLPVersion_GL4_Core``
     - GL 4.1 core, the highest version macOS supports

Building the attribute list yourself
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pixel_format_attributes`` returns the list ``CGLChoosePixelFormat`` takes,
as plain integers.  It is a pure function and needs no Mac, so the attributes a
call requests can be inspected on any platform.  A program that calls CGL
directly can build the list with it and make its own call.

::

   from OpenGL.CGL import pixel_format_attributes

   pixel_format_attributes(profile='core4', renderer='software',
                           color_size=24, alpha_size=8,
                           depth_size=24, stencil_size=8)

Errors
~~~~~~

Every CGL call returns a ``CGLError`` value, and a failure raises
``OpenGL.CGL.CGLError`` carrying that value.  ``code`` is the error number and
``operation`` is the call.  A program can therefore tell "this machine offers
no such pixel format" (``kCGLBadPixelFormat``) from "the arguments were wrong"
(``kCGLBadAttribute``) without parsing the message.

Checking a machine
~~~~~~~~~~~~~~~~~~

``tests/report_cgl_context.py`` reports whether a context can be made on the
current machine, and by which renderer, for each of the three profiles.  It
exits non-zero when no profile works.  Run it first when a suite skips every GL
case on a Mac.

::

   python tests/report_cgl_context.py

CGL is macOS only.  The module imports on any platform, because the
attribute-building functions are plain arithmetic.  Elsewhere, the first call
that needs the framework raises ``CGLError``.  :doc:`platform-macos` covers the
rest of getting OpenGL on macOS.

.. _offscreen-wgl:

Pbuffers, on Windows
--------------------

:py:mod:`OpenGL.WGL.offscreen` creates an OpenGL context on Windows with
nothing on screen.  WGL binds a context to a *device context*, and Windows
provides device contexts only for things it can draw on.  WGL has no call
that creates a context on an adapter, as EGL has, and no windowless context,
as CGL has.  Windows provides the *pbuffer* instead.  A pbuffer is a drawable
that the display driver allocates in its own memory.  It has its own device
context, belongs to no window and is never displayed.

::

   from OpenGL.WGL.offscreen import headless_context
   from OpenGL.GL import *

   with headless_context(width=256, height=256) as context:
       glClearColor(0.0, 0.0, 0.25, 1.0)
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       pixels = glReadPixels(0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE)

The pbuffer is the default framebuffer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A pbuffer needs no framebuffer object, unlike the macOS route.  Framebuffer
zero is the pbuffer, so ``glClear``, ``glReadPixels`` and other drawing calls
work as they do on a window, with no changes to the program.

The pbuffer is **single-buffered**, because nothing presents it.  The finished
frame is therefore in ``GL_FRONT``, not in ``GL_BACK``.  Pass
``double_buffer=True`` for a pbuffer with a back buffer.

One window, created and never shown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The pbuffer is built with three WGL extensions: ``wglChoosePixelFormatARB``,
``wglCreatePbufferARB`` and ``wglCreateContextAttribsARB``.  Extension entry
points are resolved through ``wglGetProcAddress``, which works only while a
context is current.  Building the pbuffer therefore needs an existing context.
On Windows, the only way to get that first context is a window, a pixel format
on its device context, and an OpenGL 1.1 context on that.  This context is used
only to resolve the entry points that build the pbuffer.

``bootstrap()`` creates one such window per process.  The window is 1×1 and
``WS_POPUP``, is never shown, and has no message loop.  The pbuffer outlives
it.  The window needs a window station and a desktop, and a service running in
session 0 has both.  It does not need anything on screen, a compositor, a
logged-in session, or a remote-desktop connection that stays open.
``release_bootstrap()`` destroys the window.  Contexts already created keep
working, because a pbuffer is not tied to the window used to create it.

Which pixel formats are accepted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default only a fully accelerated pixel format is accepted.  An unusual or
virtualised adapter may offer no pbuffer format marked as fully accelerated.
``acceleration='any'`` accepts whatever format the adapter offers instead of
failing:

::

   from OpenGL.WGL.offscreen import OffscreenContext

   context = OffscreenContext(640, 480, acceleration='any')

Profiles and versions
~~~~~~~~~~~~~~~~~~~~~

``profile`` is one of ``PROFILES``, and ``version`` is the requested GL
version.

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - What it asks for
   * - ``core``
     - ``WGL_CONTEXT_CORE_PROFILE_BIT_ARB``; the default, at GL 3.3
   * - ``compatibility``
     - ``WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB``: the fixed-function
       pipeline alongside the modern one
   * - ``legacy``
     - No profile bit at all.  A request below GL 3.2 must omit it, because
       the profile mask does not exist below 3.2.  A driver given one
       rejects the whole request instead of ignoring the bit

Resizing
~~~~~~~~

A pbuffer has a fixed size and cannot be resized.  ``resize()`` builds a new
pbuffer with the same pixel format and releases the old one.  The GL context
survives, and its textures, buffers and programs remain, because a context can
bind to any drawable with the same pixel format.

``context.lost`` reports when Windows discards a pbuffer's contents, which
happens on a display-mode change or a remote-desktop disconnect.  The pbuffer
still exists at the same size, so the program only needs to draw the frame
again.

Building the attribute lists yourself
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pixel_format_attributes`` and ``context_attributes`` return the lists
``wglChoosePixelFormatARB`` and ``wglCreateContextAttribsARB`` take, as plain
integers.  Both are pure functions and need no Windows machine, so the
attributes a call requests can be inspected on any platform.  A program that
calls WGL directly can build the lists with them and make its own calls.

::

   from OpenGL.WGL.offscreen import context_attributes, pixel_format_attributes

   pixel_format_attributes(color_bits=24, alpha_bits=8,
                           depth_bits=24, stencil_bits=8, samples=4)
   context_attributes(profile='core', version=(4, 6), debug=True)

Which drivers offer it
~~~~~~~~~~~~~~~~~~~~~~

A driver must offer ``WGL_ARB_pbuffer``, ``WGL_ARB_pixel_format`` and
``WGL_ARB_create_context``.  Every hardware OpenGL driver for Windows has
offered them since about 2009.  Microsoft's fallback, the GDI generic
rasteriser used on machines with no vendor driver, offers none of them and
supports only OpenGL 1.1.

``available()`` runs before anything is created and returns the names of the
extensions this machine lacks.  A program can use it to choose between a
pbuffer and a window.  Construction raises ``WGLError`` naming what is
missing.

::

   from OpenGL.WGL.offscreen import available, wgl_extensions

   if available():
       print('no offscreen GL here:', ', '.join(available()))
   print(len(wgl_extensions()), 'WGL extensions')

The module imports on any platform, because the attribute-building functions
are plain arithmetic.  Elsewhere, the first call that needs the Win32 API
raises ``WGLError``.  ``tests/test_wgl_offscreen.py`` holds the tests.  The
attribute-list tests run on any platform.  The rendering tests run on Windows,
and skip when the driver offers no pbuffers.

:doc:`platform-windows` covers the rest of getting OpenGL on Windows,
including how to give a machine with no vendor driver an OpenGL
implementation.

.. _offscreen-osmesa:

OSMesa, wherever Mesa is
------------------------

OSMesa is Mesa's off-screen interface.  It is a separate API, not a driver
reached through GLX or EGL.  The caller allocates the framebuffer and OSMesa
rasterises into it, with no display server, no device node and no drawable.
OSMesa therefore works where the other routes have nothing to bind to.  It
rasterises on the CPU, so it is the slowest route.

``PYOPENGL_PLATFORM=osmesa`` must be set before PyOpenGL is imported, because
the platform decides which library every entry point is loaded from:

::

   import os
   os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

   from OpenGL.osmesa.offscreen import OffscreenContext
   from OpenGL.GL import *

   with OffscreenContext(width=256, height=256) as context:
       glClearColor(0, 0, 1, 1)
       glClear(GL_COLOR_BUFFER_BIT)
       image = context.read(top_down=True)     # (height, width, 4) of bytes

The array is the default framebuffer.  ``glClear``, ``glReadPixels`` and
queries against framebuffer zero all use the array the context allocated, so
the program needs no offscreen-specific code.  ``read()`` returns a copy of the
array, bottom-up as OpenGL returns it.  ``read(top_down=True)`` flips it into
the row order image files use.

``profile`` is ``core`` or ``compatibility``, and ``version`` is the requested
GL version.  Both are passed to ``OSMesaCreateContextAttribs``, which Mesa has
provided since 12.0.  Where that entry point is missing, the module falls back
to ``OSMesaCreateContext``, which takes neither.  A core-profile request on
such a build is refused instead of returning a legacy context.

``available()`` returns the names of anything missing, before anything is
created.  It is empty when a context can be made.

::

   from OpenGL.osmesa.offscreen import available

   if available():
       print('no OSMesa here:', ', '.join(available()))

The context owns the array it renders into, and keeps it for its whole
lifetime.  Release the context with ``release()``, or use it as a context
manager.  Do not leave it to the garbage collector, because the context keeps
that array alive.

Most Linux distributions package ``libOSMesa`` (``libosmesa6`` on Debian and
Ubuntu, ``mesa-libOSMesa`` elsewhere), and Mesa's Windows build includes
``osmesa.dll``.  Apple's frameworks include no OSMesa.  On macOS, use
:ref:`CGL <offscreen-cgl>`, which has its own CPU renderer.

OpenGL ES with no window
------------------------

The routes above provide desktop OpenGL.  For OpenGL ES on Linux and Android,
EGL creates a pbuffer surface the same way it creates a window surface.  On
Windows, ANGLE provides both EGL and the ES implementation; see
:doc:`angle-gles`.
