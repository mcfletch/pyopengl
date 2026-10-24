OpenGL on macOS
===============

macOS ships OpenGL as part of the system, in
``/System/Library/Frameworks/OpenGL.framework``, so PyOpenGL needs nothing
installed to use it.  That one framework provides GL, GLU and CGL.  GLUT comes
from a second system framework, ``GLUT.framework``.

Intel and Apple Silicon Macs both have OpenGL.

CGL and NSGL
------------

macOS has two interfaces for creating a context.  PyOpenGL binds one of them:

``CGL``
    Core OpenGL, the lowest-level OpenGL interface on macOS.  It has no window
    functions, and it can create a context with no window server running.
    :py:mod:`OpenGL.CGL` binds it: pixel formats, contexts, renderer queries
    and the offscreen path.  The test suite creates its macOS context with CGL.
``NSGL``
    The AppKit interface, built on CGL: `NSOpenGLContext
    <https://developer.apple.com/documentation/appkit/nsopenglcontext>`__ and
    ``NSOpenGLPixelFormat``.  Cocoa toolkits (PyQt, PySide, wxPython, pygame)
    create their contexts through NSGL, and PyOpenGL draws into whichever
    context the toolkit made current.  PyOpenGL does not bind NSGL.
    :doc:`OpenGL.Tk <tk-widget>` on Aqua creates an ``NSOpenGLContext`` and
    chooses its pixel format and profile with :py:mod:`OpenGL.CGL`.

``OpenGL.platform.PLATFORM.releaseCurrentContext()`` releases a context made
through either interface, because CGL is underneath both.  Releasing the
context lets a program pass the thread to a second GL binding.

What version Apple's OpenGL is
------------------------------

The highest version is GL 4.1 core.  There is no compatibility profile above
2.1.  A context is one of legacy 2.1 with the fixed-function pipeline, 3.2
core or 4.1 core.  :ref:`The profile table <offscreen-cgl>` lists them.

Apple deprecated OpenGL in macOS 10.14, and every release since has still
shipped it.  For more than GL 4.1 on a Mac, a program has to use Metal, or
Vulkan through `MoltenVK <https://github.com/KhronosGroup/MoltenVK>`__.
PyOpenGL binds neither.

Hardware and the software renderer
----------------------------------

A Mac with a usable GPU has an accelerated renderer.  A virtual machine, a
session with no window server, or a remote shell may have only Apple's CPU
renderer.  On such a machine a request for acceleration fails instead of
falling back, so a library that requires ``kCGLPFAAccelerated`` gets no
context at all.

``OpenGL.CGL.renderers()`` lists the renderers a machine has.  It creates no
context and opens no window, so it works on a machine where no context can be
made:

::

   from OpenGL.CGL import renderers

   for renderer in renderers():
       print(renderer)      # index, id, accelerated or software, GL version, VRAM

Each entry reports whether the renderer is accelerated, whether it is
*online*, the major GL version it supports, and how much video memory it has.
An online renderer is attached to a display.  A GPU with no display attached
can still render.  The software renderer and the hardware renderer on one
machine can support different GL versions, so a program should check the GL
version of the renderer it actually got before choosing a shader version.

``choose_pixel_format`` tries ``accelerated``, then ``any``, then ``software``,
and returns the kind it chose alongside the format.  ``renderer=`` selects one
kind and tries no other.

Rendering with no window
------------------------

:ref:`offscreen-cgl` is the only offscreen route on macOS.  macOS has no EGL,
and Apple's frameworks do not include OSMesa.  That section covers creating
the context, the renderer choice above, and building a framebuffer object to
render into.  A windowless context has no default framebuffer, so drawing to
framebuffer zero silently produces nothing.

``python tests/report_cgl_context.py`` reports whether a context can be made
on a given machine, and by which renderer, for each of the three profiles.
Run it first when a suite skips every GL case on a Mac.

Apple Silicon and Intel
-----------------------

``PyOpenGL`` is a pure-Python wheel and installs on either.
``PyOpenGL_accelerate`` is compiled, and the published wheels are
``macosx_11_0_arm64``.  An Apple Silicon interpreter installs the binary
wheel.  An Intel Mac, or an x86_64 interpreter running under Rosetta on Apple
Silicon, builds it from the source distribution.  That build needs the Xcode
command line tools (``xcode-select --install``).  PyOpenGL runs on ctypes
without accelerate.

An interpreter and the libraries it loads must have the same architecture.
The system frameworks are universal and load into either, so desktop GL always
loads.  Check the architecture of libraries you installed yourself.  Homebrew
installs under ``/opt/homebrew`` on Apple Silicon and ``/usr/local`` on
Intel.  A universal2 Python launched as x86_64 on Apple Silicon looks for
x86_64 libraries in whichever of those directories it was configured with.

Finding the libraries
---------------------

PyOpenGL first calls ``ctypes.util.find_library``, and loads what it returns.
If it returns nothing, PyOpenGL tries the bare name, then the explicit
framework path ``/System/Library/Frameworks/<name>.framework/<name>``.  The
explicit path loads ``OpenGL`` and ``GLUT`` on machines where
``find_library`` finds nothing.  The frameworks live in the dyld shared cache
and not as files on disk, so a search for the file fails.

A library outside the frameworks, such as a Homebrew freeglut, is found by
``find_library`` or by the dynamic loader's own search.  ``/opt/homebrew/lib``
is not on that search path by default.  Set ``DYLD_FALLBACK_LIBRARY_PATH`` to
point the loader at a Homebrew library.

Getting a window
----------------

GLFW, pygame, PyQt, PySide and wxPython all create Mac windows with a GL
context.  GLUT is in the system frameworks, so ``OpenGL.GLUT`` works with
nothing installed.  Apple ships the original GLUT implementation instead of
freeglut, and deprecates it along with the rest of the framework.
``OpenGL.Tk`` works with the system Tcl/Tk or a Homebrew one.

Naming the platform yourself
----------------------------

``PYOPENGL_PLATFORM=darwin`` selects this implementation explicitly.  PyOpenGL
selects the same one on macOS by default.  No other value works on macOS:
``osmesa`` needs an OSMesa this system does not have, and ``angle`` loads
Windows DLLs.
