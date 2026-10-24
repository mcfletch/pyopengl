Contributing to PyOpenGL
========================

This page describes the architecture of PyOpenGL and where to start work on it.
It assumes familiarity with Python, NumPy and ctypes.

Getting the code
----------------

PyOpenGL is developed on `GitHub <https://github.com/mcfletch/pyopengl>`__:

.. code-block:: console

   $ git clone https://github.com/mcfletch/pyopengl.git
   $ cd pyopengl
   $ pip install -e . ./accelerate

The last command installs both packages; :doc:`installation` explains why.
Send changes as pull requests, with test cases wherever a case can be written.

Design goals
------------

Access to all of OpenGL
    OpenGL 1.1 through 4.x, OpenGL ES 1 through 3, and the registered
    extensions.

Compatibility with existing PyOpenGL code
    Most code should run unchanged, and the rest with small changes.
    Application code should not depend on the implementation underneath, so
    it keeps working when that implementation changes.

Playing well with others
    Working with alternative Python implementations, GUI libraries, numeric
    libraries, multimedia libraries, and the host program's threading model.

Robustness
    Degrading instead of failing where functionality is absent, reporting
    errors that name the cause, and being easy to debug.

Ease of installation
    Portable to anywhere ctypes runs, installable with standard tooling, and
    extensible with new data types through plugins.

Platform abstraction
--------------------

PyOpenGL exposes the host platform's OpenGL to Python.  The differences
between platforms are kept in the ``platform`` subpackage, so porting to a new
platform is mostly a matter of writing one small module there.

Each platform has its own
:py:class:`OpenGL.platform.baseplatform.BasePlatform` subclass, which provides:

- the library objects for GL, GLU, GLUT and GLE.  How the libraries are found,
  what they are called and what flags loading them needs are all
  platform-specific;
- the function type used to call into those libraries, which sets the calling
  convention (``stdcall`` on Windows, ``cdecl`` elsewhere);
- ``GetCurrentContext()`` and ``CurrentContextIsValid()``, which the
  context-specific storage is keyed on;
- ``getExtensionProcedure(name)``, to resolve an extension entry point;
- ``getGLUTFontPointer(constant)``, since each platform represents a GLUT font
  differently;
- the flags ``HAS_DYNAMIC_EXT`` and ``EXT_DEFINES_PROTO``, saying whether the
  platform can load extensions dynamically and whether it defines prototypes;
- ``safeGetError()``, which reads OpenGL's error state only where that is
  safe: with a valid context, or on a platform that allows the call without
  one;
- ``createBaseFunction`` and ``createExtensionFunction``, which build the
  callable for an entry point:

  .. code-block:: python

     def createBaseFunction(
         functionName, dll=OpenGL,
         resultType=ctypes.c_int, argTypes=(),
         doc=None, argNames=(),
     ):

     def createExtensionFunction(
         functionName, dll=OpenGL,
         resultType=ctypes.c_int, argTypes=(),
         doc=None, argNames=(),
     ):

Each platform implementation is registered as a ``PlatformPlugin`` in
``OpenGL/__init__.py``, under one or more names.  To add your own, create a
``PlatformPlugin`` before importing ``OpenGL.platform``.  Importing
``OpenGL.platform`` loads the first plugin whose name matches one of these
values, in order:

#. ``PYOPENGL_PLATFORM``, from the environment;
#. ``XDG_SESSION_TYPE``, lower-cased (``x11`` and ``wayland`` are registered);
#. on Linux with ``PYOPENGL_PLATFORM`` unset, ``wayland`` where
   ``WAYLAND_DISPLAY`` is set, otherwise ``linux`` where ``DISPLAY`` is;
#. ``sys.platform``;
#. ``os.name``.

A value that names no plugin is skipped.  A misspelt ``PYOPENGL_PLATFORM``
therefore has no effect, and PyOpenGL chooses the platform as if it were
unset.  If a plugin's import fails, PyOpenGL raises ``ImportError`` naming the
plugin, and logs the reason to the ``OpenGL.plugins`` logger.  The values each
platform accepts are in :doc:`platform-linux`, :doc:`platform-macos` and
:doc:`platform-windows`.

Generated bindings
------------------

Almost everything PyOpenGL exports is generated from the Khronos XML
registries.  Khronos publishes two registry repositories.  Both are fetched as
working copies; neither is vendored into this repository:

.. code-block:: console

   $ python src/fetch_registries.py

``src/khronosapi``
    `OpenGL-Registry <https://github.com/KhronosGroup/OpenGL-Registry>`__:
    ``gl.xml``, ``glx.xml``, ``wgl.xml``, and the extension specifications.

``src/eglapi``
    `EGL-Registry <https://github.com/KhronosGroup/EGL-Registry>`__:
    ``api/egl.xml``.

``src/cdispatch/registry_lock.json`` records the commit of each registry that
the shipped bindings came from.  A fetch that finds a different commit stops
the run.  Every enum value and signature comes from those repositories, and
the tests are generated from the same input, so no test can catch a wrong
value.  Moving to a newer registry is therefore requested explicitly, and
produces a diff to review:

.. code-block:: console

   $ python src/regenerate_c.py --update-registries

What the generators write
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ python src/regenerate_c.py      # the compiled entry points
   $ python src/xml_generate.py      # the Python-level API

``regenerate_c.py`` writes the C dispatch layer into
``accelerate/src/c/generated``, which is compiled into
``OpenGL_accelerate.dispatch``.  :doc:`c-dispatch` describes that layer.
``src/cdispatch/README.md`` is the guide to the generator, including how to
add an entry point that needs hand-written C.

``xml_generate.py`` writes the Python-level API: the declaration tables in
``OpenGL/raw/_declarations/*.dat``, and the friendly modules beside them.  At
import time a finder turns the tables into the ``OpenGL.raw`` namespaces.
There are no ``OpenGL.raw`` source files; the tables are the only source.

The generator also registers each ``glGet`` constant against the size of the
array it returns, so a ``glGet*`` call returns an array of the right length.
The sizes come from the specifications and ``src/glgetsizes.csv``.  Each
extension module also gets the specification's "Overview" as its docstring.

GLU, GLUT and GLE are not in the registries, so their wrappers are written by
hand.  All three APIs have been stable for many years.

Checking a regeneration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ python src/check_registry.py --verbose

This reports where the shipped bindings and the registry disagree: a registry
command with no binding, a binding whose signature no longer matches, an enum
with no constant, and every entry point still on the ctypes path, with the
reason.  Known differences are recorded in
``src/cdispatch/registry_baseline.json``, each with a reason.  With
``--new-only``, the command exits non-zero for any difference not recorded
there.

``.github/workflows/registry-update.yml`` runs this check weekly.  It fetches
the registries, regenerates, checks for unrecorded drift, and opens a pull
request when the regeneration produced a diff.  The pull request body holds
the report, so the change can be reviewed without a checkout.  Khronos adds
entry points to the registry continuously.  Without this job, a missing
binding would only be found when someone tried to call it.

Regenerating by hand is therefore only needed when working on a generator.  In
the weekly pull request, only an entry point whose generated body is not a
plain macro expansion needs review by a person; the rest is table data.

Customising a generated module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An extension module is a single file with its generated half above a marker:

.. code-block:: python

   ### DO NOT EDIT above the line "END AUTOGENERATED SECTION" below!
   ...
   ### END AUTOGENERATED SECTION

Customisations go below the marker.  Removing the marker stops the generator
from updating the module, so the module also misses later improvements to the
generator.  Changes that make an extension module more Pythonic are welcome.

Converters and wrappers
-----------------------

Where the generated ctypes wrapper cannot be used as it stands, the entry point
is built from :py:class:`OpenGL.wrapper.Wrapper` and the converters in
:py:mod:`OpenGL.converters`.  ``Wrapper`` provides a set of argument
transformation stages, and most entry points are composed from a few simple
operations.  Each operation is specified explicitly for its entry point.  A
SWIG-style generator would match them by rule instead.

Where a custom function using raw ctypes is simpler, write one and bind it to
the entry point's name.  The lazy wrapper below makes that easier.

The stages of a wrapped call are:

1. ``pyConverters`` - accept or suppress an incoming Python argument.  A
   converter can convert an argument to the expected type, or remove it from
   the argument list entirely.  Removal is how an argument implied by the
   shape of another one disappears from the Python signature.
2. ``cConverters`` - look at the whole Python argument list and produce a
   one-to-one list of Python objects for the ctypes call.
3. ``cResolvers`` - turn those into the low-level values ctypes passes.
4. the call itself, with error checking.  An error is annotated with the
   arguments the call was made with.
5. ``storeValues`` - keep alive anything the driver reads after the call
   returns, such as the array behind a pointer.
6. ``returnValues`` - decide what the wrapped entry point returns.

``Wrapper.setOutput`` builds an output array for a call from a size tuple, a
dictionary or a function.  :py:mod:`OpenGL.GL.glget` has many examples.

Lazy wrapping
~~~~~~~~~~~~~

To write a small piece of Python around a generated entry point, use
:py:mod:`OpenGL.lazywrapper`.  The decorated function receives the base
operation as its first argument:

.. code-block:: python

   @lazy(glGetInfoLogARB)
   def glGetInfoLogARB(baseOperation, obj):
       """Retrieve the program/shader's error messages as a Python string

       returns string which is '' if no message
       """
       length = int(glGetObjectParameterivARB(obj, GL_INFO_LOG_LENGTH_ARB))
       if length > 0:
           log = ctypes.create_string_buffer(length)
           baseOperation(obj, length, None, log)
           return log.value.strip(b'\000')
       return ''

Array handling
--------------

A Python program passes most of its work to OpenGL through array operations,
so array handling largely sets the binding's speed in practice.  NumPy is the
preferred array implementation.

The machinery is in :py:mod:`OpenGL.arrays`.  Two kinds of class do the work.
A :py:mod:`FormatHandler <OpenGL.arrays.formathandler>` gives access to the
data of one Python type, and an ``ArrayDatatype`` models one OpenGL array
format.  ``ArrayDatatype`` uses the format handlers to read whatever data the
caller passed.

ArrayDatatypes
~~~~~~~~~~~~~~

The ``ArrayDatatype`` API is mostly classmethods, called on the class instead
of an instance.  PyOpenGL uses it throughout to handle a Python argument for a
particular array format.  The types defined are:

``ArrayDatatype``
    generic array operations.

``GLclampdArray``, ``GLclampfArray``
    clamped floating-point.

``GLfloatArray``, ``GLdoubleArray``
    unclamped floating-point.

``GLbyteArray``, ``GLcharArray`` (``GLcharARBArray``), ``GLubyteArray``
    character.

``GLshortArray``, ``GLintArray``, ``GLsizeiArray``, ``GLenumArray``
    integer.

New code inside PyOpenGL should go through the ``ArrayDatatype`` interfaces, so
that a generic operation dispatches to whichever format handler the caller's
data needs.

Format handlers
~~~~~~~~~~~~~~~

A format handler implements the API that ``ArrayDatatype`` calls.  It may
implement only the parts that apply to its type.  For example, a write-only
type such as a byte string does not need ``zeros``.  The handlers shipped are:

:py:mod:`nones.NoneHandler <OpenGL.arrays.nones>`
    passes ``None`` as an array pointer.  Registered as ``nones``.

:py:mod:`numpymodule.NumpyHandler <OpenGL.arrays.numpymodule>`
    the full handler for NumPy arrays, written in Python against a stable API.
    Registered as ``numpy``.

:py:mod:`numbers.NumberHandler <OpenGL.arrays.numbers>`
    a single Python int or float as a one-element array.  Input only, since
    single-value output arguments come back as arrays.  Registered as
    ``numbers``.

:py:mod:`strings.StringHandler <OpenGL.arrays.strings>`
    byte strings as a data source; input only.  Registered as ``strings``.

:py:mod:`ctypesarrays.CtypesArrayHandler <OpenGL.arrays.ctypesarrays>` and :py:mod:`ctypespointers.CtypesPointerHandler <OpenGL.arrays.ctypespointers>`
    ctypes arrays in full, ctypes pointers for input.  Registered as
    ``ctypesarrays`` and ``ctypespointers``.

:py:mod:`lists.ListHandler <OpenGL.arrays.lists>`
    Python lists and tuples, for use where NumPy is not installed.  Registered
    as ``lists``.

Registering a new format handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register a handler with :py:mod:`OpenGL.plugins`:

.. code-block:: python

   from OpenGL.plugins import FormatHandler
   FormatHandler('numpy', 'OpenGL.arrays.numpymodule.NumpyHandler', ['numpy.ndarray'])

The first argument names the plugin, the second is the class to load, and the
third, if given, is the list of ``module.classname`` values the handler claims.
A plugin registered without that third argument is loaded unconditionally.

The set of handlers is resolved at the first call that needs one.  Before that
call, an application can choose which handler builds output arrays, naming it
by its registered name.  The chosen handler must define ``zeros``:

.. code-block:: python

   from OpenGL.arrays import formathandler
   formathandler.FormatHandler.chooseOutput('ctypesarrays')

Image handling
--------------

Image data is array data, so the array handling above does most of the work.
The rest is OpenGL pixel-store state.  Python image libraries produce tightly
packed buffers, and OpenGL's default packing would read them wrongly.

:py:mod:`OpenGL.images` holds the functions and the tables that describe each
image format, for input and for output.  Registering a new image type means
adding to those tables.  :py:mod:`OpenGL.GL.images` implements the core image
entry points on top of that module, and is an example to follow.

Error handling
--------------

Each API has one error checker, an ``_ErrorChecker`` from
:py:mod:`OpenGL.error` built in ``OpenGL/raw/<API>/_errors.py``.  It names
the function that reads an error code (``glGetError``, ``eglGetError``), the
code that means success and the exception to raise.  The ctypes bindings call
the checker after each call.  ``OpenGL._dispatch.register_error_source`` hands
the same three values to the C dispatch layer, which makes the check itself.

The GL checker starts on ``glGetError``.  On the first check in each context,
``OpenGL.dispatch`` offers debug output: where the context offers
``GL_KHR_debug`` and has no callback of its own, it installs a debug callback
and calls the checker's ``setErrorReader`` with a function that reads the flag
the callback sets.  ``setErrorReader()`` with no argument goes
back to ``glGetError``.  :doc:`using` lists when a context stays on
``glGetError``.

``glBegin`` calls the checker's ``onBegin`` and ``glEnd`` its ``onEnd``.
Checking is suspended between the two, because ``glGetError`` cannot be called
inside a ``glBegin`` block.

:py:mod:`OpenGL.error` defines the errors raised; :py:exc:`ValueError` and
:py:exc:`TypeError` come from argument conversion.  The wrappers catch an
OpenGL error and annotate it with the arguments of the call that raised it.

Context-specific data
---------------------

A pointer passed to the driver needs the Python object behind it to stay
alive.  :py:mod:`OpenGL.contextdata` stores such objects against a key for the
current context, which the platform module's ``GetCurrentContext()``
provides.  A ``context`` argument of ``None`` means the current context.

.. code-block:: python

   def setValue(constant, value, context=None, weak=False):
       """Set a stored value for the given context"""

   def getValue(constant, context=None):
       """Get a stored value for the given constant"""

   def delValue(constant, context=None):
       """Delete the specified value for the given context"""

``getValue`` returns ``None`` where nothing is stored, and ``delValue``
returns whether there was a value to delete.  When a rendering context is
destroyed, clear each stored value, or call
:py:func:`OpenGL.contextdata.cleanupContext` to clear them all.

Extensions
----------

Most new OpenGL functionality appears as an extension before it reaches the
core, and hundreds of extensions are registered.  Most add constants and a few
entry points, and the generator handles them without help.

A few of the larger ones, such as :py:mod:`OpenGL.GL.ARB.shader_objects` and
:py:mod:`OpenGL.GL.ARB.vertex_buffer_object`, need hand-written code beyond
the generated code.  Those wrappers live under ``OpenGL.GL.*``, with the
generated API underneath them in ``OpenGL.raw.*``.

Running the tests and the gates
-------------------------------

.. code-block:: console

   $ pytest
   $ tox -e errorpaths

``tox.ini`` declares the environments CI runs, including the linting and
typing gates.  ``tests/`` has the suite.  The backends in :doc:`offscreen`
give it a context without a display.
