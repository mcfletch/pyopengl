Offscreen rendering
===================

Offscreen rendering refers to running your OpenGL code in either a buffer with
no relationship to your screen, or on a hidden window that doesn't graphically
present on your screen.  There are major use cases for this, including using
OpenGL accelerated hardware to render a graphic for a web server, test suites
that want to run in the background, direct-to-video rendering and the like.

The basic idea is that a backing "surface" is mapped into the hardware such
that the GL can draw into it, and then some mechanism is used to read that
surface back to the application.  The exact mechanisms differ by platform, but
they all work in loosely the same way.

Which route a machine has
-------------------------

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

Where a machine offers more than one, the order of that table is the order to
try them in: the system's own interface first, OSMesa last, since OSMesa
rasterises on the CPU.  Each module answers ``available()``, or an empty device
list, before anything is created, so a program can choose between them without
catching a construction failure.

:doc:`platform-linux`, :doc:`platform-macos` and :doc:`platform-windows` cover
the rest of getting OpenGL on each system.

Reading the frame back
----------------------

``glReadPixels`` hands the image over **bottom-up**, whichever route made the
context, and an image file wants it the other way; the OSMesa context's
:py:meth:`read` takes ``top_down=True`` for that, and elsewhere it is a
``[::-1]`` on the array.

Rows are padded to ``GL_PACK_ALIGNMENT``, which is 4 until something sets it.
An RGBA read at any width is unaffected, since four bytes a pixel is already
aligned; an RGB or single-channel read at a width that is not a multiple of
four has padding at the end of every row unless the alignment is set to 1
first.

A finished frame is in the buffer the context draws to, which is not always
``GL_BACK``: a pbuffer is single-buffered unless one was asked for with a back
buffer, and naming a buffer the framebuffer does not have is
``GL_INVALID_OPERATION`` rather than a quiet fallback.  ``glGetIntegerv``
with ``GL_DOUBLEBUFFER`` is the question to ask.

.. _offscreen-egl:

EGL, on Linux and Android
-------------------------

``EGL_EXT_device_enumeration`` lets a program render on a device it names, with
no display server anywhere, and :py:mod:`OpenGL.EGL.devices` reports what those
devices are: which exist, what each advertises, what its driver calls itself,
and whether it rasterises on the CPU.  Getting from "the extension exists" to
"this handle is the one I want" takes three separate extensions and a pair of
string queries, so the module does it once.

::

   from OpenGL.EGL import devices

   for device in devices.devices():
       print(device.index, device.driver, device.software)

What it reports
~~~~~~~~~~~~~~~

``devices(query=...)``
   Every device, in the order EGL reports them, as a tuple of ``DeviceInfo``.
   Empty where the system cannot enumerate devices at all -- no
   ``EGL_EXT_device_enumeration``, or none behind it.  A caller that needs a
   display in that case falls back to ``eglGetDisplay`` with
   ``EGL_DEFAULT_DISPLAY``.  ``query`` is the enumeration step, exposed so it
   can be replaced in tests.
``DeviceInfo.handle``
   The ``EGLDeviceEXT`` itself, which is what
   ``eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)`` takes.
   It is the device's identity: two ``DeviceInfo`` compare equal when they hold
   the same handle, whatever index each was enumerated at.
``DeviceInfo.index``
   Where it appeared in this enumeration.  Useful for naming a device to a user
   or in an environment variable; not an identity, since another enumeration
   may number them differently.
``DeviceInfo.extensions``
   What the device says it supports, as a tuple.  Empty where it does not
   answer the query, which is a device that does not implement the optional
   extension the query comes from rather than an error.
``DeviceInfo.driver``
   What the driver calls itself -- ``EGL_DRIVER_NAME_EXT``.  ``''`` where the
   device does not answer.
``DeviceInfo.software``
   Whether this device rasterises on the CPU.  See below.

Which device is software
~~~~~~~~~~~~~~~~~~~~~~~~

The question is decided in two steps, in this order:

#. ``EGL_MESA_device_software`` among the device's extensions.  Where it is
   present it is definitive, which is why it is checked first.
#. Otherwise the driver name, matched case-insensitively as a substring against
   ``SOFTWARE_DRIVER_NAMES``: ``llvmpipe``, ``swrast``, ``softpipe``, ``swr``,
   ``lavapipe``.  Substrings because drivers append versions and build details
   to the name.

A device that answers neither is reported as hardware.  Treating a real GPU as
software costs performance; the reverse can mean selecting a device that cannot
do the work.

Asking Mesa for a display on a *hardware* device while
``LIBGL_ALWAYS_SOFTWARE`` demands software rendering is a contradiction it
warns about and then crashes on, inside ``driCreateNewScreen3``.  A caller that
can ask which devices are software avoids it; one that cannot, and takes device
0, dumps core on any machine that has both a GPU and a software rasteriser.

Choosing is the caller's
~~~~~~~~~~~~~~~~~~~~~~~~

This module reports fact.  *Choosing* between the devices is policy and stays
with the caller, because a renderer wanting speed and a test wanting
reproducibility disagree about which device is right.

A policy has one hard constraint, which is the crash above: where the
environment demands software rendering, the device chosen has to be a software
one.  Read the environment first and let it decide which kind to look for.

::

   import os

   from OpenGL.EGL import devices
   from OpenGL.EGL.EXT.platform_base import eglGetPlatformDisplayEXT
   from OpenGL.EGL.EXT.platform_device import EGL_PLATFORM_DEVICE_EXT

   available = devices.devices()
   # Mesa reads the variable as set-or-not, so read it the same way.
   software = os.environ.get('LIBGL_ALWAYS_SOFTWARE', '').lower() not in (
       '', '0', 'false', 'no', 'off'
   )
   wanted = [device for device in available if device.software == software]
   if not wanted and software:
       raise RuntimeError(
           'software rendering was demanded and there is no software device: %s'
           % (available,)
       )
   chosen = (wanted or available)[0]

   display = eglGetPlatformDisplayEXT(
       EGL_PLATFORM_DEVICE_EXT, chosen.handle, None
   )

The fallback runs one way only.  Wanting a GPU and finding a CPU rasteriser is
slow, so it renders; wanting software and finding a GPU is the pair that dumps
core, so it stops.

`OpenGLContext <https://github.com/mcfletch/openglcontext>`__'s offscreen
backend is a worked example of the policy half: it honours
``LIBGL_ALWAYS_SOFTWARE`` and ``GALLIUM_DRIVER``, takes an explicit device
index from an environment variable where a run has to be pinned to one GPU of
several, and refuses the contradiction rather than serving it.  PyOpenGL's own
headless test backend (``tests/glcontext_egl.py``) is the same policy at a
smaller size.

Render nodes, through GBM
~~~~~~~~~~~~~~~~~~~~~~~~~

:py:mod:`OpenGL.EGL.gbmdevice` is the other way onto a GPU with no display
server: it opens a DRM render node from ``/dev/dri`` through libgbm and hands
back a device EGL will make a display for.  It needs the gbm library, and the
import raises ``ImportError`` naming it where there is none.  Device
enumeration above is the first thing to try, since it needs no extra library;
this is what answers on a driver stack that enumerates no EGL devices.

Where this works
~~~~~~~~~~~~~~~~

EGL is the GL binding on Linux and Android.  Windows has no EGL of its own --
an installed ANGLE or Mesa provides one -- and macOS has none at all.
``devices()`` answers with an empty tuple wherever the enumeration extension is
absent, so the empty answer is the signal to fall back.

Having no EGL *library* is a step earlier than that, and it is common: EGL
ships with the graphics driver, so a machine with none installed -- a virtual
machine, a container, a build runner -- has nothing for the bindings to call,
as macOS and a Windows without ANGLE have nothing.  Importing raises
``ImportError`` there, naming what is missing.  That import is how a program
asks whether this machine has EGL at all:

::

   try:
       from OpenGL.EGL import devices
   except ImportError:
       devices = None      # no EGL here: render through GLX, WGL or CGL instead

:doc:`platform-linux` covers the rest of getting OpenGL on Linux, including
which of GLX and EGL a context comes from.

.. _offscreen-cgl:

CGL, on macOS
-------------

:py:mod:`OpenGL.CGL` creates an OpenGL context on macOS with no window and no
window server.  CGL is the layer NSGL is built on, and the only one of the two
that will do this.

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

Framebuffer zero belongs to a drawable, and a context made this way has none.
A ``glClear`` or a ``glReadPixels`` against it draws nowhere and reads nothing,
and raises no error.  Render into a framebuffer object instead.

``OffscreenTarget`` is one, built and bound inside a current context: a
``GL_RGBA8`` colour attachment and a ``GL_DEPTH24_STENCIL8`` depth/stencil one
at the size asked for, with the viewport set to match.  While it is bound,
drawing and reading back behave as they do on a window, so nothing else in a
program has to know.  ``release()`` gives the names back.

Which renderer answers
~~~~~~~~~~~~~~~~~~~~~~

A Mac with a GPU has an accelerated renderer.  A virtual machine, or a session
with no window server, has only Apple's CPU renderer -- and asking for
acceleration there *fails* rather than falling back, which is why a library
that requires the accelerated attribute cannot get a context on such a machine
at all.

``headless_context`` and ``choose_pixel_format`` therefore try three kinds in
order and take the first the machine offers:

``accelerated``
   Asks for ``kCGLPFAAccelerated``: a GPU, where there is one.
``any``
   Names no renderer at all and lets CGL answer with what it has.  This is what
   a machine with no accelerated renderer needs.
``software``
   Names ``kCGLRendererGenericFloatID``, Apple's CPU renderer, by id.  There is
   no "not accelerated" attribute, so asking for it explicitly means naming it.

``choose_pixel_format`` returns the kind it settled on alongside the format, so
a program can report what it got.  Pass ``renderer=`` to try one kind and no
other.

Profiles
~~~~~~~~

macOS gives a legacy 2.1 context unless asked otherwise, and it has no
compatibility profile above that: ``PROFILES`` holds the three CGL offers.

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
     - GL 4.1 core, which is as far as macOS goes

Building the attribute list yourself
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pixel_format_attributes`` is the list ``CGLChoosePixelFormat`` takes, as
plain integers, and it is pure: what a call asked for can be read off without a
Mac to ask.  A program driving CGL directly can build the list with it and make
its own call.

::

   from OpenGL.CGL import pixel_format_attributes

   pixel_format_attributes(profile='core4', renderer='software',
                           color_size=24, alpha_size=8,
                           depth_size=24, stencil_size=8)

Errors
~~~~~~

Every call answers with a ``CGLError`` value, and a failure raises
``OpenGL.CGL.CGLError`` carrying it.  ``code`` is the number and ``operation``
the call, so "this machine offers no such pixel format"
(``kCGLBadPixelFormat``) and "the arguments were wrong" (``kCGLBadAttribute``)
can be told apart without reading the message.

Checking a machine
~~~~~~~~~~~~~~~~~~

``tests/report_cgl_context.py`` reports whether a context can be made here and
by which renderer, for each of the three profiles, and exits non-zero when none
can.  It is the first thing to run when a suite skips every GL case on a Mac.

::

   python tests/report_cgl_context.py

CGL is macOS only.  The module imports anywhere -- the attribute-building half
is arithmetic and has no platform in it -- and the first call that needs the
framework raises ``CGLError`` elsewhere.  :doc:`platform-macos` covers the rest
of getting OpenGL there.

.. _offscreen-wgl:

Pbuffers, on Windows
--------------------

:py:mod:`OpenGL.WGL.offscreen` creates an OpenGL context on Windows with
nothing on screen.  WGL binds a context to a *device context*, and Windows
hands those out for things it can draw on -- there is no "give me a context on
this adapter" call as EGL has, and no windowless context as CGL has.  What
Windows offers instead is the **pbuffer**: a drawable the display driver
allocates out of its own memory, with a device context of its own that belongs
to no window and appears nowhere.

::

   from OpenGL.WGL.offscreen import headless_context
   from OpenGL.GL import *

   with headless_context(width=256, height=256) as context:
       glClearColor(0.0, 0.0, 0.25, 1.0)
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       pixels = glReadPixels(0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE)

The pbuffer is the default framebuffer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike the macOS path, this needs no framebuffer object: framebuffer zero is
the pbuffer, so ``glClear``, ``glReadPixels`` and anything else drawing to it
behave as they do on a window and nothing in a program has to know where it is.

It is **single-buffered**, since nothing presents it, so the finished frame is
in ``GL_FRONT`` and not ``GL_BACK``.  Pass ``double_buffer=True`` for a pbuffer
with a back buffer.

One window, created and never shown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The calls that build all of this -- ``wglChoosePixelFormatARB``,
``wglCreatePbufferARB``, ``wglCreateContextAttribsARB`` -- are WGL extensions,
and an extension entry point is resolved through ``wglGetProcAddress``, which
answers only while a context is current.  Building the pbuffer therefore needs
a context already, and Windows gives one way out of that: a window, a pixel
format on its device context, and an OpenGL 1.1 context on that, used for
nothing but resolving the entry points that build the real thing.

``bootstrap()`` makes one of those per process -- 1×1, ``WS_POPUP``, never
shown, never given a message loop -- and the pbuffer outlives it.  What it
costs is a window station and a desktop, which a service running in session 0
has.  What it does not need is anything on screen, a compositor, a logged-in
session, or a remote-desktop connection that stays open.
``release_bootstrap()`` gives the window back; contexts already made are
unaffected, because a pbuffer is not tied to the window it was created through.

Which pixel formats are accepted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default only a fully accelerated format is taken.  An unusual or virtualised
adapter may advertise no pbuffer format calling itself fully accelerated;
``acceleration='any'`` takes whatever it offers instead of failing:

::

   from OpenGL.WGL.offscreen import OffscreenContext

   context = OffscreenContext(640, 480, acceleration='any')

Profiles and versions
~~~~~~~~~~~~~~~~~~~~~

``profile`` is one of ``PROFILES``, and ``version`` the GL version asked for.

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
     - No profile bit at all, which is what a request below GL 3.2 must do --
       the profile mask did not exist there, and a driver handed one refuses
       the whole request rather than ignoring it

Resizing
~~~~~~~~

A pbuffer is created at a fixed size and cannot be resized, so ``resize()``
builds a replacement on the same pixel format and drops the old one.  The GL
context survives -- textures, buffers and programs are all still there
afterwards -- because a context binds to any drawable sharing its format.

``context.lost`` reports the one case where Windows discards what a pbuffer
held, on a display-mode change or a remote-desktop disconnect.  The pbuffer is
still there and still the right size; the answer is to draw the frame again
rather than to rebuild anything.

Building the attribute lists yourself
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``pixel_format_attributes`` and ``context_attributes`` are the lists
``wglChoosePixelFormatARB`` and ``wglCreateContextAttribsARB`` take, as plain
integers, and both are pure: what a call asked for can be read off without a
Windows machine to ask.  A program driving WGL directly can build the lists
with them and make its own calls.

::

   from OpenGL.WGL.offscreen import context_attributes, pixel_format_attributes

   pixel_format_attributes(color_bits=24, alpha_bits=8,
                           depth_bits=24, stencil_bits=8, samples=4)
   context_attributes(profile='core', version=(4, 6), debug=True)

Which drivers offer it
~~~~~~~~~~~~~~~~~~~~~~

``WGL_ARB_pbuffer``, ``WGL_ARB_pixel_format`` and ``WGL_ARB_create_context``
are what a driver has to offer, and every hardware OpenGL driver for Windows
has offered them since about 2009.  Microsoft's own fallback rasteriser -- the
GDI generic implementation, which is what a machine with no vendor driver
installed has -- offers none of them and is OpenGL 1.1 besides.

``available()`` answers before anything is created, returning the names of the
extensions this machine lacks, so a program can choose between this and a
window before committing to either.  Construction raises ``WGLError`` naming
what is missing rather than failing obscurely.

::

   from OpenGL.WGL.offscreen import available, wgl_extensions

   if available():
       print('no offscreen GL here:', ', '.join(available()))
   print(len(wgl_extensions()), 'WGL extensions')

The module imports anywhere -- the attribute-building half is arithmetic and
has no platform in it -- and the first call that needs the Win32 API raises
``WGLError`` elsewhere.  ``tests/test_wgl_offscreen.py`` holds the cases: the
attribute lists run on any platform, and the rendering ones on Windows,
skipping where the driver offers no pbuffers.

:doc:`platform-windows` covers the rest of getting OpenGL there, including
where a machine with no vendor driver gets one.

.. _offscreen-osmesa:

OSMesa, wherever Mesa is
------------------------

OSMesa is Mesa's off-screen interface, and an API of its own rather than a
driver reached through GLX or EGL: the caller allocates the framebuffer, OSMesa
rasterises into it, and there is no display server, no device node and no
drawable involved.  It therefore works where the other routes have nothing to
bind to, and it rasterises on the CPU, so it is the slowest of them.

``PYOPENGL_PLATFORM=osmesa`` has to be set before PyOpenGL is imported, because
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

The array is the default framebuffer.  ``glClear``, ``glReadPixels`` and the
queries a program makes against framebuffer zero all land in the array the
context allocated, so nothing has to be told it is rendering off-screen.
``read()`` returns a copy of it, bottom-up as OpenGL hands it over;
``read(top_down=True)`` flips it, which is what an image file wants.

``profile`` is ``core`` or ``compatibility`` and ``version`` the GL version
asked for.  Both are served by ``OSMesaCreateContextAttribs``, which Mesa has
had since 12.0; where that entry point is absent this falls back to
``OSMesaCreateContext``, which takes neither, so a request for a core profile
on such a build is refused rather than quietly answered with a legacy context.

``available()`` names what is missing before anything is created, and is empty
where a context can be made.

::

   from OpenGL.osmesa.offscreen import available

   if available():
       print('no OSMesa here:', ', '.join(available()))

The context owns the array it renders into and holds it for its own lifetime.
Release it -- ``release()``, or use it as a context manager -- rather than
dropping it and letting the collector do it, since a context is what keeps
that array alive.

Where the library comes from: ``libOSMesa`` is packaged by most Linux
distributions (``libosmesa6`` on Debian and Ubuntu, ``mesa-libOSMesa``
elsewhere), and Mesa's Windows build carries ``osmesa.dll``.  There is no
OSMesa for macOS in Apple's frameworks; :ref:`CGL <offscreen-cgl>` is what
answers there, and has a CPU renderer of its own.

OpenGL ES with no window
------------------------

The routes above are desktop OpenGL.  For OpenGL ES, EGL on Linux and Android
makes a pbuffer surface the same way it makes a window surface, and on Windows
ANGLE supplies both the EGL and the ES implementation: see :doc:`angle-gles`.
