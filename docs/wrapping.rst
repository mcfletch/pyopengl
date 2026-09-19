How an OpenGL entry point becomes a Python function
===================================================

``glTexImage2D`` takes eleven arguments in C, nine in PyOpenGL, and works out the length of the last one from four of the others and from GL state the caller never mentions. Nothing about that is written down in one place: it is assembled from the Khronos registry, a generated declaration, an annotation that states what the Python signature does differently, and — for most entry points now — a C function generated from all three.

This page is the map. It is for the person debugging why a call raises something unexpected, and for the person adding an entry point or an argument convention and wondering where the change belongs.

The four things that make an entry point
----------------------------------------

+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| what                   | where                                                                                        | says                                                                                                                                                                                |
+========================+==============================================================================================+=====================================================================================================================================================================================+
| **the registry**       | ``src/khronosapi/xml/{gl,glx,wgl}.xml`` and ``src/eglapi/api/egl.xml``                       | The C signature, which feature or extension declares it, and ``COMPSIZE(...)``: how long an array argument is in terms of the other arguments.                                      |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the declaration**    | the generated ``OpenGL.raw`` tables                                                          | The ctypes signature — result type, argument types, argument names — and the extension string. Held in the C extension's ``.rodata`` and in ``OpenGL/raw/_declarations/<API>.dat``. |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the customisation**  | ``src/cdispatch/annotations.json``, shipped as ``OpenGL/raw/_declarations/_annotations.dat`` | What makes the Python signature differ from the C one: which arguments are outputs, which are sized from others, which are images.                                                  |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **the implementation** | ``accelerate/src/c/generated/pygl_<API>.c``, or ``OpenGL/wrapper.py``                        | The code that actually converts arguments, calls the driver and converts the result.                                                                                                |
+------------------------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The annotation table
--------------------

The customisations are written down as data, in ``src/cdispatch/annotations.json`` — 2,079 entries, keyed ``"<API>.<command>"``, with parameters keyed by name rather than by position, since a position moves when the registry adds an argument and a name does not:

::

   "GL.glTexImage2D": {
     "parameters": {
       "pixels": {"size": {"kind": "image", "format": "format",
                           "type": "type", "dimensions": ["width", "height"]}}}}

Of 4,880 commands, 2,801 are plain pass-throughs whose every fact is in the registry; the other 2,079 carry an annotation, and what it states exists nowhere else in machine-readable form. That is what the table is for.

Generation reads the registry, the declaration tables and this table. It does not read the friendly modules: a customisation chain is a second copy of what the table holds, and migrating a module deletes the chain, so anything only the chain held would go with it. ``tests/cdispatch/test_generation_is_data_driven.py`` holds generation to that, by emitting every stub from each source and comparing the C.

Twenty-eight modules still carry a chain, for customisations the table cannot express — a hand-written converter, a resolver, an image size computed from a format and a type together. While they remain, the two copies can be compared, and ``tests/cdispatch/test_annotation_wrapping.py`` does: applying the table has to produce the wrapper the chain produces, on the real entry points. A copy of the table ships as ``OpenGL/raw/_declarations/_annotations.dat``, because the pure-Python path needs it.

Rebuilding a customisation from the table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A parameter takes an array conversion when its **declared type is an array type**, or when the **table gives it a size spec**. The length comes from the table where there is one. Both halves are needed:

-  ``setInputArraySize('value', None)`` records no length, so the table holds nothing for it — but it installs ``ArrayDatatype.asArray``, and rebuilding from the table alone would drop the conversion and hand the driver a list. The declared type supplies it.
-  ``glDrawElements``, ``glColorPointer`` and ``glDrawPixels`` declare their array argument as ``ctypes.c_void_p``, because it may be a client pointer *or* an offset into a bound buffer. Array-ness is not in the type there; the table's ``typed-array`` and ``image`` kinds are what say so.

Reading the customisation
-------------------------

Under the ctypes implementation the difference between the C signature and the Python one is applied by a chain of calls on ``wrapper.wrapper``, built either from the table or, in the twenty-eight modules that still carry one, from the chain written in the module. There are only a handful of kinds, and each is one annotation:

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
| ``.setPyConverter('count')`` then ``.setCConverter('count', ...)`` | The argument is dropped from the Python signature and computed from another one.                                       | ``FromArg(index, divisor)``.                                                                |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``images.setImageInput(...)``                                      | The length is a function of format, type, the dimensions and the pixel-store state.                                    | ``ImageSize(format, type, dimensions)``, cross-checked against the registry's ``COMPSIZE``. |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+
| ``.setStoreValues(...)``                                           | The GL keeps reading the memory after the call returns, so the array must be held against the context.                 | ``Parameter.retain``.                                                                       |
+--------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------+

What a wrapper's Python call takes, after all of these, is ``wrapper.pyArgNames()``: the C argument names, less the ones a ``setPyConverter`` removed. It is the same whichever converters the configuration installed -- under ``ERROR_ON_COPY`` an array argument is passed through with none -- so it, rather than ``pyConverterNames``, which exists only once a converter has been set, is what to read a call from.

The table was built by parsing these chains, never by importing the modules, so extraction needs no GL context and no working build. It reads the registry as well, because the chains alone are not enough: ``images.py`` reaches ``glReadPixels`` through a differently-named wrapper, and only the registry's ``COMPSIZE(format,type,width,height)`` says what it really is. The parse still runs in the migration tooling and in the test that compares the two copies; it is no part of generating anything.

What runs when you call one
---------------------------

Under the C implementation, calling ``glTexImage2D(...)`` reaches a generated C function which, in order:

#. checks the argument count;
#. converts each scalar with the CPython C API;
#. for the image argument, calls back into ``OpenGL.images`` to compute the length — because ``OpenGL.images.registerImage`` is a public entry point a third party can add a format through, so the sizing cannot be frozen into C;
#. acquires a buffer over the array, taking the fast path when the element type already matches and falling through to ``ArrayDatatype`` and the format-handler registry when it does not;
#. loads the function pointer for the current context out of that context's dispatch table and calls it;
#. releases every buffer it acquired, on the failure paths as well as the successful one;
#. converts the result, and checks for an error if error checking is on.

Under the ctypes implementation the same steps happen, built at import time as a chain of Python objects by ``OpenGL/wrapper.py``. The two are meant to be indistinguishable from outside, and ``tests/test_attribute_surface.py`` compares every entry point's attributes under both to keep them so.

Where a call can go wrong, and what it means
--------------------------------------------

+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| symptom                                                           | usually means                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
+===================================================================+====================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+
| ``NullFunctionError``                                             | The entry point did not resolve, and the message says which of three reasons it was. *The library was not found on this machine* — every entry point in it is undefined, and the message names the library and where to get it; this is the usual answer for GLU, GLUT and GLE, which are separate packages on Linux. *No context is current* — every entry point above GL 1.1 is resolved through the context, so the call came before one was created. *The library does not export it* — a driver too old for it, or an extension this machine does not have. Check ``bool(glFoo)`` *with the context current*. |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``NoContext`` error                                               | ``OpenGL.CONTEXT_CHECKING`` is on and there was no current context. Off by default, because deleting objects from a cleanup handler after the context has gone is ordinary and silently harmless.                                                                                                                                                                                                                                                                                                                                                                                                                  |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| a ``GLError`` naming a call you did not make                      | Without ``GL_KHR_debug``, an error is attributed to whichever call next asks. Switch on ``OpenGL.dispatch.use_debug_output()`` to have the driver report the offending call itself.                                                                                                                                                                                                                                                                                                                                                                                                                                |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| an argument-count error mentioning more arguments than you passed | The entry point demoted to ctypes and lost a customisation. See below.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| wrong pixels, or a crash, from an image call                      | The pixel-store state at call time is part of the length calculation. ``glPixelStorei(GL_UNPACK_ALIGNMENT, ...)`` changes how much memory the driver reads.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
+-------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Asking whether an entry point is there
--------------------------------------

``bool(glFoo)`` answers whether calling ``glFoo`` will reach the driver, and it is the check to make before an optional call:

::

   if glDrawArraysInstanced:
       glDrawArraysInstanced(GL_TRIANGLES, 0, 3, count)
   else:
       ...draw them one at a time...

Asking resolves the entry point, so ask it *with the context current* — what a driver exports depends on the context, and a question asked before there is one can only be answered no. The answer is not remembered: an entry point that has nothing to resolve against now resolves once there is a context, and asking again is how you find out. Resolving is done once per entry point, so asking repeatedly costs nothing after the first yes.

A few entry points are Python-coded wrappers rather than bindings — ``glutInit`` collects ``argv`` before calling, for instance. They answer for the function they call, so the check reads the same whichever kind you have.

Demotion: when the C hands the call back
----------------------------------------

The C implements the entry point, not the friendly module's whole chain. If a friendly module applies a customisation the C does not perform — anything that changes which arguments the function takes — the entry point *demotes*: the ctypes binding is built, every customisation swallowed earlier is replayed onto it, and the result is what you would have had with no C layer at all. Correctness before speed.

This is why the ctypes binding still exists behind every C entry point. It is built on the first demotion that asks for it rather than at import, because a few dozen entry points out of nearly five thousand ever demote.

To see what an entry point is: ``type(glFoo)`` is ``GLProc`` where the C implements it, and something else where it does not. ``OpenGL/_dispatch/support.py`` holds the machinery — ``record_custom`` for what was swallowed, ``demote_and_call`` for the fallback.

Adding or changing an entry point
---------------------------------

#. **A new entry point from the registry.** Nothing to do by hand: pull the registry, run ``python src/regenerate_c.py``, and it appears. The weekly workflow in ``.github/workflows/registry-update.yml`` does this and opens a pull request when anything changed.
#. **A new argument convention** — a sizing rule no existing annotation describes. Add a size spec to ``src/cdispatch/model.py``, teach ``src/cdispatch/extract.py`` to recognise it, and add a macro to ``accelerate/src/c/pygl.h`` for the C to use. There is a test file per family in ``tests/cdispatch/``; write that first.
#. **An entry point needing real C** — one whose behaviour is not a description. Add it to ``src/cdispatch/handwritten.py`` and write the body in ``accelerate/src/c/pygl_handwritten.c``. ``glShaderSource`` is the worked example: its friendly form takes two arguments where the C entry point takes four, and the friendly module describes that by dropping the other two. Naming the friendly form's arguments in ``handwritten.py`` is what lets the C recognise such a description as a restatement of what it already does, and so keep the entry point rather than hand it back to ctypes.
#. **A new array element type.** One row in the element table and one ``ArrayDatatype`` subclass; no new C and no change to any stub.

Whatever the change, ``python src/check_registry.py`` reports what is not implemented in C and why, for every entry point, and fails on anything new since the recorded baseline. Nothing is on the ctypes path by accident.

Where the names come from
-------------------------

A friendly module no longer imports a generated module. It says:

::

   from OpenGL._declarations import define as _define
   _EXTENSION_NAME = _define(globals(), 'OpenGL.raw.GL.VERSION.GL_1_1')

and ``define`` writes the constants and entry points straight into the module's own namespace, from the C extension's tables where the C layer is in use and from ``OpenGL/raw/_declarations/<API>.dat`` otherwise. Both are written by the same generator pass, so they cannot drift. The string is the name the generated module had, and it stays the identifier for where a declaration came from.

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

The maintainer's guide to the generator is ``src/cdispatch/README.md``; the design record, including what was tried and measured, is ``plans/C-DISPATCH.md``. What the C layer covers and how it differs is :doc:`c-dispatch`.
