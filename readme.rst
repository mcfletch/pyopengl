PyOpenGL and PyOpenGL_Accelerate
=================================

PyOpenGL is normally distributed via PyPI using standard pip::

    $ pip install PyOpenGL PyOpenGL_accelerate

`RELEASE-NOTES-4.0.md <RELEASE-NOTES-4.0.md>`_ covers what changed between the
3.x series and 4.0, including the requirements a 3.x program has to meet.

You can install this repository by branching/cloning and running
``pip``::

    $ cd pyopengl
    $ pip install -e . ./accelerate

Both at once, because ``PyOpenGL_accelerate`` requires the *exact* PyOpenGL it
pairs with: the two are released together and its dispatch extension's tables
are generated from that PyOpenGL, so a mismatched pair does not degrade, it
dispatches through the wrong slot indices.  Between releases that version is in
this tree and on no index, so installing accelerate on its own asks PyPI for a
version that is not there yet and the resolver refuses.  Installing both from
the checkout in one command resolves them against each other.

Note that to compile PyOpenGL_accelerate you will need to have 
a functioning Python extension-compiling environment.

Freezing an application
------------------------

PyOpenGL chooses its platform module and its array format handlers through a
plug-in registry (``OpenGL.plugins``), which names each one as a string and
imports it when something matches. A tool that follows import statements sees
none of them, and freezes an application that cannot load a platform at all.

PyOpenGL therefore ships its own PyInstaller hook, which PyInstaller finds by
itself through the ``pyinstaller40`` entry point: there is nothing to configure
and nothing to list. It reports the modules the registries would import --
read from the registries themselves, so a plug-in added by another package is
carried too -- and on Windows the GLUT and GLE DLLs, which
``OpenGL.platform.ctypesloader`` opens by path.

For another freezer, ``OpenGL.plugins.registered_modules()`` is the same answer
without PyInstaller in the way::

    >>> from OpenGL import plugins
    >>> plugins.registered_modules('OpenGL')
    ['OpenGL.arrays.buffers', 'OpenGL.arrays.ctypesarrays', ...]

Learning PyOpenGL
-----------------

If you are new to PyOpenGL, you likely want to start with the OpenGLContext `tutorial page`_.
Those tutorials require OpenGLContext, (which is a big wrapper including a whole
scenegraph engine, VRML97 parser, lots of demos, etc) you can install that with::

    $ pip2.7 install "OpenGLContext-full==3.1.1"

Or you can clone it (including the tutorial sources) with::

    $ git clone https://github.com/mcfletch/openglcontext.git

or (for GitHub usage)::

    $ git clone https://github.com/mcfletch/pyopengl.git
    
The `documentation pages`_ are useful for looking up the parameters and semantics of 
PyOpenGL calls.

.. _`tutorial page`: http://pyopengl.sourceforge.net/context/tutorials/index.html
.. _`documentation pages`: https://mcfletch.github.io/pyopengl/documentation/index.html


Choosing a dispatch implementation
-----------------------------------

PyOpenGL has two implementations of the OpenGL entry points.  The C
implementation is generated from the Khronos registry and reaches the driver
roughly seven times faster per call -- eleven times for a call that passes an
array.  What a program gains from that depends on how much of its frame goes on
dispatch: one structured around shaders and buffer objects makes few calls per
frame, and the measured uplift on optimised PyOpenGL applications is about 5%.
Being compiled, the C implementation ships in ``PyOpenGL_accelerate``::

    $ pip install PyOpenGL PyOpenGL_accelerate

``pip install PyOpenGL`` on its own gives the ctypes implementation, which is
pure Python and needs nothing compiled.  The extension is built for CPython
only, so the C implementation runs where ``PyOpenGL_accelerate`` is installed
under CPython, and ctypes runs everywhere else.  Where the C implementation is
available, ctypes is selected with::

    $ PYOPENGL_DISPATCH=ctypes python yourprogram.py

Both implement the same API and the test suite runs under both.  Asking for the
C implementation where none was built is not an error -- the ctypes one stays in
place -- so a program that means to be on it asks::

    >>> from OpenGL import dispatch
    >>> dispatch.status()
    Status(requested='c', active='c', available=True, reason=None)

``OpenGL.dispatch`` is also where a program says a context has become current or
been destroyed, which is what gives each context its own function pointer for
every entry point.  See `the C dispatch layer`_ for what it covers, what
differs, and how to tell it that the current context changed.

.. _`the C dispatch layer`: https://mcfletch.github.io/pyopengl/documentation/c-dispatch.html


Rendering without a display server
-----------------------------------

``OpenGL.EGL.devices`` reports which EGL devices a system offers and which of
them rasterise on the CPU, which is what a program needs before it can render
offscreen on a named device::

    from OpenGL.EGL import devices

    for device in devices.devices():
        print(device.index, device.driver, device.software)

See `EGL devices`_ for what each field means, how the software question is
decided, and the ``eglGetPlatformDisplayEXT`` call a handle is for.

.. _`EGL devices`: https://mcfletch.github.io/pyopengl/documentation/egl-devices.html

On macOS the equivalent is ``OpenGL.CGL``, which creates a context with no
window and no window server -- CGL is the layer NSGL and AGL are built on, and
the only one of the three that will::

    from OpenGL.CGL import OffscreenTarget, headless_context

    with headless_context(profile='core3'):
        target = OffscreenTarget(256, 256)
        ...                      # there is no framebuffer zero; draw into this
        target.release()

See `Offscreen OpenGL on macOS`_ for the profiles available, how the renderer is
chosen on a machine with no accelerated one, and why a framebuffer object is not
optional there.

.. _`Offscreen OpenGL on macOS`: https://mcfletch.github.io/pyopengl/documentation/cgl-offscreen.html


OpenGL in a Tkinter window
---------------------------

``OpenGL.Tk.GLFrame`` is an ordinary ``tkinter.Frame`` that owns an OpenGL
context on its own native window.  Tkinter ships with Python, so this is the
one GUI toolkit that needs nothing installed, and the context is a core profile
by default -- shaders and vertex array objects, in a Tk application::

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

``examples/tk_shader.py`` is a longer one.  See `OpenGL in a Tkinter widget`_
for what the context can be asked for, when it arrives, what happens when a
driver refuses one, and what became of the Togl-based widgets (they keep their
names and no longer need Togl).

.. _`OpenGL in a Tkinter widget`: https://mcfletch.github.io/pyopengl/documentation/tk-widget.html


Running Tests
--------------

You can run the PyOpenGL test suite from a source-code checkout, the easiest
way to run the tests with the uv runner:


* git (for the checkout)
* GLUT (FreeGLUT)
* GLExtrusion library (libgle)
* GLU (normally available on any OpenGL-capable machine)
* [uv](https://docs.astral.sh/uv/)

Running the test suite from a top-level checkout looks like::

    $ uv run --with tox,tox-uv tox

The result being a lot of tests being run in a matrix of environments.
All of the environments will pull in glfw, some will also pull in 
numpy. Some will have accelerate, and some will not.

Test Suite Concerns
....................

The test suite takes a long time to complete due to the matrix of 
supported configurations; it will open *many* windows, so it will be
difficult to interact with your machine's keyboard as it runs.

On a powerful linux machine a single test run when uv has already cached 
all dependencies is around 90s (i.e. just for actually running the tests).
There is a matrix of 6 python versions, 2 numpy conditions, and 2 
acceleration conditions for around 40 minutes to run the full tox suite
if you already have all dependencies built and cached.

You can run parallel test suites with tox's -p flag, but beware that
you can crash your desktop that way.

The glfw window generally will not proceed if your Wayland session
has locked or is otherwise preventing display of the windows.

You can set `TEST_VISIBLE=false` in your environment and many of the
tests will run "headless" (i.e. will not create an on-screen display)::

    $ TEST_VISIBLE=false uv run --with tox,tox-uv tox

there are, however, a number of tests which do not respect this flag
(mostly the test_checks.py suite which runs out-of-process scripts),
for those which do the speedup and ergonimic improvement is considerable.

You can control the inter-test pause (dwell time) by setting the 
environment variable TEST_DWELL to a floating point value. Note that
there is no point having a long dwell on non-visible runs, since the
rendered frames will not be visible to you anyway.

You can use the pygame context for many test cases, to do so::

    $ TEST_WINDOWING=pygame uv run --with tox,tox-uv tox

Keep in mind that pygame versions for python3.9 often do not support
Wayland desktops.

The ``TEST_WINDOWING`` flag selects the windowing backend used by the
``tests/gl``, ``tests/gles`` and ``tests/glu`` suites:

* ``glfw`` (the default) and ``pygame`` create an on-screen window.  On a
  desktop these render on your GPU; inside a container whose compositor is
  software-rendered they will use llvmpipe regardless of the GPU present.
* ``cgl`` is the *headless* backend on macOS: a CGL context with no window and
  no window server, which is the only kind those runners and remote shells can
  have.  ``TEST_CGL_RENDERER`` pins the renderer kind (``accelerated`` /
  ``any`` / ``software``); unset, an accelerated renderer is preferred and the
  CPU one taken where there is no other.  OpenGL-ES and a compatibility profile
  above 2.1 do not exist there, so cases wanting either are skipped with the
  reason.  ``python tests/check_cgl_context.py`` reports what a given Mac can
  give::

      $ TEST_WINDOWING=cgl uv run --with tox,tox-uv tox

* ``egl`` is a *headless* backend that renders directly on a GPU through the
  ``EGL_EXT_platform_device`` extension, with no window system at all::

      $ TEST_WINDOWING=egl uv run --with tox,tox-uv tox

  This is the right choice for CI / containers (e.g. with the NVIDIA container
  runtime), where it reaches the real GPU even though the on-screen path would
  fall back to llvmpipe.  It forces ``PYOPENGL_PLATFORM=egl`` and serves both
  desktop OpenGL and OpenGL-ES contexts via an offscreen pbuffer; because there
  is no window, ``TEST_VISIBLE`` and the inter-test dwell do not apply.  By
  default it picks the first non-software EGL device; ``LIBGL_ALWAYS_SOFTWARE=1``
  (or ``GALLIUM_DRIVER=llvmpipe``) asks for the software one instead, and
  ``TEST_EGL_DEVICE=<n>`` pins a device index.  The two have to agree: Mesa
  refuses to force software rasterisation onto a display built on a hardware
  device and crashes rather than saying no, so a run that demands software and
  pins a GPU is refused by name.  The legacy root-level ``tests/*.py`` have no
  headless equivalent and fall back to a windowed backend under this setting.
  They need a display server to open their window on, and skip where there is
  none; run them under a virtual one to have them run::

      $ xvfb-run -a uv run --with tox,tox-uv tox

Continuous integration
~~~~~~~~~~~~~~~~~~~~~~

Every push to ``develop`` runs the suite against two unrelated OpenGL
implementations, both free for a public repository:

* Mesa's llvmpipe on a Linux runner, reached headless through the EGL device
  platform -- no X server and no GPU, and the same renderer on every run.  The
  interpreters 3.10 to 3.14, both dispatch implementations, with and without
  numpy, and with and without ``PyOpenGL_accelerate``: one tox environment per
  job, so a failure names the axis it happened on.
* Apple's GL on the ``macos-14`` and ``macos-15`` runners, through ``CGL``.
  A second vendor's implementation is the half llvmpipe cannot cover: a call we
  get away with under Mesa because Mesa is lenient fails there.  Those runners
  have no accelerated renderer, so what answers is Apple's CPU one.

GitHub's GPU runner is not an option for either: it is a larger runner, billed
per minute on Team and Enterprise plans and never free, whatever the
repository's visibility.

Reproduce the Linux job on a machine that has a GPU with::

    $ LIBGL_ALWAYS_SOFTWARE=1 TEST_WINDOWING=egl python -m pytest tests/

Tests carrying the ``performance`` marker assert how fast something draws, which
a CPU rasteriser cannot answer, so that job deselects them with
``-m "not performance"``.

.. image:: https://travis-ci.org/mcfletch/pyopengl.svg?branch=master
    :target: https://travis-ci.org/mcfletch/pyopengl
    :alt: Travis Tests

.. image:: https://ci.appveyor.com/api/projects/status/github/mcfletch/pyopengl
    :target: https://ci.appveyor.com/project/MikeCFletcher/pyopengl
    :alt: Appveyor Build

.. image:: https://img.shields.io/pypi/v/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Latest PyPI Version

.. image:: https://img.shields.io/pypi/dm/pyopengl.svg
    :target: https://pypi.python.org/pypi/pyopengl
    :alt: Monthly download counter
