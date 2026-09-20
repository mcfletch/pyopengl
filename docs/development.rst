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

Both packages at once; :doc:`installation` says why.  Changes go in as pull
requests, with test cases wherever a case can be written.

Design goals
------------

Access to all of OpenGL
    OpenGL 1.1 through 4.x, OpenGL ES 1 through 3, and the registered
    extensions.

Compatibility with existing PyOpenGL code
    Most code should run unchanged and the rest with small changes, and the
    application programmer should be insulated from the implementation
    underneath so that code survives a change of it.

Playing well with others
    Alternative Python implementations, GUI libraries, numeric libraries,
    multimedia libraries, and whatever threading model the host program has
    chosen.

Robustness
    Degrading rather than failing where functionality is absent, reporting
    errors that name what went wrong, and being debuggable.

Ease of installation
    Portable to anywhere ctypes runs, installable with standard tooling, and
    extensible with new data types through plugins.

Platform abstraction
--------------------

PyOpenGL exposes the host platform's OpenGL to Python, and the differences
between platforms live in one place: porting to a new one is largely a matter
of writing a small module in the ``platform`` subpackage.

Each platform has its own
:py:class:`OpenGL.platform.baseplatform.BasePlatform` subclass, which provides:

- the library objects for GL, GLU, GLUT and GLE.  How the libraries are found,
  what they are called and what flags loading them needs are all
  platform-specific;
- the function type used to call into those libraries -- the calling
  convention, which is ``stdcall`` on Windows and ``cdecl`` elsewhere;
- ``GetCurrentContext()`` and ``CurrentContextIsValid()``, which the
  context-specific storage is keyed on;
- ``getExtensionProcedure(name)``, to resolve an extension entry point;
- ``getGLUTFontPointer(constant)``, since each platform represents a GLUT font
  differently;
- the flags ``HAS_DYNAMIC_EXT`` and ``EXT_DEFINES_PROTO``, saying whether the
  platform can load extensions dynamically and whether it defines prototypes;
- ``safeGetError()``, which reports OpenGL's error state where asking for it is
  safe -- a valid context, or a platform that tolerates the question without
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

Platform implementations are registered as entry points; ``sys.platform`` and
then ``os.name`` decide which one is loaded.

Generated bindings
------------------

Almost everything PyOpenGL exports is generated from the Khronos XML
registries rather than written out.  Two repositories, because Khronos
publishes them separately, and both are working copies rather than files
vendored here:

.. code-block:: console

   $ python src/fetch_registries.py

``src/khronosapi``
    `OpenGL-Registry <https://github.com/KhronosGroup/OpenGL-Registry>`__:
    ``gl.xml``, ``glx.xml``, ``wgl.xml``, and the extension specifications.

``src/eglapi``
    `EGL-Registry <https://github.com/KhronosGroup/EGL-Registry>`__:
    ``api/egl.xml``.

Which commit of each the shipped bindings came from is recorded in
``src/cdispatch/registry_lock.json``.  A fetch that finds a different one
stops the run: every enum value and every signature comes out of those
repositories, and no test can catch a wrong one, because the tests are
generated from the same input.  Moving to a newer registry is a decision with
a diff attached rather than whatever the network answered today, so it is
asked for:

.. code-block:: console

   $ python src/regenerate_c.py --update-registries

What the generators write
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ python src/regenerate_c.py      # the compiled entry points
   $ python src/xml_generate.py      # the Python-level API

``regenerate_c.py`` writes the C dispatch layer into
``accelerate/src/c/generated``, which is compiled into
``OpenGL_accelerate.dispatch``.  :doc:`c-dispatch` describes what that layer
does and ``src/cdispatch/README.md`` is the guide to the generator --
including how to add an entry point that needs hand-written C.

``xml_generate.py`` writes the Python-level API: the declaration tables in
``OpenGL/raw/_declarations/*.dat``, which a finder turns into the
``OpenGL.raw`` namespaces at import time, and the friendly modules beside
them.  There are no ``OpenGL.raw`` source files to read; the tables are what
there is.

``glGet`` output sizes are part of that: the generator registers each constant
against the size of the array it returns, so a ``glGet*`` call comes back the
right length.  The sizes come from the specifications together with
``src/glgetsizes.csv``.  Each extension module also gets the specification's
"Overview" as its docstring.

GLU, GLUT and GLE are not in the registries and are not generated; those
wrappers are written by hand, all three APIs being long settled.

Checking a regeneration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ python src/check_registry.py --verbose

Reports what the shipped bindings and the registry disagree about: a registry
command with no binding, a binding whose signature no longer matches, an enum
with no constant, and every entry point still on the ctypes path with the
reason.  Differences that have already been looked at are recorded in
``src/cdispatch/registry_baseline.json`` with a reason each, and
``--new-only`` exits non-zero for what is new since.

**A scheduled job already does this.**
``.github/workflows/registry-update.yml`` runs weekly: it fetches the
registries, regenerates, checks for drift nobody has recorded, and opens a
pull request when the regeneration produced a diff -- with the report in the
body, so the change can be read without checking anything out.  The registry
gains entry points continuously, and a gap in the bindings is otherwise only
noticed when somebody tries to call the thing that is missing.

So regenerating by hand is for working on a generator, not for keeping up with
Khronos.  An entry point whose generated body is not a plain macro expansion
is the one thing in that pull request that needs a person; the rest is table
data.

Customising a generated module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An extension module is a single file with its generated half above a marker:

.. code-block:: python

   ### DO NOT EDIT above the line "END AUTOGENERATED SECTION" below!
   ...
   ### END AUTOGENERATED SECTION

Customisations go below it.  Removing the marker takes the module out of the
generator's reach, and out of reach of later improvements to it as well.
Making an extension module more Pythonic and sending the change back is
welcome.

Converters and wrappers
-----------------------

Where the generated ctypes wrapper cannot be used as it stands, the entry point
is built from :py:class:`OpenGL.wrapper.Wrapper` and the converters in
:py:mod:`OpenGL.converters`.  ``Wrapper`` provides a set of argument
transformation stages, so that most entry points compose out of a small number
of simple operations -- explicitly specified, rather than matched by rule as a
SWIG-style generator would.

Where a custom function using raw ctypes is simpler, writing one and binding it
to the name works; the lazy wrapper below makes that easier.

The stages of a wrapped call are:

1. **pyConverters** -- accept or suppress an incoming Python argument.  A
   converter can convert an argument to the expected type, or remove it from
   the argument list entirely, which is how an argument implied by the shape of
   another one disappears.
2. **cConverters** -- look at the whole Python argument list and produce a
   one-to-one list of Python objects for the ctypes call.
3. **cResolvers** -- turn those into the low-level values ctypes passes.
4. the call itself, with error checking; an error is annotated with the
   arguments the call was made with.
5. **storeValues** -- keep alive anything the driver will read after the call
   returns, such as the array behind a pointer.
6. **returnValues** -- decide what the wrapped entry point gives back.

``Wrapper.setOutput`` builds an output array for a call from a size tuple, a
dictionary or a function.  :py:mod:`OpenGL.GL.glget` is full of examples.

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

Array operations are how a Python program pushes work into the OpenGL
implementation, so how naturally arrays are handled decides how fast the
binding is in practice.  NumPy is the array implementation PyOpenGL prefers.

The machinery is in :py:mod:`OpenGL.arrays`.  Two kinds of class do the work:
a :py:mod:`FormatHandler <OpenGL.arrays.formathandler>` knows how one Python
type stores its data, and an ``ArrayDatatype`` models one OpenGL array format.
``ArrayDatatype`` uses the format handlers to get at whatever the caller
passed.

ArrayDatatypes
~~~~~~~~~~~~~~

The ``ArrayDatatype`` API is made mostly of classmethods, called on the class
rather than on an instance, and is used throughout PyOpenGL to handle a Python
argument in a way specific to its array format.  The types defined are:

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

A format handler implements the API ``ArrayDatatype`` calls, and may implement
only the part that makes sense for its type: a write-only type such as a byte
string has no use for ``zeros``.  The handlers shipped are:

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

:py:mod:`OpenGL.plugins` takes the registration:

.. code-block:: python

   from OpenGL.plugins import FormatHandler
   FormatHandler('numpy', 'OpenGL.arrays.numpymodule.NumpyHandler', ['numpy.ndarray'])

The first argument names the plugin, the second is the class to load, and the
third, if given, is the list of ``module.classname`` values the handler claims.
A plugin registered without that third argument is loaded unconditionally.

The set of handlers is resolved at the first call that needs one, so until then
an application can say which handler should build output arrays -- that handler
has to define ``zeros``:

.. code-block:: python

   from OpenGL.arrays import formathandler
   formathandler.FormatHandler.chooseOutput('ctypesarrays')

naming the handler by its registered name.

Image handling
--------------

Image data is array data, so most of the work is the array handling above.
What is left is the OpenGL state: Python image libraries hand over tightly
packed buffers, and OpenGL's default packing would read them wrongly.

:py:mod:`OpenGL.images` holds the functions and the tables that describe each
image format, for input and for output.  Registering a new image type means
adding to those tables.  :py:mod:`OpenGL.GL.images` implements the core image
entry points on top of that module, and is the worked example.

Error handling
--------------

PyOpenGL runs :py:func:`OpenGL.error.glCheckError` after each call, and that
check is ``glBegin``/``glEnd``-aware, since ``glGetError`` reports nothing
between the two.  The checker can be replaced -- a program that always has a
valid context can register the raw ``glGetError`` and skip the context test:

.. code-block:: python

   from OpenGL import error
   error.ErrorChecker.registerChecker(myAlternateFunction)

:py:mod:`OpenGL.error` defines the errors raised; :py:exc:`ValueError` and
:py:exc:`TypeError` come out of argument conversion.  The wrappers catch an
OpenGL error and annotate it with the arguments of the call that raised it.

Context-specific data
---------------------

A pointer handed to the driver needs the Python object behind it to stay alive.
:py:mod:`OpenGL.contextdata` stores such objects against a key for the current
context, which the platform module's ``GetCurrentContext()`` provides.  A
``context`` argument of ``None`` means the current one.

.. code-block:: python

   def setValue(constant, value, context=None, weak=False):
       """Set a stored value for the given context"""

   def getValue(constant, context=None):
       """Get a stored value for the given constant"""

   def delValue(constant, context=None):
       """Delete the specified value for the given context"""

``getValue`` returns ``None`` where nothing is stored; ``delValue`` returns
whether there was a value to delete.  Destroying a rendering context means
clearing each stored value, or calling
:py:func:`OpenGL.contextdata.cleanupContext` for the lot.

Extensions
----------

Most new OpenGL functionality appears as an extension before it reaches the
core, and there are hundreds registered.  Most add constants and a few entry
points, and the generator handles them without help.

A few of the larger ones -- :py:mod:`OpenGL.GL.ARB.shader_objects`,
:py:mod:`OpenGL.GL.ARB.vertex_buffer_object` -- need hand-written code beyond
what the generator writes.  Those wrappers live under ``OpenGL.GL.*``, with the
generated API underneath them in ``OpenGL.raw.*``.

Running the tests and the gates
-------------------------------

.. code-block:: console

   $ pytest
   $ tox -e errorpaths

``tox.ini`` declares the environments CI runs, including the linting and typing
gates.  ``tests/`` has the suite; the backends in :doc:`offscreen` are how it gets a
context without a display.
