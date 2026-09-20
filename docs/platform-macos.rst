OpenGL on macOS
===============

macOS ships OpenGL as part of the system, in
``/System/Library/Frameworks/OpenGL.framework``, so PyOpenGL reaches it with
nothing installed.  One framework serves GL, GLU and CGL alike, and GLUT comes
from a second, ``GLUT.framework``, which is also part of the system.

Intel and Apple Silicon Macs both have it.

CGL and NSGL
------------

Two interfaces get a context on a current macOS, and PyOpenGL binds one of
them:

``CGL``
    Core OpenGL, the layer NSGL is built on.  It knows nothing about windows,
    and is the one that will create a context with no window server running.  :py:mod:`OpenGL.CGL` binds it: pixel formats, contexts, renderer
    queries and the offscreen path.
``NSGL``
    The Cocoa interface, reached through ``NSOpenGLContext``.  A Cocoa toolkit
    -- PyQt, PySide, wxPython, pygame -- makes its context through this, and
    PyOpenGL draws into whatever it made current.  PyOpenGL does not bind NSGL;
    the toolkit does.

Releasing a context works for both, because CGL is underneath: a context made
through NSGL is one ``OpenGL.platform.PLATFORM.releaseCurrentContext()`` can
give up, which is what lets a program hand the thread to a second GL binding.

What version Apple's OpenGL is
------------------------------

GL 4.1 core is as far as it goes, and there is no compatibility profile above
2.1: a context is legacy 2.1 with the fixed-function pipeline, or 3.2 core, or
4.1 core, and nothing in between.  :ref:`The profile table <offscreen-cgl>`
names them.

Apple deprecated OpenGL in macOS 10.14, and it has shipped in every release
since.  A program wanting more than 4.1 on a Mac is looking at Metal, or at
`MoltenVK <https://github.com/KhronosGroup/MoltenVK>`__ and Vulkan; PyOpenGL
binds neither.

Hardware and the software renderer
----------------------------------

A Mac with a usable GPU has an accelerated renderer.  A virtual machine, a
session with no window server, or a remote shell may have only Apple's CPU
renderer.  **Asking for acceleration there fails rather than falling back**, so
a library that requires ``kCGLPFAAccelerated`` gets no context at all on such a
machine.

``OpenGL.CGL.renderers()`` reports what a machine has.  It creates no context
and opens no window, so it answers where a context could not be made:

::

   from OpenGL.CGL import renderers

   for renderer in renderers():
       print(renderer)      # index, id, accelerated or software, GL version, VRAM

Each reports whether it is accelerated, whether it is *online* -- attached to a
display, a GPU with no display attached still being usable for rendering -- the
major GL version it serves, and how much video memory it has.  The software
renderer and the hardware on the same machine need not serve the same GL
version, so the version a program can compile shaders against is a question for
the renderer it actually got.

``choose_pixel_format`` tries ``accelerated``, then ``any``, then ``software``,
and returns the kind it settled on alongside the format.  ``renderer=`` pins
one kind and tries no other.

Rendering with no window
------------------------

:ref:`offscreen-cgl` is the route, and the only one here: macOS has no EGL, and
Apple's frameworks carry no OSMesa.  That section covers making the context,
building a framebuffer object to render into -- a windowless context has no
default framebuffer, so drawing to framebuffer zero silently goes nowhere --
and the renderer question above.

``python tests/report_cgl_context.py`` says whether a context can be made on a
given machine, and by which renderer, for each of the three profiles.  It is
the first thing to run when a suite skips every GL case on a Mac.

Apple Silicon and Intel
-----------------------

``PyOpenGL`` is a pure-Python wheel and installs on either.
``PyOpenGL_accelerate`` is compiled, and the published wheels are
``macosx_11_0_arm64``: an Apple Silicon interpreter installs a binary, and an
Intel Mac -- or an x86_64 interpreter running under Rosetta on an Apple Silicon
machine -- builds it from the source distribution, which needs the Xcode
command line tools (``xcode-select --install``).  PyOpenGL runs on ctypes
without accelerate.

An interpreter and the libraries it loads have to be the same architecture.
The system frameworks are universal and load into either, so desktop GL is
unaffected; a library you installed is the one to check.  Homebrew installs
under ``/opt/homebrew`` on Apple Silicon and ``/usr/local`` on Intel, and a
universal2 Python launched as x86_64 on an Apple Silicon machine looks for
x86_64 libraries in whichever of those it was told about.

Finding the libraries
---------------------

``ctypes.util.find_library`` is asked first, and where it answers, that is what
loads.  Where it comes up empty the bare name is tried, and then the framework
path is built explicitly:
``/System/Library/Frameworks/<name>.framework/<name>``.  That last step is what
makes ``OpenGL`` and ``GLUT`` load on a machine where ``find_library``'s
heuristics find nothing -- the dyld shared cache holds the frameworks rather
than the filesystem, so looking for the file does not find them.

A library outside the frameworks -- a Homebrew freeglut, say -- is found by
``find_library`` or by the dynamic loader's own search.
``/opt/homebrew/lib`` is not on that search path by default, so
``DYLD_FALLBACK_LIBRARY_PATH`` is how a Homebrew library is pointed at.

Getting a window
----------------

GLFW, pygame, PyQt, PySide and wxPython all create Mac windows with a GL
context.  GLUT is in the system frameworks, so ``OpenGL.GLUT`` works with
nothing installed -- though Apple's GLUT is the original implementation rather
than freeglut, and is as deprecated as the rest of the framework.
``OpenGL.Tk`` works with the system Tcl/Tk or a Homebrew one.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM=darwin`` selects this implementation explicitly, which is
what PyOpenGL selects here anyway.  There is no second choice on macOS:
``osmesa`` wants an OSMesa this system does not have, and ``angle`` loads
Windows DLLs.
