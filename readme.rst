PyOpenGL and PyOpenGL_Accelerate
=================================

PyOpenGL is normally distributed via PyPI using standard pip::

    $ pip install PyOpenGL PyOpenGL_accelerate

The two packages carry the same version number, and the versions must match.
They are released together and share the dispatch extension's generated tables.
A mismatched pair dispatches calls through the wrong slot indices, so
``PyOpenGL_accelerate`` requires the *exact* ``PyOpenGL`` it was released with.
Installing or upgrading accelerate also installs the matching PyOpenGL.
Upgrading ``PyOpenGL`` on its own leaves the older accelerate in place.  pip
reports that as a conflict only after installing, and other installers may not
report it at all.  Name both packages whenever you upgrade either::

    $ pip install -U PyOpenGL PyOpenGL_accelerate

PyOpenGL detects a mismatched pair when it builds the first entry point, and
raises an error naming both versions.  Until the versions match,
``PYOPENGL_USE_ACCELERATE=0`` in the environment makes PyOpenGL use ctypes.

`RELEASE-NOTES-4.0.md <RELEASE-NOTES-4.0.md>`_ covers what changed between the
3.x series and 4.0, including the requirements a 3.x program has to meet.

To install from a clone of this repository, run ``pip``::

    $ cd pyopengl
    $ pip install -e . ./accelerate

Install both packages in one command, because their versions must match.
Between releases, the version in this tree is not on any package index.
Installing accelerate on its own asks PyPI for that version, and the resolver
fails.  Installing both from the checkout in one command resolves each against
the other.

Compiling PyOpenGL_accelerate needs a working Python extension-building
environment.

Freezing an application
------------------------

PyOpenGL chooses its platform module and its array format handlers through a
plug-in registry (``OpenGL.plugins``). The registry names each module as a
string and imports it when it matches. A freezing tool that follows import
statements does not find these modules. The frozen application then cannot
load any platform.

PyOpenGL ships its own PyInstaller hook to include them. PyInstaller finds the
hook through the ``pyinstaller40`` entry point, with no configuration. The hook
lists the modules the registries would import, read from the registries
themselves, so plug-ins added by other packages are included too. On Windows it
also lists the GLUT and GLE libraries, which ``OpenGL.platform.ctypesloader``
opens by path. Those libraries come from ``PyOpenGL-glut-binaries``. A frozen
application includes them if the build host installed ``PyOpenGL[glut]``, and
is frozen without GLUT otherwise.

For another freezer, ``OpenGL.plugins.registered_modules()`` returns the same
module list without PyInstaller::

    >>> from OpenGL import plugins
    >>> plugins.registered_modules('OpenGL')
    ['OpenGL.arrays.buffers', 'OpenGL.arrays.ctypesarrays', ...]

Learning PyOpenGL
-----------------

If you are new to PyOpenGL, start with the OpenGLContext `tutorial page`_.
The tutorials require OpenGLContext, a large package with a scenegraph engine,
a VRML97 parser and many demos.  Install it with::

    $ pip install OpenGLContext

Or you can clone it (including the tutorial sources) with::

    $ git clone https://github.com/mcfletch/openglcontext.git

or (for GitHub usage)::

    $ git clone https://github.com/mcfletch/pyopengl.git
    
The `documentation pages`_ are useful for looking up the parameters and semantics of 
PyOpenGL calls.

.. _`tutorial page`: http://pyopengl.sourceforge.net/context/tutorials/index.html
.. _`documentation pages`: https://mcfletch.github.io/pyopengl/index.html


Choosing a dispatch implementation
-----------------------------------

PyOpenGL has two implementations of the OpenGL entry points.  The C
implementation is generated from the Khronos registry.  It calls the driver
roughly seven times faster per call, and eleven times faster for a call that
passes an array.  The gain for a program depends on how much of each frame is
spent in dispatch.  A program built around shaders and buffer objects makes few
calls per frame.  On optimised PyOpenGL applications the measured gain is about
5%.  The C implementation is compiled, so it ships in ``PyOpenGL_accelerate``::

    $ pip install PyOpenGL PyOpenGL_accelerate

``pip install PyOpenGL`` on its own gives the ctypes implementation, which is
pure Python and needs no compiler.  The extension is built for CPython only.
The C implementation runs under CPython with ``PyOpenGL_accelerate`` installed.
ctypes runs everywhere else.  Where the C implementation is available, select
ctypes with::

    $ PYOPENGL_DISPATCH=ctypes python yourprogram.py

Both implement the same API, and the test suite runs under both.  Requesting
the C implementation where it was not built is not an error.  PyOpenGL keeps
using ctypes.  A program that requires the C implementation checks
``dispatch.status()``::

    >>> from OpenGL import dispatch
    >>> dispatch.status()
    Status(requested='c', active='c', available=True, reason=None)

A program also calls ``OpenGL.dispatch`` to report that a context has become
current or been destroyed.  Those calls give each context its own function
pointer for every entry point.  See `the C dispatch layer`_ for what it covers,
how it differs from ctypes, and how to report a change of current context.

.. _`the C dispatch layer`: https://mcfletch.github.io/pyopengl/c-dispatch.html


Rendering without a display server
-----------------------------------

``OpenGL.EGL.devices`` lists the EGL devices a system offers, and which of
them rasterise on the CPU.  A program uses that list to choose a device for
offscreen rendering::

    from OpenGL.EGL import devices

    for device in devices.devices():
        print(device.index, device.driver, device.software)

See `EGL devices`_ for what each field means, how a device is classed as
software, and the ``eglGetPlatformDisplayEXT`` call that a device handle is
passed to.

.. _`EGL devices`: https://mcfletch.github.io/pyopengl/egl-devices.html

On macOS the equivalent is ``OpenGL.CGL``.  CGL is the lowest-level OpenGL
interface on macOS.  NSGL (the ``NSOpenGLContext`` Cocoa classes) and AGL (the
older Carbon interface) are built on it.  Of the three, only CGL can create a
context with no window and no window server::

    from OpenGL.CGL import OffscreenTarget, headless_context

    with headless_context(profile='core3'):
        target = OffscreenTarget(256, 256)
        ...                      # there is no framebuffer zero; draw into this
        target.release()

An offscreen CGL context has no default framebuffer (framebuffer zero), so
rendering must target a framebuffer object.  See `Offscreen OpenGL on macOS`_
for the available profiles, how the renderer is chosen on a machine without an
accelerated one, and the framebuffer object requirement.

.. _`Offscreen OpenGL on macOS`: https://mcfletch.github.io/pyopengl/cgl-offscreen.html


OpenGL ES through ANGLE
------------------------

Windows has no EGL and no OpenGL ES of its own.  ANGLE supplies both by
translating ES calls to Direct3D 11.  ``PYOPENGL_PLATFORM=angle`` makes
PyOpenGL bind to ANGLE::

    PYOPENGL_PLATFORM=angle
    PYOPENGL_ANGLE_PATH=C:\path\to\angle     # holding libEGL.dll, libGLESv2.dll

With those set, ``OpenGL.EGL`` and ``OpenGL.GLES2`` work as they do on Linux:
pick a config, make a pbuffer current, and render with no window::

    from OpenGL.EGL import eglGetDisplay, eglInitialize, eglBindAPI, ...
    from OpenGL.GLES2 import glClear, glClearColor, glReadPixels

PyOpenGL uses the ANGLE platform only when ``PYOPENGL_PLATFORM`` requests it.
Otherwise a Windows program uses WGL and gets desktop GL from the driver.

ANGLE supplies OpenGL ES only, with no desktop GL.  It advertises
``EGL_CLIENT_APIS`` of ``OpenGL_ES``, offers no config with
``EGL_OPENGL_BIT``, and rejects ``eglBindAPI(EGL_OPENGL_API)``.  On this
platform ``GL`` is therefore ``None``.  ``OpenGL.GL`` still imports, and
calling a desktop-only entry point raises ``NullFunctionError`` naming that
entry point.  ES 1, 2 and 3 all come from ``libGLESv2.dll``, including ANGLE's
ES 1 emulation.

ANGLE is not installed system-wide.  Browsers and Electron applications each
bundle their own copy, so a machine may hold several copies of different ages.
``PYOPENGL_ANGLE_PATH`` names the copy to use.  Without it, the ordinary
library search runs, which finds ANGLE only if it is on ``PATH``.

See `OpenGL ES through ANGLE`_ for what a context can be asked for and what the
platform does and does not supply.

.. _`OpenGL ES through ANGLE`: https://mcfletch.github.io/pyopengl/angle-gles.html


OpenGL in a Tkinter window
---------------------------

``OpenGL.Tk.GLFrame`` is an ordinary ``tkinter.Frame`` that owns an OpenGL
context on its own native window.  Tkinter ships with Python, so it is the one
GUI toolkit that needs nothing extra installed.  The context is a core profile
by default, so a Tk application can use shaders and vertex array objects::

    import tkinter
    from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor
    from OpenGL.Tk import GLFrame

    class Scene(GLFrame):
        def initgl(self):              # once, with the context current
            glClearColor(0.2, 0.3, 0.3, 1.0)
        def redraw(self):              # per frame
            glClear(GL_COLOR_BUFFER_BIT)

    root = tkinter.Tk()
    Scene(root, width=640, height=480).pack(fill='both', expand=True)
    root.mainloop()

``examples/tk_shader.py`` is a longer example.  See
`OpenGL in a Tkinter widget`_ for the context options, when the context is
created, what happens when a driver rejects a request, and which of the older
widgets still need Togl (``RawOpengl`` and ``Opengl`` do not; ``Togl`` does).

.. _`OpenGL in a Tkinter widget`: https://mcfletch.github.io/pyopengl/tk-widget.html


Running Tests
--------------

You can run the PyOpenGL test suite from a source-code checkout.  The easiest
way is with the uv runner, which needs:


* git (for the checkout)
* GLUT (FreeGLUT)
* GLExtrusion library (libgle)
* GLU (normally available on any OpenGL-capable machine)
* [uv](https://docs.astral.sh/uv/)

Running the test suite from a top-level checkout looks like::

    $ uv run --with tox,tox-uv tox

This runs the tests in a matrix of environments.  Every environment installs
glfw.  Some also install numpy, and some install accelerate.

Test Suite Concerns
....................

The test suite takes a long time because it covers a matrix of supported
configurations.  It opens *many* windows, so using the keyboard while it runs
is difficult.

On a powerful Linux machine, with all dependencies already cached by uv, a
single test run takes around 90s (for running the tests alone).  The matrix
has 7 CPython and 2 PyPy versions, 2 numpy conditions and 2 acceleration
conditions.  The
full tox suite takes around 40 minutes with all dependencies built and cached.

tox's -p flag runs test suites in parallel, but it can crash your desktop.

The glfw windows usually stall if your Wayland session is locked or otherwise
not displaying windows.

With `TEST_VISIBLE=false` in your environment, many tests run "headless"
(without an on-screen window)::

    $ TEST_VISIBLE=false uv run --with tox,tox-uv tox

Some tests ignore this flag, mostly the test_checks.py suite, which runs
scripts out of process.  The tests that honour it run much faster and do not
take over the desktop.

The environment variable TEST_DWELL sets the pause between tests (the dwell
time) as a floating point value.  On a run without visible windows a long dwell
has no use, because the rendered frames are not shown.

Many test cases can use the pygame context::

    $ TEST_WINDOWING=pygame uv run --with tox,tox-uv tox

pygame versions for Python 3.9 often do not support Wayland desktops.

The ``TEST_WINDOWING`` flag selects the windowing backend used by the
``tests/gl``, ``tests/gles`` and ``tests/glu`` suites:

* ``glfw`` (the default) and ``pygame`` create an on-screen window.  On a
  desktop they render on your GPU.  Inside a container with a
  software-rendered compositor they use llvmpipe (Mesa's CPU rasteriser),
  whatever GPU is present.
* ``cgl`` is the *headless* backend on macOS: a CGL context with no window and
  no window server.  CI runners and remote shells on macOS can only create this
  kind of context.  ``TEST_CGL_RENDERER`` pins the renderer kind
  (``accelerated`` / ``any`` / ``software``).  When it is unset, an accelerated
  renderer is preferred, and the CPU renderer is used when there is no other.
  macOS has no OpenGL-ES and no compatibility profile above 2.1, so cases that
  need either are skipped with that reason.  ``python
  tests/check_cgl_context.py`` reports what contexts a given Mac supports::

      $ TEST_WINDOWING=cgl uv run --with tox,tox-uv tox

* ``egl`` is a *headless* backend that renders directly on a GPU through the
  ``EGL_EXT_platform_device`` extension, with no window system at all::

      $ TEST_WINDOWING=egl uv run --with tox,tox-uv tox

  Use it for CI and containers (for example with the NVIDIA container
  runtime).  There it reaches the real GPU, where the on-screen path would use
  llvmpipe.  It forces ``PYOPENGL_PLATFORM=egl`` and provides both desktop
  OpenGL and OpenGL-ES contexts through an offscreen pbuffer.  There is no
  window, so ``TEST_VISIBLE`` and the inter-test dwell do not apply.  By
  default it picks the first non-software EGL device.
  ``LIBGL_ALWAYS_SOFTWARE=1`` (or ``GALLIUM_DRIVER=llvmpipe``) selects the
  software device instead, and ``TEST_EGL_DEVICE=<n>`` pins a device index.
  The two settings must agree.  Mesa crashes when asked to force software
  rasterisation on a display created from a hardware device.  A run that
  requests software and pins a GPU is therefore refused with an error that
  names the conflict.  The legacy root-level ``tests/*.py`` have no headless equivalent
  and use a windowed backend under this setting.  They need a display server
  for their windows and are skipped where there is none.  To run them, use a
  virtual display server::

      $ xvfb-run -a uv run --with tox,tox-uv tox

Continuous integration
~~~~~~~~~~~~~~~~~~~~~~

Every push to ``develop`` runs the suite against two independent OpenGL
implementations.  Both runners are free for a public repository:

* Mesa's llvmpipe on a Linux runner, run headless through the EGL device
  platform.  There is no X server and no GPU, and every run uses the same
  renderer.  The jobs cover Python 3.10 to 3.14, both dispatch
  implementations, with and without numpy, and with and without
  ``PyOpenGL_accelerate``.  Each job runs one tox environment, so a failing
  job identifies the configuration that failed.
* Apple's GL on the ``macos-14`` and ``macos-15`` runners, through ``CGL``.
  Mesa accepts some incorrect calls that Apple's implementation rejects, so
  this job catches errors the llvmpipe job misses.  These runners have no
  accelerated renderer, so the tests run on Apple's CPU renderer.

GitHub's GPU runner is a larger runner.  It is billed per minute on Team and
Enterprise plans and is never free, whatever the repository's visibility, so
neither job uses it.

Reproduce the Linux job on a machine that has a GPU with::

    $ LIBGL_ALWAYS_SOFTWARE=1 TEST_WINDOWING=egl python -m pytest tests/

Tests with the ``performance`` marker assert drawing speed, which a CPU
rasteriser cannot measure meaningfully.  The Linux job deselects them with
``-m "not performance"``.

.. image:: https://img.shields.io/pypi/v/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Latest PyPI Version

.. image:: https://img.shields.io/pypi/dm/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Monthly download counter
