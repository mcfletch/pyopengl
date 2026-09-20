Using OpenGL in Python
======================

This page describes getting started with OpenGL from Python through PyOpenGL.
It assumes some familiarity with Python, with OpenGL, and with NumPy.

Accessing OpenGL functionality
------------------------------

The OpenGL library is a single instance per process, shared by all in-process
code that issues OpenGL commands.  Something has to create a context before
PyOpenGL can draw into one: `GLFW <https://pypi.org/project/glfw/>`__ is the
one to reach for, and is what PyOpenGL's own test suite uses.  A program that
already has a GUI toolkit -- PyGame, PyQt or PySide, wxPython, PyGTK, Tkinter
through :py:mod:`OpenGL.Tk` -- uses that toolkit's OpenGL widget instead, and
one that wants no toolkit at all can use GLUT, which PyOpenGL also wraps.

The GUI package defines an OpenGL "window" and makes it current.  Once it is
current, PyOpenGL commands draw into it, as do commands issued from another
language in the same process.  The drawing itself normally happens in handlers
the framework calls: display, resize, mouse movement and the like.

For the core API, import :py:mod:`OpenGL.GL` and :py:mod:`OpenGL.GLU`:

.. code-block:: python

   from OpenGL.GL import *
   from OpenGL.GLU import *

An extension's entry points come from its own module:

.. code-block:: python

   from OpenGL.GL.ARB.shader_objects import *
   from OpenGL.GL.ARB.fragment_shader import *
   from OpenGL.GL.ARB.vertex_shader import *

Check that an extension is present before calling into it, so that the program
can fall back rather than fail:

.. code-block:: python

   if not glInitShaderObjectsARB():
       raise RuntimeError(
           "ARB shader objects are required but not supported here"
       )

Extensions and the version that adopts them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most extensions are eventually adopted into a GL version, and a command that
has been is declared twice: once by the extension that introduced it, and once
by the version that adopted it.  :py:mod:`OpenGL.GL` exports the version's
declaration, which is available whenever the context provides that version.
The extension module keeps its own, which is available only while the driver
advertises the extension string -- and a driver is free to stop advertising one
it has promoted, as a core profile commonly does.

.. code-block:: python

   from OpenGL.GL import glCreateShaderProgramv    # GL 4.1; asks the context
   from OpenGL.GL.ARB.separate_shader_objects import glCreateShaderProgramv
                                                  # asks for the extension string

Import from :py:mod:`OpenGL.GL` for a command your context's version provides,
and from the extension module when the extension itself is what you depend on.

A single entry point answers for itself, which is what you want when one
command of an extension is all you need, or when a driver serves part of one.
:py:func:`OpenGL.extensions.available` asks it:

.. code-block:: python

   from OpenGL.extensions import available

   if available(glPointParameterf):
       glPointParameterf(GL_POINT_SIZE_MAX, 64.0)

The entry point answers ``bool()`` with the same thing, so ``if
glPointParameterf:`` works as well.  Prefer the call in code you type-check: a
stub declares the name as a function, a function object is always true, and a
checker reports the bare form as a missing ``()``.  ``available(None)`` is
``False``, so a name reached with ``getattr(module, name, None)`` needs no
separate test.

Differences from C-level OpenGL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyOpenGL provides a Pythonic interface to OpenGL: it implies arguments it can
work out, such as the length of an array from the array itself, and it returns
values rather than filling in buffers you pass.  :doc:`opengl-programmers`
covers the differences an OpenGL programmer coming from C will meet, and the
:doc:`reference pages <reference/index>` give the Python signature beside the C
prototype for each entry point.

Error handling
~~~~~~~~~~~~~~

PyOpenGL follows Python's *errors should never pass silently*, rather than
OpenGL's model of explicit checks.  Each entry point runs
:py:func:`OpenGL.error.glCheckError` after the call.  That check is
``glBegin``/``glEnd``-aware: those two switch it off and on again, because
``glGetError`` does not report between them.

Calling C-level ``glBegin``/``glEnd`` from another extension in the same
process can leave the check out of step with the driver.  Switch checking off
explicitly in that case.

Checking can be switched off entirely before anything in the ``OpenGL``
namespace is imported -- that is, as the first thing the top-level script does:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_CHECKING = False

Applications may do this; libraries should not, since it takes the diagnosis
away from whoever is debugging the application.

Under :doc:`the C dispatch layer <c-dispatch>` the same flag applies per entry
point per context, and the check is made from C rather than through a Python
callback, so it costs the driver round trip and nothing else.

The round trip is most of what checking costs, and a context offering
``GL_KHR_debug`` does not pay it: the driver reports the error through a
callback during the call, so the check is a read of the flag that callback set.
Both implementations use it where a context offers it, without being asked.
``OpenGL.dispatch.error_checking_mode()`` says which mechanism a context ended
up with, and :doc:`c-dispatch` describes how to decline it.

The checker itself can be replaced rather than switched off.  A program that
always has a valid context can register the raw ``glGetError`` and skip the
context-validity test:

.. code-block:: python

   from OpenGL import error
   error.ErrorChecker.registerChecker(myAlternateFunction)

:py:mod:`OpenGL.error` defines the errors PyOpenGL raises.  It also raises
standard Python exceptions -- :py:exc:`ValueError`, :py:exc:`TypeError` --
where those fit.  The wrappers catch OpenGL errors and add what they know about
the call to them, so that a failure names the argument that caused it.

Performance
-----------

Every call into OpenGL costs something on the Python side, so the way to be
fast is to make fewer, larger calls: put the data where the driver can reach it
and let the hardware iterate.

Buffer objects
    Geometry belongs in a vertex buffer object, uploaded once and drawn from
    many times.  :py:mod:`OpenGL.arrays.vbo` wraps the creation, binding and
    updating; a NumPy array goes to the driver without a Python-level loop and
    without a copy, provided its data type already matches.  A vertex array
    object then records the attribute bindings, so a draw is one state change
    and one call.

Instanced drawing
    ``glDrawArraysInstanced`` and ``glDrawElementsInstanced`` draw the same
    geometry many times from one call, with per-instance attributes supplying
    what differs.  This is how to draw a forest, a particle system or a tile
    map without a call per object.

Uniform buffer objects
    A block of uniforms uploaded once and bound to several programs, rather
    than a ``glUniform*`` call per value per frame.  Shader storage buffers do
    the same for larger and writable data.

Multi-draw
    ``glMultiDrawElements`` and the indirect forms take a list of draws in one
    call, including one whose parameters the GPU itself wrote.

Batch by state
    Sort what you draw so that programs, textures and buffers are bound as few
    times as possible; a bind is a call, and calls are what cost.

Display lists are not on this list.  They are fixed-function OpenGL, removed
from the core profile, and where a driver still offers them it is through a
compatibility path that is slower than a buffer object.

Avoiding array copies
~~~~~~~~~~~~~~~~~~~~~

The largest avoidable cost in array-based PyOpenGL code is passing

- an array whose data type is compatible but not exact, or
- a non-contiguous array, which has no single data pointer.

Either makes PyOpenGL copy the array on every call.  The copy happens in C, but
on a per-frame data set it is still the dominant cost.

The copy is made by default so that a mismatch between ``float`` and ``double``
is a working program rather than a mystifying error.  To find the places it
happens, ask for an error instead:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_ON_COPY = True

which raises :py:exc:`OpenGL.error.CopyError`, naming the condition and the
reason for the copy.

The flag is about array *data*.  A string parameter -- a uniform or attribute
name, a debug label, GLSL source -- still takes a :py:class:`str` and is
encoded for you, since it is encoded once and read before the call returns.

The assignment has to come before the first entry point is built: the flags are
read once and frozen, so setting one afterwards is dropped and PyOpenGL warns
that it was.  Every flag in ``OpenGL/__init__.py``'s list is also settable as
``PYOPENGL_<NAME>`` in the environment -- ``PYOPENGL_ERROR_ON_COPY=1`` -- which
is read before anything is built and so works whatever the import order.  That
is how a program that does not control its own imports sets one.

Context-specific data
---------------------

A pointer PyOpenGL hands the driver has to keep the Python object behind it
alive for as long as the driver may read it.  PyOpenGL does that by storing the
object against a key for the current context;
:py:mod:`OpenGL.contextdata` is the interface to that storage.  The key comes
from the platform module's ``GetCurrentContext()``, and a ``context`` argument
of ``None`` means the current one.

A program that creates and destroys rendering contexts has to clear that
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
a context whose storage has been cleaned up reads freed memory.

Tkinter
-------

:py:mod:`OpenGL.Tk` gives Tkinter an OpenGL widget.  It needs nothing but
PyOpenGL and a Python built with Tk support: the widget creates its own context
through the platform's own API, so there is no separate extension to install.
:doc:`tk-widget` has the details, including the widget options and what a
program that used the old Togl-based widget has to change.

Contributing
------------

:doc:`development` describes the layout of the code, how to run the suite and
how to send a change.
