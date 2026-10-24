PyOpenGL for OpenGL programmers
===============================

This page describes the features of PyOpenGL that an OpenGL programmer coming
from C will not expect, and the PyOpenGL behaviour that general OpenGL
documentation does not cover.

What a call costs
-----------------

By default PyOpenGL favours helpfulness and strictness over speed.  It checks
for errors after every call, converts array data that does not match what the
driver expects, and accepts many argument types.  Each of these has a cost,
and this page says how to turn each one off where a program needs the speed.

Where ``PyOpenGL_accelerate`` is installed, the entry points are compiled and
the per-call overhead is several times smaller.  :doc:`c-dispatch` has the
measurements and the switches.  With either implementation, per-vertex calls
(``glColor``, ``glNormal``, ``glVertex``) pay that overhead once per vertex,
and array calls pay it once per array.  Draw from arrays, and preferably from
buffer objects.

Signatures against the C specification
--------------------------------------

Most entry points are called exactly as the C specification describes them.
The exceptions come from the way Python handles arrays.  A C function that
takes a count and a pointer:

.. code-block:: c

   void foo(int count, const int *args);

has the Python binding:

.. code-block:: python

   foo(args) -> None

since the count is the length of the array.  A C function that writes into an
array the caller provides:

.. code-block:: c

   void bar(int args[4]);

returns that array instead:

.. code-block:: python

   bar() -> args[]

The :doc:`reference pages <reference/index>` give both forms for each entry
point.  The rest of this page covers the other differences.

Errors raise exceptions
-----------------------

PyOpenGL checks for a GL error after each call and raises an exception, so
the program does not have to check.

How the check is made depends on the context.  If the context offers
``GL_KHR_debug``, the driver reports errors through a callback during the
call, and the check afterwards reads the flag that callback set.  Otherwise
the check is a ``glGetError`` round trip.  Both implementations install the
callback automatically on a context that offers the extension:

.. code-block:: python

   >>> from OpenGL import dispatch
   >>> dispatch.error_checking_mode()
   'debug-output'

``'get-error'`` is the round trip and ``'off'`` is no checking at all.
:py:func:`OpenGL.dispatch.use_debug_output` turns the callback off for the
current context and back on again.  Setting
``OpenGL.ERROR_DEBUG_OUTPUT = False`` before the first call stops PyOpenGL
from installing it.
:doc:`c-dispatch` has the mechanism and the measurements.

The ``glGetError`` round trip is the cost of checking, and the callback
removes it: about one nanosecond per call instead of eleven.  On a context
with ``GL_KHR_debug``, turning checking off gains no speed, so a program can
ship with checking on.  Where the context offers only the round trip, switch
checking off with a flag on the ``OpenGL`` package, set before any submodule
is imported:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_CHECKING = False
   from OpenGL.GL import *

This roughly halves the number of calls issued to the driver.  PyOpenGL's own
helper code assumes errors raise, so code that runs with checking off must
call ``glGetError`` where it matters.

The exceptions raised are:

:py:exc:`OpenGL.error.GLError`
    from every module except WGL.

:py:exc:`OpenGL.error.GLUError`
    from some GLU entry points.  GLU can also raise ``GLError``.

:py:exc:`OSError`
    from WGL, where the Win32 API reports the failure.

:py:exc:`TypeError` and :py:exc:`ValueError`
    for an argument of the wrong type or an impossible value.

``GLError`` carries these details of the call:

``err``
    the OpenGL error code.

``result``
    the value the entry point returned.

``baseOperation``
    the entry point being called.

``pyArgs``
    the arguments as the caller passed them.

``cArgs``
    the Python-level objects expanded from ``pyArgs``, one per C argument.

``cArguments``
    the ctypes-level objects converted from ``cArgs``.

``description``
    OpenGL's own description of the error code.

Logging
-------

PyOpenGL logs errors through the :py:mod:`logging` module.  A release build can
switch that off:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_LOGGING = False

To see every call PyOpenGL makes, with its arguments, turn on full logging:

.. code-block:: python

   import OpenGL
   OpenGL.FULL_LOGGING = True

Full logging is slow enough to change the behaviour of timing-dependent code.
Use it to trace a crash, and leave it off for normal runs.

What a wrapped call does
------------------------

Under the C implementation, each entry point is a C function generated from
the Khronos registry.  A call checks the argument count, converts the scalars,
and acquires a buffer over each array.  It acquires the buffer directly where
the element type already matches what the driver expects, and through the
format-handler registry where it does not.  It then loads the function pointer
held for the current context, calls it, releases the buffers, converts the
result and checks for an error.

Under the ctypes implementation the same work is done by a chain of Python
objects built at import time, in these stages:

1. *converters* turn the arguments into the object types the wrapper works
   with (``pyArgs``);
2. *cConverters* turn ``pyArgs`` into objects mapping one-to-one onto the C
   arguments (``cArgs``).  This is where one Python argument becomes several
   C ones;
3. *cResolvers* turn ``cArgs`` into the final ctypes-compatible arguments
   (``cArguments``);
4. *storeValues* keeps alive any temporary the driver will read after the call
   returns, such as the object behind a pointer;
5. a *return* function decides what the call returns.

:py:class:`OpenGL.wrapper.Wrapper` holds that chain, and ``GLError`` reports
the arguments under those names.  The two implementations are meant to behave
identically from outside.  Where a module customises an entry point in a way
the C does not perform, the entry point demotes to its ctypes binding, and the
customisation is replayed onto it.  :doc:`wrapping` describes the internals,
and :doc:`c-dispatch` describes what differs at the surface.

Array handling
--------------

An entry point that takes an array, or a ``void *``, accepts any type that a
registered :py:mod:`format handler <OpenGL.arrays.formathandler>` claims.  The
shipped handlers cover:

- NumPy arrays
- byte strings
- numbers, treated as a pointer to a one-element array
- ctypes arrays, parameters and pointers
- lists and tuples
- vertex buffer objects

Lists, tuples and numbers have no buffer for the driver to read, so each call
builds a temporary array.  A NumPy array whose data type does not match the
entry point is converted, which also builds a temporary.  Avoid both in code
that runs every frame.  To find where they happen:

.. code-block:: python

   import OpenGL
   OpenGL.ERROR_ON_COPY = True

which makes the format handlers raise :py:exc:`OpenGL.error.CopyError`
instead of copying.

Type-specialised array functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each entry point that sets an array pointer has, beside the form the
specification describes, a set of suffixed forms:

.. code-block:: text

   glXPointer{ub|b|us|s|ui|i|f|d}

Each takes a single multidimensional array.  The suffix fixes the element type
(``ub`` unsigned byte, ``b`` byte, ``f`` float, ``d`` double), and the
remaining arguments come from the array's shape.  For ``glColorPointer``:

.. code-block:: python

   glColorPointer(size, type, stride, pointer) -> None
   glColorPointerub(pointer[][]) -> None
   glColorPointerb(pointer[][]) -> None
   glColorPointerus(pointer[][]) -> None
   glColorPointers(pointer[][]) -> None
   glColorPointerui(pointer[][]) -> None
   glColorPointeri(pointer[][]) -> None
   glColorPointerf(pointer[][]) -> None
   glColorPointerd(pointer[][]) -> None

Other array entry points have suffixed forms too.  ``glDrawElements`` has:

.. code-block:: python

   glDrawElements(mode, count, type, indices) -> None
   glDrawElementsub(mode, indices[]) -> None
   glDrawElementsus(mode, indices[]) -> None
   glDrawElementsui(mode, indices[]) -> None

where the suffixed forms take a one-dimensional array.

Memory passed to ``glColorPointer``, ``glVertexPointer`` and the rest is
reference-counted, and the count follows ``glPushClientAttrib`` and
``glPopClientAttrib``.  To release it explicitly, pass ``None``:
``glColorPointerub(None)``.

``glPushClientAttrib`` always sets ``GL_CLIENT_VERTEX_ARRAY_BIT``.
``glPopClientAttrib`` reads that flag to decide whether to drop the pointer
locks.  Bracketing array use in a ``glPushClientAttrib`` /
``glPopClientAttrib`` pair releases the allocations, provided every
``glXPointer`` call is inside the pair.

Because the allocation is automatic, ``glGetPointerv`` has nothing to report,
and it is not wrapped.  ``glInterleavedArrays`` is wrapped, without the
suffixed variants.

Image routines
--------------

``glDrawPixels`` and the texture entry points have suffixed forms, like the
array functions.  The specification form takes the pixel data as a byte
string:

.. code-block:: python

   glDrawPixels(width, height, format, type, pixels) -> None

and uses the state set by ``glPixelStore{i|f}``.  The suffixed forms take a
multidimensional array and set ``glPixelStore{i|f}`` themselves:

.. code-block:: python

   glDrawPixelsub(format, pixels) -> None

where the width, height and type all come from the array.

PyOpenGL sets tightly packed pixel-transfer state for the imaging entry
points.  Python image libraries produce tightly packed buffers, and reading
them with OpenGL's default packing would read past the end.

Extensions and conditional functionality
----------------------------------------

An extension's entry points come from the module named after it, with no
initialisation call needed:

.. code-block:: python

   from OpenGL.GL.ARB.vertex_buffer_object import *
   buffer = glGenBuffersARB(1)

The extension's ``init`` function reports whether the machine supports it:

.. code-block:: python

   if glInitVertexBufferObjectARB():
       ...

Testing the entry points you intend to call is more specific:

.. code-block:: python

   from OpenGL.extensions import available

   if available(glGenBuffersARB):
       buffers = glGenBuffersARB(1)

Where several entry points implement the same API and any of them will do,
:py:func:`OpenGL.extensions.alternate` picks whichever is present, in the order
given:

.. code-block:: python

   from OpenGL.extensions import alternate
   glCreateProgram = alternate('glCreateProgram', glCreateProgram, glCreateProgramObjectARB)
   glCreateProgram = alternate(glCreateProgram, glCreateProgramObjectARB)

A string as the first argument names the result; otherwise the name comes from
the first entry point.

Selection and feedback buffers
------------------------------

Both are deprecated in OpenGL 3.x.  Modern programs pick objects by rendering
unique colours, or by intersecting in their own coordinates.  Where selection
is used, C allocates the buffer:

.. code-block:: c

   GLuint buffer[SIZE];
   glSelectBuffer(SIZE, buffer);
   glRenderMode(GL_SELECT);
   /* draw some stuff */
   GLint count = glRenderMode(GL_RENDER);
   /* parse the selection buffer */

and PyOpenGL returns it:

.. code-block:: python

   glSelectBuffer(SIZE)          # allocate a buffer of SIZE elements
   glRenderMode(GL_SELECT)
   # draw some stuff
   buffer = glRenderMode(GL_RENDER)
   for hit_record in buffer:
       min_depth, max_depth, names = hit_record
       ...

Feedback buffers work the same way, with each item a ``(token, value)`` tuple
whose value is either a passthrough token or a list of vertices.

Returning the buffer also clears OpenGL's pointer to it, so a later pass
cannot overwrite the buffer ``glRenderMode`` returned.  As a result, each
``glRenderMode(GL_SELECT)`` or ``glRenderMode(GL_FEEDBACK)`` must be preceded
by its own ``glSelectBuffer`` or ``glFeedbackBuffer``.  This does not work:

.. code-block:: python

   glSelectBuffer(SIZE)
   glRenderMode(GL_SELECT)
   # draw some stuff
   buffer = glRenderMode(GL_RENDER)
   glRenderMode(GL_SELECT)       # no buffer is set any more
   # draw some stuff
   buffer = glRenderMode(GL_RENDER)

This does:

.. code-block:: python

   glSelectBuffer(SIZE)
   glRenderMode(GL_SELECT)
   # draw some stuff
   buffer = glRenderMode(GL_RENDER)

   glSelectBuffer(SIZE)          # a new buffer for the second pass
   glRenderMode(GL_SELECT)
   # draw some stuff
   buffer = glRenderMode(GL_RENDER)

Function aliases
----------------

PyOpenGL provides undecorated names for some entry points:

============================ ================================================
Entry point                  Also available as
============================ ================================================
``glGetBooleanv``            ``glGetBoolean``
``glGetDoublev``             ``glGetDouble``
``glGetIntegerv``            ``glGetInteger``
``glColord``                 ``glColor``, ``glColor3``, ``glColor4``
``glEvalCoordd``             ``glEvalCoord``, ``glEvalCoord1``, ``glEvalCoord2``
``glFogfv``                  ``glFog``
``glIndexd``                 ``glIndex``
``glLightfv``                ``glLight``
``glLightModelfv``           ``glLightModel``
``glMaterialfv``             ``glMaterial``
``glNormald``                ``glNormal``, ``glNormal3``, ``glNormal4``
``glRasterPosd``             ``glRasterPos``, ``glRasterPos2``,
                             ``glRasterPos3``, ``glRasterPos4``
``glRotated``                ``glRotate``
``glScaled``                 ``glScale``
``glTexCoordd``              ``glTexCoord``, ``glTexCoord1``, ``glTexCoord2``,
                             ``glTexCoord3``, ``glTexCoord4``
``glTexGendv``               ``glTexGen``
``glTexParameterfv``         ``glTexParameter``
``glTranslated``             ``glTranslate``
``glVertexd``                ``glVertex``
============================ ================================================
