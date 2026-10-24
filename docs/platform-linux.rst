OpenGL on Linux
===============

Linux provides OpenGL through two interfaces, GLX and EGL, and a machine
usually has both.  PyOpenGL loads whichever are installed and detects which
one created the current context.  A program does not have to name the
interface, and the common cases need no configuration.

BSD systems use the same code path.

GLX, EGL, X11 and Wayland
-------------------------

GLX is part of the X protocol.  A GLX context belongs to an X display and an X
drawable.  X11 programs have used GLX for OpenGL since 1992.

EGL is an interface to the same drivers that does not depend on a window
system.  Wayland clients use EGL, because Wayland has no GLX.  EGL is also the
interface on Android, and it can render with no display server at all (see
:ref:`offscreen-egl`).

A Wayland session runs XWayland so that X11 programs keep working.  An X11
program under XWayland gets a GLX context, as it would on an X server.  GLUT
programs usually run this way.  freeglut has a Wayland backend, but
distributions ship X11 builds, so a GLUT program on a Wayland desktop is an
XWayland client with a GLX context.

Which interface a context came from
-----------------------------------

The environment does not show which interface created a context.  GLUT under
XWayland creates a GLX context while ``WAYLAND_DISPLAY`` is set.  GLFW creates
either kind on either session type, depending on how it was built and what the
program requested.  The toolkit makes the choice, and PyOpenGL is not told
which.

GLX and EGL each keep their own per-thread current-context state.  PyOpenGL
loads both where both exist and checks each for a current context.  An entry
point is resolved through the interface that has a current context.  The check
runs when an entry point is resolved, not at import, so a program that creates
its context after importing ``OpenGL`` gets the right interface.

A name with an interface prefix always goes to that interface.  ``glX*`` names
resolve through ``glXGetProcAddressARB`` and ``egl*`` names through
``eglGetProcAddress``.  A core ``gl*`` name follows the current context, and
falls back to GLX when no context is current.

The prefix rule keeps ``egl*`` names away from GLX.  Under libglvnd,
``glXGetProcAddressARB`` returns a dispatch stub for *any* name, including an
``egl*`` one.  Calling the stub raises no error, but it is not the real entry
point.  An EGL client extension resolved this way returns failure with
``EGL_SUCCESS`` set.  The device-enumeration functions in
:ref:`offscreen-egl` are called before any context exists, so the prefix is
the only information available for routing them.

Because of the same stub, PyOpenGL cannot report on Linux whether the driver
has a given entry point: every lookup returns a pointer.  :doc:`c-dispatch`
lists the platforms where that report is possible.

Finding the libraries
---------------------

Each library is loaded the first time something needs it.  The requested name
(``GL``, ``GLU``, ``glut``) becomes ``lib<name>.so``, which is passed directly
to ``dlopen`` instead of to ``ctypes.util.find_library``.
``LD_LIBRARY_PATH``, the linker cache and ``LD_PRELOAD`` therefore all apply.
Use them to point a program at a particular driver stack.

``lib<name>.so`` is the development symlink, and most distributions ship it
only in the ``-dev`` package.  If it is absent, PyOpenGL tries the versioned
names from highest to lowest: ``lib<name>.so.9`` down to ``lib<name>.so.0``.
A machine with ``libGLU.so.1`` and no ``libGLU.so`` therefore loads GLU.

The names tried, in order:

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
     - ``libGLX``, ``libOpenGL``, ``libGL``: the first that exports
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
     - ``libGLESv2``, for both, as the implementer's guide specifies

``libOpenGL`` comes before ``libGL`` because of the libglvnd split.  On a
glvnd system, ``libGL`` is the compatibility library that also contains GLX,
and ``libOpenGL`` is the vendor-neutral dispatch library for GL alone.

Every library is loaded with ``RTLD_GLOBAL``, because GLUT resolves its own
references to GL and GLU against libraries already loaded in the process.  A
missing library is ``None`` instead of an error, so a system with no GLU and
no GLUT can still import and run PyOpenGL.  Calling an entry point from a
missing library raises ``NullFunctionError`` naming the function.

Installing the libraries
------------------------

The GL library comes with the graphics driver.  The others are packages:

.. code-block:: console

   $ sudo apt install freeglut3-dev libgle3-dev libglu1-mesa-dev     # Debian, Ubuntu
   $ sudo dnf install freeglut-devel libGLU-devel                    # Fedora

A container or build image usually has none of them, and often no GL either.

Two GPUs in one machine
-----------------------

A laptop with integrated and discrete graphics has two drivers installed.  The
driver a context uses is chosen per process or per context:
``DRI_PRIME=1`` or ``__NV_PRIME_RENDER_OFFLOAD=1`` in the environment, or an
EGL device named explicitly (:ref:`offscreen-egl`).  A server with several
cards works the same way.

Contexts on two different drivers are not interchangeable.  They report
different extensions, limits and versions, and an entry point present in one
may be missing from the other.  The result of a call therefore depends on
which context is current.

PyOpenGL keeps a separate table of resolved entry points for each context.  A
program tells PyOpenGL when it changes the current context:

::

   from OpenGL import dispatch, platform

   toolkit.make_current(window)             # whatever the toolkit calls it
   dispatch.make_current(platform.PLATFORM.GetCurrentContext())

``dispatch.forget_context(handle)`` tells PyOpenGL a context was destroyed.
PyOpenGL then retires its table, so a later context that the driver gives the
same address does not reuse it.  Neither call is required.  PyOpenGL re-reads
the current context whenever it resolves an entry point, which is enough when
all of a program's contexts have the same capabilities.  When contexts differ,
both calls keep dispatch on the right table.  :doc:`c-dispatch` has the
details, including the cost of the tables and the symptoms of an unreported
switch.

PyOpenGL's own widget toolkit makes these calls itself.  :doc:`tk-widget`
documents this for ``OpenGL.Tk``, where a program calls neither.

Software rendering
------------------

Mesa's ``llvmpipe`` rasterises on the CPU.  A machine with no GPU, or no
access to one, renders through it.  ``LIBGL_ALWAYS_SOFTWARE=1`` in the
environment forces it.  Most distributions install it alongside the hardware
drivers.

Setting ``LIBGL_ALWAYS_SOFTWARE`` while requesting a hardware device makes
Mesa crash instead of returning an error.  :py:mod:`OpenGL.EGL.devices`
therefore reports which devices rasterise on the CPU.  :ref:`offscreen-egl`
has the rule and a worked example.

``PYOPENGL_PLATFORM=osmesa`` is a separate software route.  OSMesa is its own
interface, not a driver behind GLX or EGL, and it needs no display server and
no device node.  See :ref:`offscreen-osmesa`.

Rendering with no display server
--------------------------------

:doc:`offscreen` covers this in full.  The Linux options are:

- :ref:`EGL device enumeration <offscreen-egl>` selects a GPU by name and
  renders on it, with no X server and no compositor.
- :py:mod:`OpenGL.EGL.gbmdevice` opens a DRM render node when device
  enumeration returns no devices.
- :ref:`OSMesa <offscreen-osmesa>` rasterises into an array the caller owns,
  and needs neither an X server nor a compositor.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM`` overrides the platform PyOpenGL selects, and must be set
before ``OpenGL`` is imported.  The values that have an effect on Linux are:

``linux``, ``glx``, ``egl``, ``x11``, ``wayland``, ``xwayland``, ``posix``
    All select the same implementation, described above.  None of them
    changes which interface serves a context, because that is decided per
    context.  Set one when automatic selection picks a different platform
    entirely.
``osmesa``
    Mesa's off-screen interface, which uses a different library and a
    different set of entry points.  See :ref:`offscreen-osmesa`.

A value that names no plugin is ignored, and PyOpenGL selects the platform as
it would with the variable unset.  If a plugin's import fails, PyOpenGL raises
``ImportError`` naming the plugin and the variable, and logs the reason to the
``OpenGL.plugins`` logger.  :doc:`development` lists the full order in which
sources are checked.
