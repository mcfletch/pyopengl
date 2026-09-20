OpenGL on Linux
===============

Linux reaches OpenGL through two interfaces, and a machine usually has both.
PyOpenGL loads whichever of them is installed and works out which one a context
came from, so a program does not have to say, and nothing has to be configured
for the common cases.

BSD systems take this same path.

GLX, EGL, X11 and Wayland
-------------------------

GLX is part of the X protocol: a GLX context belongs to an X display and an X
drawable, and it is how X11 programs have got OpenGL since 1992.

EGL is a window-system-neutral interface to the same drivers.  It is what
Wayland clients use, since Wayland carries no GLX; it is also the interface on
Android, and the one that renders with no display server at all -- see
:ref:`offscreen-egl`.

A Wayland session runs XWayland so that X11 programs keep working, and an X11
program under it gets a GLX context through XWayland exactly as it would on an
X server.  GLUT is usually one of those: freeglut has a Wayland backend, but
the builds distributions ship are X11 builds, so a GLUT program on a Wayland
desktop is an XWayland client with a GLX context.

Which interface a context came from
-----------------------------------

The environment does not answer that question.  GLUT under XWayland creates a
GLX context with ``WAYLAND_DISPLAY`` set; GLFW creates either, on either
session type, depending on how it was built and what it was asked for.  The
choice belongs to the toolkit, and is not visible from inside PyOpenGL.

GLX and EGL keep independent per-thread current-context state, so the state can
be read rather than inferred: PyOpenGL loads both where both exist and probes
for a live context in each.  The interface holding one is the interface an
entry point is resolved through, and the probe runs at the point of resolution
rather than at import, so a program that makes its context after importing
``OpenGL`` is answered correctly.

A name that says which interface it belongs to goes to that interface whatever
is current: ``glX*`` through ``glXGetProcAddressARB``, ``egl*`` through
``eglGetProcAddress``.  A core ``gl*`` name follows the context, and falls back
to GLX where nothing is current.

Routing an ``egl*`` name by its prefix is what keeps it off GLX.  Under
libglvnd, ``glXGetProcAddressARB`` manufactures a dispatch stub for *any* name
asked of it, including an ``egl*`` one: the pointer marshals and calls without
error but is not the entry point, and an EGL client extension resolved that way
returns failure with ``EGL_SUCCESS`` set.  The device-enumeration family in
:ref:`offscreen-egl` is called before any context exists, so the prefix is all
there is to route it by.

The same stub is why PyOpenGL cannot report on Linux whether the driver has a
given entry point: a lookup always answers.  :doc:`c-dispatch` covers which
platforms can.

Finding the libraries
---------------------

Each library is loaded when something first needs it.  The name asked for
(``GL``, ``GLU``, ``glut``) becomes ``lib<name>.so``, and that is handed
straight to ``dlopen`` rather than to ``ctypes.util.find_library`` -- so
``LD_LIBRARY_PATH``, the linker cache and an ``LD_PRELOAD`` all apply, which is
how a program is pointed at a particular driver stack.

``lib<name>.so`` is the development symlink, and most distributions ship it
only in the ``-dev`` package.  Where it is absent the versioned names are tried
in turn, highest first: ``lib<name>.so.9`` down to ``lib<name>.so.0``.  So a
machine with ``libGLU.so.1`` and no ``libGLU.so`` loads GLU.

What is asked for, in order:

.. list-table::
   :widths: auto
   :header-rows: 1
   :class: entry-point-index

   * - Asked for
     - Names tried
   * - GL
     - ``libOpenGL``, then ``libGL``; then ``libGLESv2``/``libGLESv1_CM`` on a
       system that has only those
   * - GLX
     - ``libGLX``, ``libOpenGL``, ``libGL`` -- the first that exports
       ``glXCreateContext``
   * - EGL
     - ``libEGL``
   * - GLU
     - ``libGLU``
   * - GLUT
     - ``libglut``
   * - GLE
     - ``libgle``
   * - GLES 1
     - ``libGLESv1_CM``
   * - GLES 2 and 3
     - ``libGLESv2``, for both, which is what the implementer's guide asks for

``libOpenGL`` before ``libGL`` is the libglvnd split: on a glvnd system
``libGL`` is the compatibility name that also carries GLX, and ``libOpenGL`` is
the vendor-neutral dispatch library for GL itself.

Everything is loaded with ``RTLD_GLOBAL``, because GLUT resolves its own
references to GL and GLU against what is already loaded in the process.  A
library that is missing is ``None`` rather than an error, so a system with no
GLU and no GLUT imports and runs; calling an entry point from a library that is
not there raises ``NullFunctionError`` naming the function.

Installing the libraries
------------------------

The GL library comes with the graphics driver.  The rest are packages:

.. code-block:: console

   $ sudo apt install freeglut3-dev libgle3-dev libglu1-mesa-dev     # Debian, Ubuntu
   $ sudo dnf install freeglut-devel libGLU-devel                    # Fedora

A container or build image usually has none of them, and often no GL either.

Two GPUs in one machine
-----------------------

A laptop with integrated and discrete graphics has two drivers installed, and
which one a context lands on is chosen per process or per context:
``DRI_PRIME=1`` or ``__NV_PRIME_RENDER_OFFLOAD=1`` in the environment, or an
EGL device named explicitly (:ref:`offscreen-egl`).  A server with several
cards is the same situation.

Two contexts on two drivers are not interchangeable.  They report different
extensions, different limits and different versions, and an entry point that
exists in one may be absent in the other -- so which context is current decides
what a call means.

PyOpenGL keeps a resolved entry point per context for that reason, and it has
to be told when the program changes which context is current:

::

   from OpenGL import dispatch, platform

   toolkit.make_current(window)             # whatever the toolkit calls it
   dispatch.make_current(platform.PLATFORM.GetCurrentContext())

``dispatch.forget_context(handle)`` says a context has been destroyed, so its
table is retired rather than left for whichever context the driver gives that
address to next.  Neither call is required -- PyOpenGL re-reads the current
context when it has to resolve something, and that covers a program whose
contexts have the same capabilities.  On a machine whose contexts differ, both
notifications are what keeps dispatch on the right table.  :doc:`c-dispatch`
has the detail, including what the tables cost and what an unannounced switch
looks like when it goes wrong.

A widget toolkit inside PyOpenGL does this itself: :doc:`tk-widget` says so for
``OpenGL.Tk``, where a program calls neither.

Software rendering
------------------

Mesa's ``llvmpipe`` rasterises on the CPU.  A machine with no GPU, or no
access to one, renders through it.  ``LIBGL_ALWAYS_SOFTWARE=1`` in the
environment demands it, and most distributions install it alongside the
hardware drivers.

Demanding software while asking for a hardware device is a contradiction Mesa
crashes on rather than refuses, which is why :py:mod:`OpenGL.EGL.devices`
reports which devices rasterise on the CPU.  :ref:`offscreen-egl` has the rule
and a worked example.

``PYOPENGL_PLATFORM=osmesa`` is a different software route: OSMesa is not a
driver behind GLX or EGL but an interface of its own, needing no display server
and no device node.  See :ref:`offscreen-osmesa`.

Rendering with no display server
--------------------------------

:doc:`offscreen` covers this in full.  In short, on Linux:

- :ref:`EGL device enumeration <offscreen-egl>` picks a GPU by name and renders
  on it, with no X server and no compositor.
- :py:mod:`OpenGL.EGL.gbmdevice` opens a DRM render node where that
  enumeration answers with nothing.
- :ref:`OSMesa <offscreen-osmesa>` rasterises into an array the caller owns,
  needing neither.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM`` overrides what PyOpenGL selects, and has to be set before
``OpenGL`` is imported.  On Linux the values that mean anything are:

``linux``, ``glx``, ``egl``, ``x11``, ``wayland``, ``xwayland``, ``posix``
    All the same implementation, the one described above.  Setting one of them
    changes nothing about which interface serves a context, since that is
    decided per context; it is useful where the automatic selection picks
    something else entirely.
``osmesa``
    Mesa's off-screen interface, which is a different library and a different
    set of entry points.  See :ref:`offscreen-osmesa`.

A value naming no plugin, or one whose import fails, raises ``ImportError``
naming the plugin and the variable; the reason goes to the ``OpenGL.plugins``
logger.
