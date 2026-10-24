The C dispatch layer
====================

PyOpenGL has two implementations of the OpenGL entry points. The *C* implementation is generated from the Khronos registry and compiled into an extension module. It ships in ``PyOpenGL_accelerate`` and runs under CPython wherever that package is installed. The *ctypes* implementation is pure Python and needs nothing compiled. It runs everywhere else. Where the C implementation is available, an environment variable selects ctypes instead:

::

   PYOPENGL_DISPATCH=ctypes   python yourprogram.py

Both implement the same API. A call reaches the driver about seven times faster through the C implementation, and about eleven times faster when it passes an array. The figures below were measured on a GeForce RTX 3060 Ti with CPython 3.12 and ``PyOpenGL_accelerate`` installed.

======================================== ======= ======
call                                     ctypes  C
======================================== ======= ======
``glBindTexture(GL_TEXTURE_2D, 0)``      407 ns  58 ns
``glUniform1f(loc, 1.0)``                382 ns  51 ns
``glUniformMatrix4fv(loc, 1, False, m)`` 1184 ns 106 ns
an empty Python function, for scale      32 ns
======================================== ======= ======

These are per-call figures. A program gains in proportion to the share of its frame spent on dispatch. A program written for modern GL (shaders, vertex array objects, uniform buffers, instancing) issues few calls per frame. It spends its time in the driver and on the GPU, and optimised PyOpenGL applications measure about 5% faster. A program with many calls per frame approaches the table's ratios: immediate-mode drawing, a uniform set per object, or geometry pushed through client-side arrays every frame. A program between the two sees a gain between the two.

Where the C implementation comes from
-------------------------------------

The C dispatch is compiled, so it ships in a separate distribution, ``PyOpenGL_accelerate``:

::

   pip install PyOpenGL PyOpenGL_accelerate

``pip install PyOpenGL`` on its own gives the ctypes implementation on every platform. That is a complete PyOpenGL: both implementations are the same bindings with the same semantics. It is also what runs where no compiled wheel exists and no compiler is available to build one.

The extension is built for CPython only. Other interpreters reach CPython's vectorcall protocol through an emulation layer, where the C implementation would be slower than ctypes. ``PyOpenGL_accelerate`` does not build it there, and ctypes runs instead.

Keeping the pair matched
~~~~~~~~~~~~~~~~~~~~~~~~

The two distributions carry the same version number, and the versions must be equal. The extension's tables are generated from one ``PyOpenGL`` release, and their slot numbers mean nothing to another release. A mismatched pair dispatches through the wrong entry points. ``PyOpenGL_accelerate`` therefore requires the exact ``PyOpenGL`` it was released with, so a resolver cannot assemble a mismatched pair.

The requirement runs in one direction. Installing or upgrading ``PyOpenGL_accelerate`` brings the matching ``PyOpenGL`` with it. Upgrading ``PyOpenGL`` alone leaves the older accelerate installed, because an installer resolves only the packages it was asked for. pip reports the conflict after installing, and other installers may not report it at all. Name both packages whenever you upgrade either:

::

   pip install -U PyOpenGL PyOpenGL_accelerate

PyOpenGL refuses a mismatched pair when it builds the first entry point, with a message naming both versions. It checks two things. The C dispatch extension records the ``PyOpenGL`` version its tables were generated from, and that version must be equal. The older Cython accelerators (the wrapper, array-datatype and format-handler modules) follow PyOpenGL's internals and do not share its tables. They must meet a minimum version that moves with the major version. Setting ``PYOPENGL_USE_ACCELERATE=0`` in the environment runs on ctypes until the versions are fixed. It is read before the versions are compared, so it works inside a broken installation.

Selecting an implementation
---------------------------

``PYOPENGL_DISPATCH=c``
   The default on CPython, effective where ``PyOpenGL_accelerate`` is installed. Every entry point with a C implementation uses it. An entry point without one keeps its ctypes binding. The two coexist, so there is no per-function choice to make.
``PYOPENGL_DISPATCH=ctypes``
   The reference semantics, the bootstrap route for a new platform, and the default on every interpreter other than CPython. It runs with ``PyOpenGL`` alone, and there is no plan to remove it.

When the extension is absent, ``PYOPENGL_DISPATCH=c`` falls back to ctypes without an error. Two other settings select ctypes for the whole process. ``OpenGL.USE_ACCELERATE = False`` turns off every compiled accelerator. ``OpenGL.FULL_LOGGING`` needs ctypes because the ctypes wrapper chain writes the call trace.

Asking which one you got
~~~~~~~~~~~~~~~~~~~~~~~~

Requesting the C implementation and running without it is not an error. A program that requires the C dispatch must check, using ``OpenGL.dispatch``:

::

   >>> from OpenGL import dispatch
   >>> dispatch.requested()          # what the configuration asks for
   'c'
   >>> dispatch.active()             # what the entry points built so far use
   'c'
   >>> dispatch.status()
   Status(requested='c', active='c', available=True, reason=None)

``status().reason`` is a sentence naming what selected ctypes: an absent extension, ``USE_ACCELERATE``, ``FULL_LOGGING``, or an interpreter the extension is not built for. A program can include it in the error it raises:

::

   state = dispatch.status()
   if state.active != 'c':
       raise SystemExit('this program needs the C dispatch: %s' % state.reason)

The implementation is chosen when the first entry point is built. Until a process imports something from ``OpenGL.GL``, ``active()`` returns ``'ctypes'`` whatever the configuration. ``dispatch.settle()`` makes the choice immediately and returns it. Use it in a test suite, or in a program that must know before it has a context to draw with. It reads ``OpenGL.ERROR_CHECKING`` and the related flags as the first entry point would, so call it after setting them.

What is implemented in C
------------------------

4,859 of PyOpenGL's 4,880 bindings are implemented in C, across GL, GLES 1/2/3, GLSC2, GLX, WGL and EGL. This includes the families whose array length is computed from other values: images, sized from format, type, dimensions and the current pixel-store state; arrays whose element type is an argument, such as ``glDrawElements``; the client-side array pointers, whose memory the GL keeps after the call returns; and the string-array parameters. Image sizing stays in Python because ``OpenGL.images.registerImage`` is a public entry point that third parties use to add formats. The C code calls into it.

The remaining 21 keep their ctypes binding. ``python src/check_registry.py`` lists them with the reason for each:

-  12 return a pointer to a struct the binding has no element type for, mostly GLX and X11 (``XVisualInfo *``, ``GLXFBConfig *``, ``Display *``).
-  7 have an output argument that is not the last argument.
-  1 has a parameter type the generator does not know (``EGLnsecsANDROID``).
-  1 belongs to a hand-written family.

Contexts
--------

Under the C implementation, each OpenGL context holds its own function pointer for every entry point, resolved in that context. This matters when two contexts differ: a discrete-GPU context beside a software one, a core context beside a compatibility one, or GLES beside desktop GL. Under the ctypes implementation, the first context to resolve an entry point sets the binding for the whole process.

Two consequences are visible from Python. ``bool(glFoo)`` and ``glInitXxx()`` report on the current context, so the same expression can be true in one context and false in another. A binding held in a local variable across a context switch still dispatches correctly. The entry point object holds a slot index and does not store an address.

Knowing which context is current
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Applications make a context current through their windowing toolkit. glfw, Qt, pygame and SDL all call ``glXMakeCurrent`` or ``eglMakeCurrent`` themselves. PyOpenGL is not on that call path and is not told about the switch. Querying the driver instead costs about 97 ns per call on the reference machine, more than a whole dispatch.

By default, PyOpenGL re-reads the current context whenever an entry point needs resolving. Otherwise it assumes the context has not changed. The ctypes implementation holds one binding per process and cannot distinguish contexts at all. Under ctypes, a process with two contexts of differing capability is exposed on every entry point. Per-context tables reduce that exposure.

A program that switches between contexts of different capability, such as a discrete-GPU context and a software one, has two exact options:

-  ``PYOPENGL_CONTEXT_TRACKING=verify`` queries the driver on every call. The program needs no change. The cost is the 97 ns: about 177 ns per call instead of 58, compared with 383 for ctypes.
-  Call ``OpenGL.dispatch.make_current(handle)`` after each switch, with the handle that ``OpenGL.platform.PLATFORM.GetCurrentContext()`` returns. This is exact and costs nothing, and the program must make the call itself.

The handle takes whatever form names a context on the platform: an ``int`` from WGL or CGL, a ``c_void_p``, or a ctypes pointer such as GLX's ``GLXContext``. A toolkit can pass the object its own API returned. ``None`` or a null pointer means no context.

``OpenGL.dispatch.forget_context(handle)`` releases a destroyed context's table. A table holds a slot and a flag per entry point, about 43 KB, so a hundred live contexts use 4.3 MB.

``OpenGL.dispatch.context_identity()`` returns an object representing the current context. The object stays the same for the life of the context. It changes once ``forget_context`` has been called for that context, even if the driver reuses the handle for the next context. Buffers, textures and programs are numbered from 1 in each context, so a name kept after its context is gone refers to some other object in the next one. Store the identity with the name and compare it before using the name. ``OpenGL.arrays.vbo.VBO`` compares it before deleting its buffer at garbage collection, and otherwise leaves the buffer to its context. The identity is only as exact as the ``forget_context`` calls. A context destroyed without one and a new context at the same address share an identity.

A glBegin block and the life of a context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``glBegin`` block must be closed in the context that opened it. Creating or destroying a context while a block is open is undefined, and a driver may crash on the missing ``glEnd``. Intel's Windows ICD leaves state behind that makes the *next* context creation in the process fault. The access violation then appears far from the block that caused it.

An exception that escapes a block leaves it open, for example a bad vertex or an entry point the driver does not export. The exception-safe form is:

::

   glBegin(GL_POINTS)
   try:
       ...
   finally:
       glEnd()

``make_current`` and ``forget_context`` close an open block, which is a second reason to call them. PyOpenGL is *not* told when a context is created, because creation happens inside the toolkit. Call ``OpenGL.error.end_abandoned_block()`` before creating one. It closes any open block and returns whether there was one. ``OpenGL.error.inside_begin_block()`` returns whether a block is open without closing it. With ``PYOPENGL_ERROR_CHECKING=0``, PyOpenGL keeps no record of an open block and both return False. A program run that way must close its own blocks.

Arrays
------

The C implementation accepts every array argument the ctypes implementation accepts. A buffer whose element type already matches is used directly. Anything else is converted by ``ArrayDatatype`` exactly as under ctypes: a different dtype, a non-contiguous array, a list, ``bytes``, a ctypes object, a VBO, or an object from a ``FormatHandler`` you registered yourself. A type the C layer does not recognise is not an error. It takes the unaccelerated path.

Registering a new array type therefore needs no knowledge of this layer. A type registered against an older PyOpenGL keeps working.

A pass-in array of the wrong type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entry points that fill an array accept one you supply, and return it:

::

   names = glGenTextures(4)              # allocated for you
   glGenTextures(4, names)               # or filled in an array you own

Use the return value, because it may be a different object from the array you passed. When the array you pass already has the element type the call needs, the GL writes into it directly and the two are the same object. Otherwise (an ``int32`` array of four where ``uint32`` was wanted, or a list) the array is converted first. The GL writes into the converted copy, and *that* copy is returned. Your original is unchanged:

::

   a = numpy.zeros(4, 'int32')
   b = glGetFloatv(GL_COLOR_CLEAR_VALUE, a)
   # b holds the clear colour; a is still [0 0 0 0]

Both implementations behave this way. Much code passes a list or an array of a convenient type and reads the result from the return value, so this is not refused. Passing ``None`` or an array of the right type both get an array written in place.

Two cases are refused, because nothing usable would come back: a conversion that produced a *smaller* buffer than the one you passed, and an array too short for the number of elements the call was told to write. The second would let the driver write past the end of the array.

Strings
-------

Some entry points take several strings: ``glShaderSource``, ``glTransformFeedbackVaryings``, ``glGetUniformIndices``, ``glCreateShaderProgramv``, ``glCompileShaderIncludeARB`` and their ``ARB``/``EXT`` spellings. They are declared as an array of pointers to nul-terminated strings. They accept four forms:

::

   glShaderSource(shader, source)                  # one str
   glShaderSource(shader, source.encode())         # one bytes, or a bytearray
   glShaderSource(shader, [header, body])          # a list or tuple of any of those
   glShaderSource(shader, prepared_char_pp)        # a pointer array you built

A ``str`` is encoded as UTF-8. ``bytes`` and ``bytearray`` are passed as the bytes they hold. A single string counts as an array of one, the usual way to pass one shader source or one varying name. An item that is not a string is refused. Converting it would compile the text of a Python repr as GLSL, and the driver's error would name a shader line instead of the argument.

Both implementations accept the same forms, for every entry point in the list. ``OpenGL._string_array`` defines what counts as a string. The C layer calls back into it, and the ctypes bindings convert with it. The two differ only in the exception type for a refusal: ctypes wraps the conversion's exception in ``ctypes.ArgumentError``.

Some of these entry points also take the count, such as ``glTransformFeedbackVaryings(program, count, varyings, bufferMode)``. The driver reads ``count`` pointers. Fewer strings than the count, or ``None`` with a positive count, raises ``ValueError`` before the call. More strings than the count are accepted. A pointer array you built is passed unchanged, because only the caller knows its length. ``OpenGL.ARRAY_SIZE_CHECKING = False`` disables this check along with the other array-length checks.

``glGetUniformIndices`` takes the names the same way and derives the count from them. It returns a ``GLuint`` array with one index per name:

::

   indices = glGetUniformIndices(program, ['blockColor', 'blockEdge'])
   glGetUniformIndices(program, names, indices)    # or into an array you own
   glGetUniformIndices(program, uniformNames=names)    # by keyword
   glGetUniformIndices(program, 2, prepared_char_pp)   # or the C ordering

A name the program does not declare, or one its compiler removed, gets ``GL_INVALID_INDEX``. The C ordering (the count, then the names) is detected when the second argument is a count. It serves a caller who built the pointer array themselves, and the result array is allocated from the count. The names are required in either form. ``OpenGL.GL``, ``OpenGL.GL.ARB.uniform_buffer_object`` and ``OpenGL.GLES3`` provide the same function, because GL 3.1 adopted the extension and OpenGL ES 3.0 declares the same entry point.

Error checking
--------------

``OpenGL.ERROR_CHECKING`` is read when the layer is configured and applies per entry point, per context. The API's ``getError`` function is called from C without a Python callback, so checking costs the driver round trip only. ``OpenGL.dispatch.set_error_checking(enable, entry_point=None)`` changes the setting at run time, for one entry point or for all. The import-time flag cannot do that.

Each API has its own error function and its own success value, so the function called depends on the API the entry point belongs to:

+----------------------+-----------------+--------------------------+--------------+
| API                  | error function  | means success            | raises       |
+======================+=================+==========================+==============+
| GL, GLES1/2/3, GLSC2 | ``glGetError``  | ``GL_NO_ERROR`` (0)      | ``GLError``  |
+----------------------+-----------------+--------------------------+--------------+
| EGL                  | ``eglGetError`` | ``EGL_SUCCESS`` (0x3000) | ``EGLError`` |
+----------------------+-----------------+--------------------------+--------------+
| GLX, WGL             | nothing to poll | none                     | not checked  |
+----------------------+-----------------+--------------------------+--------------+

Each API states this once, in ``OpenGL/raw/<api>/_errors.py``, and both implementations read that file. The ctypes bindings call the checker it builds. ``register_error_source`` passes the same three facts to the compiled layer, which makes the call itself. A single ``glGetError`` for every API would miss all of EGL's errors. When a GL context happened to be current, it would also report a GL error against the next EGL call.

``GL_KHR_debug`` (below) and the error-checking suspension inside ``glBegin`` apply only to the GL family. Both are GL constructs. An EGL call is checked with ``eglGetError`` in every case.

Checking through GL_KHR_debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The driver round trip is the cost of error checking. When the context offers ``GL_KHR_debug``, the driver reports errors through a callback during the call. The check afterwards reads the flag that the callback set. PyOpenGL enables this on every context that offers the extension, under either implementation, without the program asking:

::

   >>> from OpenGL import dispatch
   >>> dispatch.error_checking_mode()
   'debug-output'

============================= ====
``glBindTexture``             ns
============================= ====
checking via ``glGetError``   48.9
checking via ``GL_KHR_debug`` 38.4
no checking at all            37.6
============================= ====

With the callback, checking costs 0.8 ns instead of 11 ns, so it can stay on without a speed penalty. The exception is the same ``GLError`` with the same ``err`` and ``baseOperation``, raised from the same call. It also carries ``description``, the driver's own message about the error, and ``debugMessageID``.

``GL_DEBUG_OUTPUT_SYNCHRONOUS`` is enabled with it. The callback must run during the call that caused the error, so the error is attributed to the right entry point. Non-error messages are not requested, so the driver does not spend time formatting them.

Turning it off
^^^^^^^^^^^^^^

``OpenGL.ERROR_DEBUG_OUTPUT = False``
   Set before the first call, for a program that does not want the driver in synchronous debug output at all. Checking uses the ``glGetError`` round trip.
``dispatch.use_debug_output(False)``
   Callable at any point, for the current context. It removes the callback and restores the driver state. PyOpenGL does not enable debug output on that context again.

A context that already has a debug callback keeps it. PyOpenGL checks for one before installing its own. If another component uses ``GL_KHR_debug``, the context stays on ``glGetError``. Replacing that callback would silence the program's own diagnostics, and the program's next ``glDebugMessageCallback`` would silence PyOpenGL's checking.

Checking the callback with glGetError
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A flag that is never set looks the same as a context with no errors. So a context checking this way also queries the driver once every 64 calls. If that query finds an error the callback never reported, the callback does not belong to this context. The context then switches to ``glGetError`` permanently.

The audit keeps the mechanism safe to leave on. The driver reuses context handles. A program that destroys a context without telling PyOpenGL can leave a table describing a context that no longer exists. A check that reads only the flag would then pass every call. The audit limits that to 64 calls and repairs it. A thread returning to a context it left audits on its first call back. The audit costs about a sixth of a nanosecond per call.

The ctypes implementation has no context handle to record until the program provides one. A context it enables before then is recorded as unnamed. That record is dropped when the program reports a change, through ``forget_context`` or a ``make_current`` naming a context. The context current afterwards may not be the one that was enabled. The next context is offered the mechanism again.

Calling ``dispatch.forget_context(handle)`` when a context is destroyed, and ``dispatch.make_current(handle)`` when one becomes current, is better than relying on the audit. Neither is required, and both help under either implementation.

Extensions that declare the same function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A command is often declared by more than one extension. ``GL_NV_gpu_shader5`` and ``GL_AMD_gpu_shader_int64`` both declare ``glUniform1i64NV``, and two KHR extensions declare each EGL sync entry point. A context advertising any one of them has the function, which is all resolution requires. ``proc.extension`` reports the single extension the entry point is recorded under.

A command may also be declared by a core version *and* by an extension. ``glGetPointerv`` is GL 1.1, and ``GL_KHR_debug`` re-specifies it to report a debug callback. Import order decides which declaration ``OpenGL.GL`` holds. It does not change where the entry point is looked up. This matters most on Windows, where ``opengl32`` exports GL 1.1 and nothing above it. ``wglGetProcAddress`` returns everything above GL 1.1, and NULL for the 1.1 set. PyOpenGL looks up each name in both.

Mesa's Windows ``osmesa`` library has the same split: the same export list, with ``OSMesaGetProcAddress`` for the rest. With ``PYOPENGL_PLATFORM=osmesa`` on Windows, PyOpenGL looks in the library and then through the lookup function. Each platform declares which lookup routes it has. Only a platform whose lookup function is a *query*, returning NULL for a name it does not have, uses this fallback. Under libglvnd, ``glXGetProcAddressARB`` returns a dispatch stub for any name at all. A Linux fallback would therefore report an entry point as present when the driver lacks it.

The driver's extension string does not decide it either. An extension that re-specifies a core entry point changes which arguments it takes. The entry point exists either way. Importing ``glGetPointerv`` from ``OpenGL.GL.KHR.debug`` therefore gives a working entry point on a driver that does not advertise ``GL_KHR_debug``. Apple's driver is one: it implements no GL version that includes it. The extension check is skipped only for a name a core version declares. macOS exports every entry point its framework implements, whether or not the current context supports it, so an extension that is absent is still reported absent.

Docstrings and introspection
----------------------------

Under the C implementation, entry points carry a docstring and a text signature. Under ctypes they have neither:

::

   >>> glBindTexture.__doc__
   'glBindTexture(target: GLenum, texture: GLuint) -> None'
   >>> glGenTextures.__doc__
   'glGenTextures(n: GLsizei) -> textures: GLuint[]'
   >>> inspect.signature(glGenTextures)
   <Signature (n, textures=None, /)>

The signature is built from the registry, so every entry point has one without an external documentation source. The types are the registry's own, such as ``GLenum`` and ``GLuint``, because callers make that distinction and the man pages use those names. An array argument is written ``GLfloat[]``, with one ``[]`` per level of indirection. The ``.pyi`` stubs beside the package give the same signatures in Python types, for type checkers.

What an editor sees
~~~~~~~~~~~~~~~~~~~

A friendly module (a public wrapper such as ``OpenGL.GL.ARB.vertex_array_object``) fills its namespace at import, from the same tables the entry points come from: ``_define(globals(), 'OpenGL.raw.GL.ARB.vertex_array_object')``. A tool reading the file cannot follow that call. Each module therefore ships a stub beside it listing what the import defines:

::

   OpenGL/GL/ARB/vertex_array_object.pyi

   GL_VERTEX_ARRAY_BINDING: int

   def glBindVertexArray(array: int) -> None: ...
   def glGenVertexArrays(n: int, arrays: UIntArray | None = None) -> UIntArrayResult: ...
   def glInitVertexArrayObjectARB() -> bool: ...

Completion on ``from OpenGL.GL.ARB import vertex_array_object`` therefore offers what that extension declares. A type checker sees the signatures instead of ``Any``. There are 1,299 stubs, generated from the module table in the same pass as the C, so a registry update regenerates them. The array aliases they use are defined in ``OpenGL/_typing.pyi``, a stub file with no module to import.

Threads
-------

A GL context is current in one thread at a time. The usual arrangement is one rendering thread, with other threads doing everything else. Two properties of the dispatch layer affect that arrangement.

Calls that can wait release the GIL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A call that waits on the driver releases the GIL while it waits, so the other threads in the process keep running. These calls include ``glFinish``, ``glReadPixels``, ``glClientWaitSync``, a shader compile, a buffer mapping, a swap under vsync, and a large texture or buffer upload. During a 4096×4096 ``glReadPixels`` taking 20 ms, a second thread runs several hundred times instead of once or twice.

Releasing the GIL costs 15 to 25 ns, against 57 ns for a whole ``glBindTexture``. It is therefore done only for calls that can block. ``src/cdispatch/blocking.py`` holds the list: 26 exact names and 19 family patterns, 244 entry points in total. The choice is made when the C is generated, with no test on each call. A call not on the list holds the GIL, which suits a call that returns in tens of nanoseconds.

Arguments converted for the call (the arrays, the strings, the buffers) are held by the calling frame while the GIL is released. Nothing the driver is reading from can be collected during the call.

Free-threaded builds
~~~~~~~~~~~~~~~~~~~~

The dispatch layer declares compatibility with the free-threaded builds of Python 3.13 and later (``Py_mod_gil``). Each call touches only its own context's table. A lock guards the registry of tables, and the configuration a call reads is set once at import. On a platform that cannot report the current context, two threads may share a table. They then race to write the same resolved address.

Importing PyOpenGL on a free-threaded build still re-enables the GIL. The dispatch layer ships in ``PyOpenGL_accelerate`` with that package's other compiled modules, and ``import OpenGL.GL`` loads six of them: ``errorchecker``, ``arraydatatype``, ``formathandler``, ``latebind``, ``wrapper`` and ``vbo``. None of the six declares free-threading compatibility. Each one turns the GIL back on as it loads, and the interpreter prints a warning:

::

   RuntimeWarning: The global interpreter lock (GIL) has been enabled to load
   module 'OpenGL_accelerate.errorchecker', which has not declared that it can
   run safely without the GIL.

Running ``PyOpenGL`` without ``PyOpenGL_accelerate`` keeps the GIL disabled, at ctypes speed. Having both needs those six modules audited for free-threaded safety and declared, and their current code does not support that. For example, ``LateBind`` resolves its target by writing an attribute on its first call. Two threads reaching that write together race on a reference count. Until those modules are audited, a free-threaded process gets either the GIL with the C dispatch or no GIL with ctypes.

Error-checking suspension inside ``glBegin`` is per thread under the C implementation. The ctypes implementation keeps the flag on a shared object, so one thread's ``glBegin`` block silences error checking for every thread.

Subinterpreters with their own GIL are refused at import. The layer keeps one set of context tables per process, so a second interpreter would share the first one's contexts.

What differs from the ctypes implementation
-------------------------------------------

These are the differences a program can observe. Everything else behaves identically, and the test suite runs under both implementations to check that.

+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| behaviour                                            | ctypes                                                                   | C                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+======================================================+==========================================================================+=========================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+
| ``type(glBindTexture)``                              | a ctypes function pointer, or ``_NullFunctionPointer``                   | ``GLProc``. An ``isinstance`` check against ``ctypes._CFuncPtr`` is the idiom most likely to be affected.                                                                                                                                                                                                                                                                                                                                                                               |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``repr(glBindTexture)``                              | ctypes' wording                                                          | ``<OpenGL entry point glBindTexture>``                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| exception message text for a bad argument            | ctypes' wording                                                          | PyOpenGL's own wording. The exception *type* is the same: ``ctypes.ArgumentError`` for a bad argument, ``NullFunctionError`` for an absent entry point.                                                                                                                                                                                                                                                                                                                                 |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``bool(glFoo)``, ``glInitXxx()``                     | resolved once, cached for the process                                    | evaluated for the current context                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| error checking suspended by ``glBegin``              | process-wide: one thread's block silences another thread's checking      | per thread                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``OpenGL.FULL_LOGGING``                              | logs every call                                                          | not implemented in C. Tracing selects the ctypes implementation for the process.                                                                                                                                                                                                                                                                                                                                                                                                        |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``glFoo.__doc__`` and ``inspect.signature(glFoo)``   | ``None``; ``signature()`` raises                                         | a signature line, and a Signature. Both are additions under C.                                                                                                                                                                                                                                                                                                                                                                                                                          |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``glFoo.extension`` for a command promoted into core | whichever declaration the namespace holds, which depends on import order | the core declaration. A command adopted into a GL version is declared twice: by the extension that introduced it and by the version that adopted it. ``proc.extension`` reports one of the two. Both implementations resolve the entry point either way. A name a core version declares is present whether or not the extension that re-specified it is advertised. Neither the declaration a caller imported nor the driver's extension string decides whether the entry point exists. |
+------------------------------------------------------+--------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

``tests/bindings/dispatch/test_attribute_surface.py`` surveys every entry point under both implementations in separate processes and compares the results. A difference not in the table above fails that test.

Ways out
~~~~~~~~

Assigning ``errcheck`` or ``argtypes`` to an entry point moves that entry point to the ctypes implementation for the life of the process. Debugging habits that use either keep working. Assigning ``restype`` the conversion the entry point already performs has no effect. Assigning a different ``restype`` also moves the entry point to ctypes. ``PYOPENGL_DISPATCH=ctypes`` switches everything else.

What is not implemented in C
----------------------------

GL, GLES 1/2/3, GLSC2, GLX, WGL and EGL are generated from the registry. GLU, GLUT, GLE and OSMesa are hand-maintained and the registry does not describe them, so there is no table to generate them from. They keep their ctypes bindings, about 210 entry points, none of them on a hot path.

Where the OpenGL.raw modules come from
--------------------------------------

The modules under ``OpenGL.raw`` hold only constants, entry-point declarations and re-exports. They are not shipped as files. A finder that PyOpenGL adds to ``sys.meta_path`` builds them on import from declaration tables, one per API: ``OpenGL/raw/_declarations/<API>.dat``. The tables describe 1,298 modules in 1.2 MB. As files, those modules would be 1,298 entries in the wheel. That accounts for most of the difference between a 4.0 MB wheel and a 2.9 MB one.

Nothing needs to be enabled, and importing code sees no difference: ``from OpenGL.raw.GL.VERSION.GL_1_1 import *`` works unchanged. A tool that inspects the module sees the tables. ``__spec__.origin`` is the table the definitions came from, and ``__file__`` names that table instead of a ``.py`` source.

Where the C extension is installed, the definitions are read from its own tables instead, which are already in memory. Both sets of tables are generated in one pass and describe the same modules.

Two kinds of module are real files. The packages have ``__init__.py`` files. The private modules (``_types``, ``_errors``, ``_glgets``) hold classes and conditionals, which have no table form.

There is no switch to turn this off. The files are not shipped and the generator does not write them, so these names resolve from the tables or not at all. ``tests/bindings/generated/test_virtual_modules.py`` holds the tables to what the files defined. It compares every constant and every signature against a recorded survey of the modules as files.

Regenerating and keeping up with the registry
---------------------------------------------

::

   python src/regenerate_c.py     # registry and shipped tree in, C out
   python src/check_registry.py   # what changed, and what needs a person

Maintaining or extending the generator is covered in ``src/cdispatch/README.md``: how the pipeline fits together, how to add an entry point that needs hand-written C, and how to add an array element type.

``check_registry.py`` reports registry commands with no binding, bindings whose signature no longer matches, enums with no constant, and every entry point still on the ctypes path with its reason. Known differences are recorded in ``src/cdispatch/registry_baseline.json``, each with a reason. The tool exits non-zero only for new differences, so it can drive a scheduled job.
