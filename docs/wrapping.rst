How an OpenGL entry point becomes a Python function
===================================================

``glTexImage2D`` takes eleven arguments in C and nine in PyOpenGL. PyOpenGL computes the length of the last one from four of the other arguments and from GL state the caller does not pass. That behaviour comes from four sources: the Khronos registry, a generated declaration, an annotation that states how the Python signature differs from the C one, and, for most entry points, a C function generated from all three.

This page describes where each of those parts lives and how they combine. It is for debugging a call that raises something unexpected, and for finding where to add an entry point or an argument convention.

The four things that make an entry point
----------------------------------------

+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| what                   | where                                                                                        | says                                                                                                                                                                                |
+========================+==============================================================================================+=====================================================================================================================================================================================+
| **the registry**       | ``src/khronosapi/xml/{gl,glx,wgl}.xml`` and ``src/eglapi/api/egl.xml``                       | The C signature, which feature or extension declares it, and ``COMPSIZE(...)``: how long an array argument is in terms of the other arguments.                                      |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the declaration**    | the generated ``OpenGL.raw`` tables                                                          | The ctypes signature (result type, argument types, argument names) and the extension string. Held in the C extension's ``.rodata`` and in ``OpenGL/raw/_declarations/<API>.dat``.   |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the customisation**  | ``src/cdispatch/annotations.json``, shipped as ``OpenGL/raw/_declarations/_annotations.dat`` | What makes the Python signature differ from the C one: which arguments are outputs, which are sized from others, which are images.                                                  |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the implementation** | ``accelerate/src/c/generated/pygl_<API>.c``, or ``OpenGL/wrapper.py``                        | The code that converts arguments, calls the driver and converts the result.                                                                                                         |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The annotation table
--------------------

The customisations are stored as data in ``src/cdispatch/annotations.json``. The file has 2,082 entries, keyed ``"<API>.<command>"``. Parameters are keyed by name instead of position, because a position moves when the registry adds an argument and a name does not:

::

   "GL.glTexImage2D": {
     "parameters": {
       "pixels": {"size": {"kind": "image", "format": "format",
                           "type": "type", "dimensions": ["width", "height"]}}}}

Of 4,880 commands, 2,798 are plain pass-throughs, fully described by the registry. The other 2,082 carry an annotation. The annotation is the only machine-readable record of what it states.

Generation reads the registry, the declaration tables and this table. It does not read the friendly modules. A customisation chain in a friendly module is a second copy of what the table holds. Migrating a module deletes its chain, so anything held only in the chain would be lost. ``tests/cdispatch/test_generation_is_data_driven.py`` checks that generation uses only the data, by emitting every stub from each source and comparing the C.

Twenty-eight modules carry a chain, for customisations the table cannot express: a hand-written converter, a resolver, or an image size computed from a format and a type together. For those modules the two copies can be compared. ``tests/cdispatch/test_annotation_wrapping.py`` compares them: applying the table must produce the same wrapper as the chain, on the real entry points. A copy of the table ships as ``OpenGL/raw/_declarations/_annotations.dat`` for the pure-Python path.

Rebuilding a customisation from the table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A parameter gets an array conversion when its declared type is an array type, or when the table gives it a size spec. The length comes from the table where the table has one. Both rules are needed:

-  ``setInputArraySize('value', None)`` records no length, so the table holds nothing for it. It does install ``ArrayDatatype.asArray``. Rebuilding from the table alone would drop that conversion and pass the driver a list, so the declared type supplies the conversion.
-  ``glDrawElements``, ``glColorPointer`` and ``glDrawPixels`` declare their array argument as ``ctypes.c_void_p``, because it may be a client pointer *or* an offset into a bound buffer. Their type does not mark them as arrays; the table's ``typed-array`` and ``image`` kinds do.

Reading the customisation
-------------------------

Under the ctypes implementation, a chain of calls on ``wrapper.wrapper`` applies the difference between the C signature and the Python one. The chain is built from the table, or, in the twenty-eight modules that carry one, from the chain written in the module. There are only a few kinds of call, and each corresponds to one annotation:

+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| call                                                               | means                                                                                                                  | generator sees                                                                              |
+====================================================================+========================================================================================================================+=============================================================================================+
| ``.setOutput('data', size)``                                       | The caller does not pass ``data``; it is allocated, filled by the driver and returned.                                 | ``Parameter.direction = OUT`` with a size spec.                                             |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setOutput('data', _glgets.GL_GET_SIZES)``                       | The length depends on which ``pname`` was asked for, through the 1,798-entry table in ``OpenGL/raw/<API>/_glgets.py``. | ``GLGetTable(pname_argument)``.                                                             |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setInputArraySize('v', 4)``                                     | The array must hold exactly four elements.                                                                             | ``Fixed(4)``.                                                                               |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setInputArraySize('v', None)``                                  | Any length; the caller is trusted.                                                                                     | ``NO_SIZE``.                                                                                |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setInputArrayCount('v', 'count', 4)``                           | The array must hold at least ``count * 4`` elements, which is what the driver reads; a longer one is accepted.         | ``FromArg(index, multiplier=4)``; the C uses ``PYGL_ARRAY_IN_MIN``.                         |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setInputArrayCount('varyings', 'count')`` on a ``char **``      | At least ``count`` strings, or a pointer array the caller built, which is passed unmeasured.                           | ``FromArg(index)``; the C uses ``PYGL_STRING_ARRAY_MIN``.                                   |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setPyConverter('count')`` then ``.setCConverter('count', ...)`` | The argument is dropped from the Python signature and computed from another one.                                       | ``FromArg(index, divisor)``.                                                                |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``images.setImageInput(...)``                                      | The length is a function of format, type, the dimensions and the pixel-store state.                                    | ``ImageSize(format, type, dimensions)``, cross-checked against the registry's ``COMPSIZE``. |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setStoreValues(...)``                                           | The GL keeps reading the memory after the call returns, so the array must be held against the context.                 | ``Parameter.retain``.                                                                       |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+

``wrapper.pyArgNames()`` lists the arguments a wrapper's Python call takes after all of these: the C argument names, minus those a ``setPyConverter`` removed. The list is the same whichever converters the configuration installed. For example, under ``ERROR_ON_COPY`` an array argument is passed through with no converter. Read a call's arguments from ``pyArgNames()``. ``pyConverterNames`` exists only once a converter has been set.

The table was built by parsing these chains, without importing the modules, so extraction needs no GL context and no working build. Extraction also reads the registry, because the chains are not enough on their own. For example, ``images.py`` reaches ``glReadPixels`` through a wrapper with a different name, and only the registry's ``COMPSIZE(format,type,width,height)`` identifies the entry point. The parser runs in the migration tooling and in the test that compares the two copies. Generation does not use it.

What runs when you call one
---------------------------

Under the C implementation, calling ``glTexImage2D(...)`` reaches a generated C function which, in order:

#. checks the argument count;
#. converts each scalar with the CPython C API;
#. for the image argument, calls back into ``OpenGL.images`` to compute the length. ``OpenGL.images.registerImage`` is a public entry point that lets a third party add a format, so the sizing cannot be fixed in C;
#. acquires a buffer over the array, taking the fast path when the element type already matches and falling through to ``ArrayDatatype`` and the format-handler registry when it does not;
#. loads the function pointer for the current context out of that context's dispatch table and calls it;
#. releases every buffer it acquired, on the failure paths as well as the successful one;
#. converts the result, and checks for an error if error checking is on.

Under the ctypes implementation, ``OpenGL/wrapper.py`` performs the same steps with a chain of Python objects built at import time. The two implementations are meant to behave identically from outside. ``tests/test_attribute_surface.py`` compares every entry point's attributes under both.

Where a call can go wrong, and what it means
--------------------------------------------

+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| symptom                                                           | usually means                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
+===================================================================+====================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+
| ``NullFunctionError``                                             | The entry point did not resolve. The message gives one of three reasons. *The library was not found on this machine*: every entry point in it is undefined, and the message names the library and where to get it. This is the usual cause for GLU, GLUT and GLE, which are separate packages on Linux. *No context is current*: every entry point above GL 1.1 is resolved through the context, so the call came before a context was created. *The library does not export it*: the driver is too old for it, or this machine lacks the extension. Check ``bool(glFoo)`` *with the context current*.             |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``NoContext`` error                                               | ``OpenGL.CONTEXT_CHECKING`` is on and there was no current context. The check is off by default, because cleanup handlers commonly delete objects after the context is gone, and that does no harm.                                                                                                                                                                                                                                                                                                                                                                                                                |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| a ``GLError`` naming a call you did not make                      | Without ``GL_KHR_debug``, an error is reported by the next call that checks for errors. Switch on ``OpenGL.dispatch.use_debug_output()`` to have the driver report the call that caused it.                                                                                                                                                                                                                                                                                                                                                                                                                        |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| an argument-count error mentioning more arguments than you passed | The entry point demoted to ctypes and lost a customisation. See the demotion section below.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| wrong pixels, or a crash, from an image call                      | The pixel-store state at call time is part of the length calculation. ``glPixelStorei(GL_UNPACK_ALIGNMENT, ...)`` changes how much memory the driver reads.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Asking whether an entry point is there
--------------------------------------

``bool(glFoo)`` is true when calling ``glFoo`` will reach the driver. Check it before an optional call:

::

   if glDrawArraysInstanced:
       glDrawArraysInstanced(GL_TRIANGLES, 0, 3, count)
   else:
       ...draw them one at a time...

The check resolves the entry point, so make it *with the context current*. What a driver exports depends on the context, and a check made before there is a context is always false. A false result is not cached: an entry point that cannot resolve without a context resolves once there is one, so check again after creating the context. Each entry point is resolved once, so repeated checks cost nothing after the first true result.

A few entry points are Python wrappers instead of bindings. For example, ``glutInit`` collects ``argv`` before calling. ``bool()`` on such a wrapper reports on the function it calls, so the check is the same for both kinds.

Demotion to ctypes
------------------

The C layer implements the entry point itself. It does not implement the friendly module's whole customisation chain. When a friendly module applies a customisation the C already performs, the C *swallows* it: the call is recorded and the entry point stays in C. When a friendly module applies a customisation the C does not perform (anything that changes which arguments the function takes), the entry point *demotes*. PyOpenGL builds the ctypes binding and replays onto it every customisation the chain swallowed earlier. The result is what you would have had with no C layer at all. The ctypes path is slower, and it applies every customisation.

Each chain records what it swallowed. The first swallowed call on a chain returns a separate ``GLProc`` for that chain. That ``GLProc`` dispatches through the same slot as the entry point, and holds the record that the chain replays if it demotes. For example, ``OpenGL.GL.pointers`` builds ``glColorPointerd`` and ``glColorPointerf`` from the one ``glColorPointer``, each with its own array converter. Each demotes to a wrapper carrying its own converter, in whatever order the chains are built. The ``glColorPointer`` that ``OpenGL.GL`` exports is such a chain, so assigning ``errcheck`` to it demotes it to a wrapper with its customisations. The entry point that ``OpenGL.raw`` exports carries none, and demotes to the plain binding.

A chain must use the value each call returns, as every friendly module does: ``glFoo = wrapper.wrapper(glFoo).setPyConverter(...)``. If a call is made only for its side effect and its return value is discarded, the customisation is recorded on a chain that is then dropped.

Demotion needs a ctypes binding behind every C entry point. The binding is built on the first demotion that needs it, instead of at import, because only a few dozen of nearly five thousand entry points ever demote.

``type(glFoo)`` is ``GLProc`` where the C implements the entry point, and another type where it does not. ``OpenGL/_dispatch/support.py`` holds the machinery: ``record_custom`` records a swallowed call on its chain, and ``demote_and_call`` implements the fallback.

Adding or changing an entry point
---------------------------------

#. A new entry point from the registry - nothing to do by hand. Pull the registry, run ``python src/regenerate_c.py``, and the entry point appears. The weekly workflow in ``.github/workflows/registry-update.yml`` does this and opens a pull request when anything changed.
#. A new argument convention (a sizing rule no existing annotation describes) - add a size spec to ``src/cdispatch/model.py``, extend ``src/cdispatch/extract.py`` to recognise it, and add a macro to ``accelerate/src/c/pygl.h`` for the generated C to use. ``tests/cdispatch/`` has a test file per family; write the test first.
#. An entry point that needs hand-written C (one whose behaviour an annotation cannot describe) - add it to ``src/cdispatch/handwritten.py`` and write the body in ``accelerate/src/c/pygl_handwritten.c``. ``glShaderSource`` is an example. Its friendly form takes two arguments where the C entry point takes four, and the friendly module describes that by dropping the other two. ``handwritten.py`` names the friendly form's arguments, so the C can recognise that customisation as one it already performs. The entry point then stays in C instead of demoting to ctypes.
#. A new array element type - one row in the element table and one ``ArrayDatatype`` subclass. It needs no new C and no change to any stub.

For any change, ``python src/check_registry.py`` reports every entry point not implemented in C, with the reason. It fails on anything new since the recorded baseline, so every entry point on the ctypes path has a recorded reason.

Where the names come from
-------------------------

A friendly module does not import a generated module. It contains:

::

   from OpenGL._declarations import define as _define
   _EXTENSION_NAME = _define(globals(), 'OpenGL.raw.GL.VERSION.GL_1_1')

``define`` writes the constants and entry points directly into the module's namespace. It reads them from the C extension's tables when the C layer is in use, and from ``OpenGL/raw/_declarations/<API>.dat`` otherwise. The same generator pass writes both sources, so they cannot drift apart. The string argument is a generated-module name, and it identifies where a declaration came from.

The files
---------

+-------------------------------------+------------------------------------------------------------------------+
| file                                | holds                                                                  |
+=====================================+========================================================================+
| ``src/fetch_registries.py``         | Fetching both Khronos registries; run first by ``regenerate_c.py``.    |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/extract.py``        | Reading the shipped tree and the registries into command records.      |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/annotations.py``    | The customisations as data, and the round trip that checks them.       |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/eglgen.py``         | Bindings for what the EGL registry declares and the tree lacks.        |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/model.py``          | The command record: one field per thing that can be emitted.           |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/emit_c.py``         | Turning a record into a C function, and deciding when it cannot.       |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/modules.py``        | What each generated module declared, for the tables and the data file. |
+-------------------------------------+------------------------------------------------------------------------+
| ``src/cdispatch/handwritten.py``    | The entry points whose C is written by a person.                       |
+-------------------------------------+------------------------------------------------------------------------+
| ``accelerate/src/c/pygl.h``         | The macro vocabulary every generated stub is written in.               |
+-------------------------------------+------------------------------------------------------------------------+
| ``accelerate/src/c/pygl_runtime.c`` | Dispatch tables, buffer acquisition, image and array helpers.          |
+-------------------------------------+------------------------------------------------------------------------+
| ``OpenGL/_declarations.py``         | Filling a friendly module's namespace from either source.              |
+-------------------------------------+------------------------------------------------------------------------+
| ``OpenGL/_dispatch/support.py``     | Resolution, demotion, and what the C calls back into.                  |
+-------------------------------------+------------------------------------------------------------------------+
| ``OpenGL/wrapper.py``               | The ctypes implementation of everything above.                         |
+-------------------------------------+------------------------------------------------------------------------+

``src/cdispatch/README.md`` is the maintainer's guide to the generator. ``plans/C-DISPATCH.md`` is the design record, including what was tried and measured. :doc:`c-dispatch` describes what the C layer covers and how it differs.
