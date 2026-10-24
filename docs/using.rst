Using OpenGL in Python
======================

This page describes getting started with OpenGL from Python through PyOpenGL.
It assumes some familiarity with Python, with OpenGL, and with NumPy.

Accessing OpenGL functionality
------------------------------

The OpenGL library is a single instance per process, shared by all in-process
code that issues OpenGL commands.  PyOpenGL draws into a context that another
library creates.  `GLFW <https://pypi.org/project/glfw/>`__ is a good
choice, and PyOpenGL's own test suite uses it.  A program that already uses a
GUI toolkit (PyGame, PyQt or PySide, wxPython, PyGTK, or Tkinter through
:py:mod:`OpenGL.Tk`) uses that toolkit's OpenGL widget instead. GLUT is also 
available from PyOpenGL (:mod:`OpenGL.GLUT`) and can be used, but note that 
it does not work natively on modern Linux Wayland machines.

The GUI package creates an OpenGL "window" and makes it current.  PyOpenGL
commands then draw into it, as do commands issued from another language in the
same process.  Drawing normally happens in handlers the framework calls, such
as display, resize and mouse movement.

For the core API, import :py:mod:`OpenGL.GL` and :py:mod:`OpenGL.GLU`:

.. code-block:: python

   from OpenGL.GL import *
   from OpenGL.GLU import *

An extension's entry points come from its own module:

.. code-block:: python

   from OpenGL.GL.ARB.shader_objects import *
   from OpenGL.GL.ARB.fragment_shader import *
   from OpenGL.GL.ARB.vertex_shader import *

Check that an extension is present before calling into it, so the program can
fall back instead of failing:

.. code-block:: python

   if not glInitShaderObjectsARB():
       raise RuntimeError(
           "ARB shader objects are required but not supported here"
       )

Extensions and the version that adopts them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most extensions are eventually adopted into a GL version.  A command from such
an extension is declared twice: once by the extension that introduced it, and
once by the version that adopted it.  :py:mod:`OpenGL.GL` exports the
version's declaration, which is available whenever the context provides that
version.  The extension module exports its own declaration, which is
available only while the driver advertises the extension string.  A driver
may stop advertising an extension it has promoted to core, and a core profile
commonly does.

.. code-block:: python

   from OpenGL.GL import glCreateShaderProgramv    # GL 4.1; asks the context
   from OpenGL.GL.ARB.separate_shader_objects import glCreateShaderProgramv
                                                  # asks for the extension string

Import from :py:mod:`OpenGL.GL` for a command your context's version provides,
and from the extension module when the extension itself is what you depend on.

A single entry point can be tested on its own.  This is useful when you need
only one command of an extension, or when a driver implements only part of
one.  :py:func:`OpenGL.extensions.available` makes the test:

.. code-block:: python

   from OpenGL.extensions import available

   if available(glPointParameterf):
       glPointParameterf(GL_POINT_SIZE_MAX, 64.0)

``bool()`` on the entry point gives the same result, so
``if glPointParameterf:`` also works.  Prefer the call in type-checked code.
A stub declares the name as a function, a function object is always true, and
a type checker reports the bare form as a missing ``()``.  ``available(None)``
is ``False``, so a name looked up with ``getattr(module, name, None)`` needs
no separate test.

Differences from C-level OpenGL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyOpenGL provides a Pythonic interface to OpenGL.  It computes arguments it
can derive, such as the length of an array from the array itself, and it
returns values instead of filling in buffers you pass.
:doc:`opengl-programmers` covers the differences an OpenGL programmer coming
from C will meet, and the :doc:`reference pages <reference/index>` give the
Python signature beside the C prototype for each entry point.

Error handling
~~~~~~~~~~~~~~

PyOpenGL follows Python's *errors should never pass silently*, instead of
OpenGL's model of explicit checks.  A GL call that fails raises
:py:exc:`OpenGL.error.GLError`, naming the call and its arguments.

On a context that offers ``GL_KHR_debug`` (core in OpenGL 4.3, and offered by
current Linux and Windows drivers), PyOpenGL installs a debug callback the
first time it checks for an error.  The driver reports an error to that
callback during the failing call, and PyOpenGL raises the error when the call
returns.  A call that succeeds costs one flag read, with no extra trip to the
driver.

A context uses ``glGetError`` after every call instead when:

- the context does not offer ``GL_KHR_debug``, as on macOS, whose OpenGL
  stops at 4.1;
- the program or another library has already installed a debug callback on the
  context, which PyOpenGL does not replace;
- ``OpenGL.ERROR_DEBUG_OUTPUT`` is set to False before ``OpenGL.GL`` is
  imported, or the program calls ``OpenGL.dispatch.use_debug_output(False)``
  with the context current;
- an occasional ``glGetError`` check (one call in 64) finds an error the
  callback did not report.  That context then uses ``glGetError`` from then
  on.

Both methods raise the same ``GLError`` from the same call.
``OpenGL.dispatch.error_checking_mode()`` returns ``'debug-output'``,
``'get-error'`` or ``'off'`` for the current context, and
:doc:`c-dispatch` gives the timings.

``glBegin`` switches checking off and ``glEnd`` switches it on again, because
``glGetError`` cannot be called between them.  Calling C-level
``glBegin``/``glEnd`` from another extension in the same process can leave the
check out of step with the driver.  Switch checking off explicitly in that
case. Note: You should not be using glBegin/glEnd in new code.

Checking can be switched off entirely, before anything in the ``OpenGL``
namespace is imported.  Do this as the first thing in the top-level script:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_CHECKING = False

Applications may do this.  Libraries should not, because it removes the error
reports that someone debugging the application needs.

:py:mod:`OpenGL.error` defines the errors PyOpenGL raises.  PyOpenGL also
raises standard Python exceptions, such as :py:exc:`ValueError` and
:py:exc:`TypeError`, where those fit.

Performance
-----------

Every call into OpenGL has a cost on the Python side, so fast code makes fewer,
larger calls.  Put the data in buffers the driver can read, and let the
hardware iterate over it.

Buffer objects
    Store geometry in a vertex buffer object, upload it once and draw from it
    many times.  :py:mod:`OpenGL.arrays.vbo` wraps creating, binding and
    updating the buffer.  A NumPy array whose data type already matches goes
    to the driver without a Python-level loop and without a copy.  A vertex
    array object records the attribute bindings, so a draw is one state change
    and one call.

Instanced drawing
    ``glDrawArraysInstanced`` and ``glDrawElementsInstanced`` draw the same
    geometry many times in one call, with per-instance attributes for what
    differs.  Use them to draw a forest, a particle system or a tile map
    without one call per object.

Uniform buffer objects
    A block of uniforms uploaded once and bound to several programs, in place
    of a ``glUniform*`` call per value per frame.  Shader storage buffers do
    the same for larger data, and shaders can write to them.

Multi-draw
    ``glMultiDrawElements`` and the indirect forms take a list of draws in one
    call.  An indirect draw can use parameters that the GPU itself wrote.

Batch by state
    Sort draws so that programs, textures and buffers are bound as few times
    as possible.  Each bind is a call, and calls are the main cost.

Avoid legacy APIs
    glBegin/glEnd and display lists are not recommended.  
    They are fixed-function OpenGL, removed from the core profile.
    Drivers that still offer them do so through a
    compatibility path that is slower than a buffer object.

Avoiding array copies
~~~~~~~~~~~~~~~~~~~~~

The largest avoidable cost in array-based PyOpenGL code comes from passing

- an array whose data type is compatible but not exact, or
- a non-contiguous array, which has no single data pointer.

Either one makes PyOpenGL copy the array on every call.  The copy happens in
C, but for data passed every frame it is still a large cost.

PyOpenGL copies by default so that a mismatch between ``float`` and
``double`` still runs, instead of raising a confusing error.  To find where
copies happen, ask for an error instead:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_ON_COPY = True

which raises :py:exc:`OpenGL.error.CopyError`, naming the condition and the
reason for the copy.

A typed client-array setter converts its data to one element type, the type
it passes to the driver.  That is usually the type its suffix names.  The
exceptions are ``glVertexPointerb``, ``glIndexPointerb`` and
``glTexCoordPointerb``.  They widen signed bytes to ``GL_INT``, which those
entry points take in place of ``GL_BYTE``.  An array of any other type is
copied on every call, and raises an error under the flag.  Pass an array of
the type the setter converts to.  For the three that widen, widen the data
once and keep the wider array.

The flag applies to array *data*.  A string parameter (a uniform or attribute
name, a debug label, GLSL source) still takes a :py:class:`str`, which
PyOpenGL encodes for you.  The string is encoded once and read before the call
returns.

Set the flag before the first entry point is built.  The flags are read once
and then fixed.  A later assignment has no effect, and PyOpenGL warns about
it.  Every flag in ``OpenGL/__init__.py``'s list can also be set in the
environment as ``PYOPENGL_<NAME>``, for example ``PYOPENGL_ERROR_ON_COPY=1``.
The environment is read before anything is built, so it works regardless of
import order.  Use it in a program that does not control its own imports.

Context-specific data
---------------------

A pointer PyOpenGL passes to the driver must keep the Python object behind it
alive for as long as the driver may read it.  PyOpenGL stores the object
against a key for the current context, and :py:mod:`OpenGL.contextdata` is
the interface to that storage.  The key comes from the platform module's
``GetCurrentContext()``, and a ``context`` argument of ``None`` means the
current context.

A program that creates and destroys rendering contexts must clear that
storage, or every array it ever passed stays reachable.  Set the values to
``None``, or clean up the context as a whole:

.. code-block:: python

   from OpenGL import contextdata

   def cleanup_callback(context=None):
       """Clear context-specific storage for a context that will not render again"""
       context = contextdata.getContext(context)
       def callback():
           contextdata.cleanupContext(context)
       return callback

Register the callback to run *after* the context is destroyed.  Rendering into
a context whose storage has been cleaned up reads freed memory (segfaults).

Tkinter
-------

:py:mod:`OpenGL.Tk` gives Tkinter an OpenGL widget.  It needs only PyOpenGL
and a Python built with Tk support.  The widget creates its own context
through the platform's API, so there is no separate extension to install.
:doc:`tk-widget` has the details, including the widget options and the
changes a program written for the old Togl-based widget needs.

Contributing
------------

:doc:`development` describes the layout of the code, how to run the suite and
how to send a change.
