The C dispatch layer
====================

PyOpenGL has two implementations of the OpenGL entry points. The *C* implementation is generated from the Khronos registry and compiled into an extension module; it ships in ``PyOpenGL_accelerate``, and it is what runs where that package is installed under CPython. The *ctypes* implementation is pure Python, needs nothing compiled, and is what runs otherwise. Where the C implementation is available, an environment variable selects the ctypes one instead:

::

   PYOPENGL_DISPATCH=ctypes   python yourprogram.py

Both implement the same API. A call reaches the driver about seven times faster through the C implementation, and about eleven times faster for a call that passes an array; the numbers below are on a GeForce RTX 3060 Ti with CPython 3.12 and ``OpenGL_accelerate`` installed.

======================================== ======= ======
call                                     ctypes  C
======================================== ======= ======
``glBindTexture(GL_TEXTURE_2D, 0)``      407 ns  58 ns
``glUniform1f(loc, 1.0)``                382 ns  51 ns
``glUniformMatrix4fv(loc, 1, False, m)`` 1184 ns 106 ns
an empty Python function, for scale      32 ns   
======================================== ======= ======

Those are per-call figures, and a program gains from them in proportion to how much of its frame goes on dispatch. A program structured around modern GL — shaders, vertex array objects, uniform buffers, instancing — issues few calls per frame and spends its time in the driver and on the GPU: measured uplift on optimised PyOpenGL applications is about 5%. The table's ratios are what a program approaches as its calls per frame rise — immediate-mode drawing, a uniform set per object, geometry pushed through the client-side arrays every frame — and a program between the two sees a figure between the two.

Where the C implementation comes from
-------------------------------------

The C dispatch is compiled, so it ships in the ``PyOpenGL_accelerate`` distribution rather than in ``PyOpenGL`` itself:

::

   pip install PyOpenGL PyOpenGL_accelerate

``pip install PyOpenGL`` on its own gives the ctypes implementation, on every platform. That is a working PyOpenGL — the two implementations are the same bindings with the same semantics — and it is what runs where no compiled wheel is available and where there is no compiler to build one.

The extension is built for CPython only. Another interpreter reaches CPython's vectorcall protocol through an emulation layer, where the C implementation would be slower than ctypes, so ``PyOpenGL_accelerate`` does not build it there and ctypes is what runs.

Keeping the pair matched
~~~~~~~~~~~~~~~~~~~~~~~~

The two distributions carry the same version number and have to be equal. The extension's tables are generated from a particular ``PyOpenGL``, and the slot numbering in one release is meaningless to another, so a mismatched pair does not degrade — it dispatches through the wrong entry points. ``PyOpenGL_accelerate`` therefore requires the exact ``PyOpenGL`` it was released with, which is what stops a resolver assembling such a pair in the first place.

That constraint travels in one direction only. Installing or upgrading ``PyOpenGL_accelerate`` brings the matching ``PyOpenGL`` with it; upgrading ``PyOpenGL`` on its own leaves the older accelerate installed, since an installer resolves what it was asked for rather than what is already there. pip reports that as a conflict after it has installed, and other installers may not report it at all, so name both packages whenever you upgrade either:

::

   pip install -U PyOpenGL PyOpenGL_accelerate

A pair that has come apart is refused when the first entry point is built, in a message naming both versions. Two things are checked: the C dispatch extension states the ``PyOpenGL`` its tables were generated from and is held to equality with it, and the older Cython accelerators — the wrapper, array-datatype and format-handler modules, which follow PyOpenGL's internals rather than sharing its tables — are held to a floor that moves with the major version. ``PYOPENGL_USE_ACCELERATE=0`` in the environment runs on ctypes until the versions are put right, and is read before the pair is judged so that it works from inside a broken installation.

Selecting an implementation
---------------------------

``PYOPENGL_DISPATCH=c``
   The default on CPython, taking effect where ``PyOpenGL_accelerate`` is installed. Every entry point that has a C implementation uses it; one that does not keeps its ctypes binding, so the two coexist and you never have to choose per function.
``PYOPENGL_DISPATCH=ctypes``
   The reference semantics, the bootstrap route for a new platform, and the default on every interpreter other than CPython. It is what runs with ``PyOpenGL`` alone, and it is not scheduled for removal.

With the extension absent, ``PYOPENGL_DISPATCH=c`` leaves the ctypes implementation in place rather than failing. Two other settings select ctypes for the process: ``OpenGL.USE_ACCELERATE = False``, which turns off every compiled accelerator, and ``OpenGL.FULL_LOGGING``, since the call trace is written by the ctypes wrapper chain.

Asking which one you got
~~~~~~~~~~~~~~~~~~~~~~~~

Since asking for the C implementation and running without it is not an error, a program that means to be on it has to ask. ``OpenGL.dispatch`` is where:

::

   >>> from OpenGL import dispatch
   >>> dispatch.requested()          # what the configuration asks for
   'c'
   >>> dispatch.active()             # what the entry points built so far use
   'c'
   >>> dispatch.status()
   Status(requested='c', active='c', available=True, reason=None)

``status().reason`` is a sentence naming whatever chose ctypes — an absent extension, ``USE_ACCELERATE``, ``FULL_LOGGING``, an interpreter the extension is not built for — so a program can put it in the error it raises:

::

   state = dispatch.status()
   if state.active != 'c':
       raise SystemExit('this program needs the C dispatch: %s' % state.reason)

The choice is made when the first entry point is built, so ``active()`` answers ``'ctypes'`` in a process that has imported nothing from ``OpenGL.GL`` yet, however it is configured. ``dispatch.settle()`` makes the choice rather than reporting it, for a test suite or a program that has to know before it has anything to draw with. It reads ``OpenGL.ERROR_CHECKING`` and its neighbours as the first entry point would, so call it after setting them.

What is implemented in C
------------------------

4,859 of PyOpenGL's 4,880 bindings, across GL, GLES 1/2/3, GLSC2, GLX, WGL and EGL. That includes the families whose length is a computation rather than a description — images, sized from format, type, dimensions and the current pixel-store state; arrays whose element type is an argument, such as ``glDrawElements``; the client-side array pointers, whose memory the GL keeps after the call returns; and the string-array parameters. The image sizing itself stays in Python, because ``OpenGL.images.registerImage`` is a public entry point a third party can add a format through, and the C calls it.

The remaining twenty-one keep their ctypes binding, and ``python src/check_registry.py`` lists them with the reason for each: twelve that return a pointer to a struct the binding has no element type for (mostly GLX and X11 — ``XVisualInfo *``, ``GLXFBConfig *``, ``Display *``), seven whose output argument is not the last one, one with a parameter type the generator does not know (``EGLnsecsANDROID``), and one whose family is hand-written.

Contexts
--------

Under the C implementation each OpenGL context holds its own function pointer for every entry point, resolved in that context. This matters where two contexts differ: a discrete-GPU context beside a software one, a core context beside a compatibility one, or GLES beside desktop GL. Under the ctypes implementation whichever context resolved an entry point first determines the binding for the whole process.

Two consequences reach the Python surface. ``bool(glFoo)`` and ``glInitXxx()`` answer for the context that is current, so the same expression can correctly be true in one context and false in another. And a binding held in a local variable across a context switch still dispatches correctly, because the entry point object holds a slot index rather than an address.

Knowing which context is current
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An application makes a context current inside its windowing toolkit — glfw, Qt, pygame and SDL all call ``glXMakeCurrent`` or ``eglMakeCurrent`` themselves — and PyOpenGL is not on that call path, so it cannot observe the switch. Asking the driver instead costs about 97 ns per call on the reference machine, more than a whole dispatch.

The default therefore re-reads the current context whenever an entry point needs resolving, and otherwise assumes it has not changed. The ctypes implementation holds one binding per process and cannot tell contexts apart at all, so under it a process with two contexts of differing capability is exposed on every entry point; per-context tables narrow that rather than widening it.

Where it matters — a program that switches between contexts of genuinely different capability, such as a discrete-GPU context beside a software one — there are two ways to be exact:

-  ``PYOPENGL_CONTEXT_TRACKING=verify`` asks the driver on every call. Nothing to change in the program, and it costs the 97 ns: about 177 ns per call rather than 58, against 383 for ctypes.
-  ``OpenGL.dispatch.make_current(handle)`` after each switch, with the handle ``OpenGL.platform.PLATFORM.GetCurrentContext()`` returns. Exact and free, for a program willing to say so.

The handle goes in whichever shape names a context on the platform: an ``int`` from WGL or CGL, a ``c_void_p``, or a ctypes pointer such as GLX's ``GLXContext``. A toolkit that holds the object its own API handed it passes that object; ``None`` or a null pointer names no context.

``OpenGL.dispatch.forget_context(handle)`` releases a destroyed context's table. A table is a slot and a flag per entry point, about 43 KB, so a hundred live contexts cost 4.3 MB.

``OpenGL.dispatch.context_identity()`` answers an object standing for the current context: the same object for as long as the context lives, and a different one once ``forget_context`` has been told it is gone, even where the driver gives the next context the same handle. Buffers, textures and programs are numbered per context from 1, so a name kept past its context is, in the next one, some other object; keep the identity beside the name and compare before using it. ``OpenGL.arrays.vbo.VBO`` does this before it deletes its buffer when it is garbage-collected, and leaves the buffer to its context otherwise. It is as exact as ``forget_context`` is told: a context destroyed without it, and another made at the same address, share an identity.

A glBegin block and the life of a context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``glBegin`` block is closed in the context that opened it. A context created or destroyed while one is still open is undefined, and a driver need not survive being denied the ``glEnd``: Intel's Windows ICD leaves state that the *next* context creation in the process faults on, so the access violation arrives with nothing near it to name the block that caused it.

A block is left open when an exception escapes it — a bad vertex, an entry point the driver does not export — which is why the exception-safe form is:

::

   glBegin(GL_POINTS)
   try:
       ...
   finally:
       glEnd()

``make_current`` and ``forget_context`` close such a block for you, so the two notifications above are worth making for this reason as well as for the tables. For the change PyOpenGL is *not* told about — creating a context, which happens inside the toolkit — call ``OpenGL.error.end_abandoned_block()`` first; it answers whether there was one. ``OpenGL.error.inside_begin_block()`` asks without closing anything. With ``PYOPENGL_ERROR_CHECKING=0`` there is no record that a block was opened and both answer False, so a program built that way closes its own.

Arrays
------

Nothing you can pass today stops being accepted. Where an array is wanted, a buffer whose element type already matches is used directly; anything else — a different dtype, a non-contiguous array, a list, ``bytes``, a ctypes object, a VBO, an object from a ``FormatHandler`` you registered yourself — is converted by ``ArrayDatatype`` exactly as it is today. A type the C layer does not recognise is not an error; it is simply not accelerated.

Registering a new array type therefore needs no knowledge of this layer, and a type registered against an older PyOpenGL keeps working. Acceleration is optional; acceptance is not.

A pass-in array of the wrong type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entry points that fill an array take one you supply, and hand it back:

::

   names = glGenTextures(4)              # allocated for you
   glGenTextures(4, names)               # or filled in an array you own

**Read the return value, not the array you passed.** Where the array you pass already has the element type the call wants, the GL writes directly into it and the two are the same object. Where it does not — an ``int32`` array of four where ``uint32`` was wanted, or a list — the array is converted first, the GL writes into the converted copy, and *that* is what comes back. Your original is left as it was:

::

   a = numpy.zeros(4, 'int32')
   b = glGetFloatv(GL_COLOR_CLEAR_VALUE, a)
   # b holds the clear colour; a is still [0 0 0 0]

Passing an array means this in both implementations, and a great deal of code relies on being able to pass a list or an array of a convenient type and read the result from the return value. So it is not refused. Passing ``None``, or an array of the right type, are both ways to get an array written in place.

Two cases are refused, because in them nothing usable comes back at all: a conversion that produced a *smaller* buffer than you passed, and an array too short for the number of elements the call was told to write — which would otherwise let the driver write past the end of it.

Strings
-------

The entry points that take several strings — ``glShaderSource``, ``glTransformFeedbackVaryings``, ``glGetUniformIndices``, ``glCreateShaderProgramv``, ``glCompileShaderIncludeARB`` and their ``ARB``/``EXT`` spellings — are declared as an array of pointers to nul-terminated strings. Four forms are accepted for one:

::

   glShaderSource(shader, source)                  # one str
   glShaderSource(shader, source.encode())         # one bytes, or a bytearray
   glShaderSource(shader, [header, body])          # a list or tuple of any of those
   glShaderSource(shader, prepared_char_pp)        # a pointer array you built

A ``str`` is encoded as UTF-8; ``bytes`` and ``bytearray`` are taken as the bytes they hold. One string on its own is an array of one, which is how a single shader source or a single varying name is usually passed. An item that is not a string is refused — rendering it would compile the text of a Python repr as GLSL, and the error the driver then reports names a line of the shader rather than the argument.

The same forms are accepted under both implementations, and by every entry point in the list. What counts as a string is decided in one place, ``OpenGL._string_array``, which the C layer calls back into and the ctypes bindings convert with; the two differ only in which exception carries a refusal, since ctypes wraps what a conversion raises in ``ctypes.ArgumentError``.

Error checking
--------------

``OpenGL.ERROR_CHECKING`` is read when the layer is configured and applies per entry point per context. The API's ``getError`` is called from C rather than through a Python callback, so checking costs the driver round trip and nothing else. ``OpenGL.dispatch.set_error_checking(enable, entry_point=None)`` changes it at run time, for one entry point or for all — which the import-time flag cannot do.

Which function is asked is a property of the API the entry point belongs to, because the APIs do not agree on the question or on the answer:

+----------------------+-----------------+--------------------------+--------------+
| API                  | asked           | means success            | raises       |
+======================+=================+==========================+==============+
| GL, GLES1/2/3, GLSC2 | ``glGetError``  | ``GL_NO_ERROR`` (0)      | ``GLError``  |
+----------------------+-----------------+--------------------------+--------------+
| EGL                  | ``eglGetError`` | ``EGL_SUCCESS`` (0x3000) | ``EGLError`` |
+----------------------+-----------------+--------------------------+--------------+
| GLX, WGL             | nothing to poll | —                        | not checked  |
+----------------------+-----------------+--------------------------+--------------+

Each API states this once, in ``OpenGL/raw/<api>/_errors.py``, and both implementations read that statement: the ctypes bindings call the checker it builds, and ``register_error_source`` hands the same three facts to the compiled layer, which does the call itself. A single ``glGetError`` answering for all of them would report none of EGL's errors, and where a GL context happened to be current would report a GL error against whichever EGL call asked next.

``GL_KHR_debug`` below, and the suspension ``glBegin`` performs, apply to the GL family alone: both are GL constructs, and an EGL call is checked by asking EGL either way.

Checking through GL_KHR_debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The round trip *is* the cost of error checking. Where the context offers ``GL_KHR_debug``, the driver reports an error through a callback during the call instead, and the check afterwards is a read of the flag that callback set. **A context that offers it is given it**, under either implementation, without the program asking:

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

Checking costs 0.8 ns rather than 11 ns, so leaving it on is not a trade against speed. The exception is the same ``GLError`` with the same ``err`` and the same ``baseOperation``, raised from the same call; what is added is ``description``, the driver's own account of what was wrong, and ``debugMessageID``.

``GL_DEBUG_OUTPUT_SYNCHRONOUS`` is turned on with it, because the callback has to run during the call it belongs to for the error to be attributed to the right entry point. Messages that are not errors are not requested, so the driver does not spend time formatting them.

Turning it off
^^^^^^^^^^^^^^

``OpenGL.ERROR_DEBUG_OUTPUT = False``
   Before the first call, for a program that does not want the driver put into synchronous debug output at all. Checking stays the ``glGetError`` round trip.
``dispatch.use_debug_output(False)``
   At any point, for the current context: the callback is removed and the driver state undone. A context a program has spoken for is left alone afterwards.

A context that already has a debug callback installed keeps it: PyOpenGL looks before it installs, and where somebody else is using ``GL_KHR_debug`` the context stays on ``glGetError``. Taking that callback over would silence the program's own diagnostics, and its next ``glDebugMessageCallback`` would silence PyOpenGL's checking.

Why it audits itself
^^^^^^^^^^^^^^^^^^^^

A flag that is never set looks exactly like a context with nothing wrong. So a context checking this way asks the driver anyway, once every 64 calls, and what that finds decides whether the flag is still to be trusted: an error the callback never reported means the callback is not this context's, and the context goes back to ``glGetError`` for good.

That is what makes it safe to leave on. A context handle is an address the driver hands out again, so a program that destroys a context without saying so can leave a table describing a context that no longer exists — and checking that reads only the flag would pass everything. The audit bounds that to 64 calls and repairs it, and a thread returning to a context it left audits on its first call back. It costs about a sixth of a nanosecond per call.

The ctypes implementation has no handle to record against until a program gives it one, so a context it arms before then is recorded as unnamed. That record is given up as soon as the program says the situation has changed — ``forget_context``, or ``make_current`` naming a context — because whatever is current afterwards cannot be shown to be the context that was armed. The next context is offered the mechanism afresh.

Telling PyOpenGL is still better than being caught by the audit: ``dispatch.forget_context(handle)`` when a context goes, and ``dispatch.make_current(handle)`` when one becomes current. Neither is required — nothing breaks without them — and both are worth calling under either implementation.

Extensions that declare the same function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A command is often declared by more than one extension — ``glUniform1i64NV`` by both ``GL_NV_gpu_shader5`` and ``GL_AMD_gpu_shader_int64``, the EGL sync entry points by two KHR extensions each. A context advertising any one of them has the function, and that is what resolution requires. ``proc.extension`` reports the one the entry point is recorded under, which is a single name.

A command may also be declared by a core version *and* by an extension: ``glGetPointerv`` is GL 1.1, and ``GL_KHR_debug`` re-specifies it to report a debug callback. Which declaration ``OpenGL.GL`` holds is settled by import order, and it does not change where the entry point is found. That matters most on Windows, where the split is real: ``opengl32`` exports GL 1.1 and nothing above it, while ``wglGetProcAddress`` answers for everything above GL 1.1 and returns NULL for the 1.1 set. A name is looked for in both.

Windows is not the only platform built that way. Mesa's Windows ``osmesa`` library carries the same export list, with ``OSMesaGetProcAddress`` for the rest, so ``PYOPENGL_PLATFORM=osmesa`` there asks the library and then the lookup as well. A platform says which routes it has, and only one whose lookup is a *query* — one that answers NULL for a name it does not have — takes this one: ``glXGetProcAddressARB`` under libglvnd answers with a dispatch stub for any name at all, so a Linux fallback would report an entry point the driver lacks as present.

Nor does the driver's extension string decide it. What an extension re-specifies about a core entry point is which arguments it takes, not whether the entry point is there, so importing ``glGetPointerv`` from ``OpenGL.GL.KHR.debug`` gives a working entry point on a driver that does not advertise ``GL_KHR_debug`` — Apple's, which implements no version that has it. The gate stands aside only for a name a core version declares: macOS exports every entry point its framework implements whether or not the current context does, so an extension that is genuinely absent is still reported absent.

Docstrings and introspection
----------------------------

Entry points carry a docstring and a text signature under the C implementation, which they do not have under ctypes:

::

   >>> glBindTexture.__doc__
   'glBindTexture(target: GLenum, texture: GLuint) -> None'
   >>> glGenTextures.__doc__
   'glGenTextures(n: GLsizei) -> textures: GLuint[]'
   >>> inspect.signature(glGenTextures)
   <Signature (n, textures=None, /)>

The signature is built from the registry, so it is available for every entry point without any external documentation source. The types are the registry's own, because ``GLenum`` and ``GLuint`` are a distinction the caller makes and the man page they read next uses; an array argument is written ``GLfloat[]``, one level of ``[]`` per level of indirection. The ``.pyi`` stubs beside the package state the same signatures in Python types, which is what a type checker can use.

What an editor sees
~~~~~~~~~~~~~~~~~~~

A friendly module fills its namespace when it is imported, from the same tables the entry points come from — ``_define(globals(), 'OpenGL.raw.GL.ARB.vertex_array_object')``. Nothing reading the file can follow that, so every module ships a stub beside it saying what the import leaves in it:

::

   OpenGL/GL/ARB/vertex_array_object.pyi

   GL_VERTEX_ARRAY_BINDING: int

   def glBindVertexArray(array: int) -> None: ...
   def glGenVertexArrays(n: int, arrays: UIntArray | None = None) -> UIntArrayResult: ...
   def glInitVertexArrayObjectARB() -> bool: ...

Completion in ``from OpenGL.GL.ARB import vertex_array_object`` therefore offers what that extension declares, and a type checker knows the signatures rather than answering ``Any``. 1,299 of them, generated from the module table in the same pass as the C, so a registry update carries them along; the array aliases they annotate with are in ``OpenGL/_typing.pyi``, which is a stub and not a module to import.

Threads
-------

A GL context belongs to one thread at a time, so the usual arrangement is one rendering thread and other threads doing everything else. Two properties of the dispatch layer matter to that arrangement.

Calls that can wait release the GIL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A call that waits on the driver — ``glFinish``, ``glReadPixels``, ``glClientWaitSync``, a shader compile, a buffer mapping, a swap under vsync, a large texture or buffer upload — releases the GIL for the duration, so the other threads in the process keep running while it waits. On a 4096×4096 ``glReadPixels`` taking 20 ms, a second thread runs several hundred times during the call rather than once or twice.

Releasing costs 15–25 ns against the 57 ns a ``glBindTexture`` takes, so it is done for the calls that can actually block rather than for all of them. The list is ``src/cdispatch/blocking.py``: 26 exact names and 19 family patterns, 244 entry points in total, and the choice is made when the C is generated rather than tested on each call. A call not in that list holds the GIL, which is the right trade for one that returns in tens of nanoseconds.

Arguments converted for the call — the arrays, the strings, the buffers — are held by the calling frame across the released region, so nothing the driver is reading from can be collected while it reads.

Free-threaded builds
~~~~~~~~~~~~~~~~~~~~

The dispatch layer itself declares compatibility with the free-threaded builds of Python 3.13 and later (``Py_mod_gil``). What makes that safe is that a call touches only its own context's table; the registry of tables is guarded by a lock, and the configuration a call reads is set once at import. Where two threads share a table — on a platform that cannot say which context is current — the value they race to write is the same resolved address.

**Importing PyOpenGL on a free-threaded build re-enables the GIL anyway.** The dispatch layer ships in ``PyOpenGL_accelerate`` alongside that package's other compiled modules, and ``import OpenGL.GL`` loads six of them — ``errorchecker``, ``arraydatatype``, ``formathandler``, ``latebind``, ``wrapper`` and ``vbo``. None of those declares itself free-threading compatible, so each one turns the GIL back on as it loads, and the interpreter says so:

::

   RuntimeWarning: The global interpreter lock (GIL) has been enabled to load
   module 'OpenGL_accelerate.errorchecker', which has not declared that it can
   run safely without the GIL.

Running ``PyOpenGL`` without ``PyOpenGL_accelerate`` keeps the GIL disabled, at the ctypes implementation's speed. Getting both at once needs those six modules audited for free-threaded safety and declared, which is not something their current code supports: ``LateBind``, for one, resolves its target by writing an attribute on first call, and two threads reaching that write together is a race on a reference count rather than on a value. Until that work is done the combination is the GIL or the C dispatch, not both.

Suspending error checking, which ``glBegin`` does, is a property of the calling thread rather than the process. The ctypes implementation holds that flag on a shared object, so there one thread's ``glBegin`` block silences error checking for every thread; under C it does not.

Subinterpreters with their own GIL are refused at import. The layer keeps one set of context tables for the process, and a second interpreter would share the first one's contexts rather than have its own.

What differs from the ctypes implementation
-------------------------------------------

These are the differences a program can observe. Everything not listed here behaves identically, and the test suite runs under both implementations to keep it that way.

+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| behaviour                                            | ctypes                                                                              | C                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
+======================================================+=====================================================================================+==================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+
| ``type(glBindTexture)``                              | a ctypes function pointer, or ``_NullFunctionPointer``                              | ``GLProc``. An ``isinstance`` check against ``ctypes._CFuncPtr`` is the one idiom likely to notice.                                                                                                                                                                                                                                                                                                                                                                              |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``repr(glBindTexture)``                              | ctypes' wording                                                                     | ``<OpenGL entry point glBindTexture>``                                                                                                                                                                                                                                                                                                                                                                                                                                           |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| exception message text for a bad argument            | ctypes' wording                                                                     | ours. The exception *type* is preserved: ``ctypes.ArgumentError`` for a bad argument, ``NullFunctionError`` for an absent entry point.                                                                                                                                                                                                                                                                                                                                           |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``bool(glFoo)``, ``glInitXxx()``                     | resolved once, cached for the process                                               | answered for the current context                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| error checking suspended by ``glBegin``              | process-wide: one thread's block silences another's checking                        | per thread                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``OpenGL.FULL_LOGGING``                              | logs every call                                                                     | not implemented in C. Tracing selects the ctypes implementation for the process.                                                                                                                                                                                                                                                                                                                                                                                                 |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``glFoo.__doc__`` and ``inspect.signature(glFoo)``   | ``None``; ``signature()`` raises                                                    | a signature line, and a Signature. Gained, not changed.                                                                                                                                                                                                                                                                                                                                                                                                                          |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ``glFoo.extension`` for a command promoted into core | whichever declaration the namespace ended up holding, which depends on import order | the core declaration. A command adopted into a GL version is declared twice, by the extension that introduced it and by the version that adopted it, and ``proc.extension`` reports one of the two. Both implementations resolve it either way: a name a core version declares is present whether or not the extension that re-specified it is advertised, so neither the declaration a caller reached nor the driver's extension string decides whether the entry point exists. |
+------------------------------------------------------+-------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The full list is not a matter of recollection: ``tests/bindings/dispatch/test_attribute_surface.py`` surveys every entry point under both implementations in separate processes and compares the answers, so a difference that is not in the table above is a test failure.

Ways out
~~~~~~~~

Assigning ``errcheck`` or ``argtypes`` to an entry point moves that one entry point to the ctypes implementation for the life of the process, so a debugging habit that relies on either keeps working. Assigning ``restype`` the conversion the entry point already performs changes nothing; assigning a different one moves it likewise. ``PYOPENGL_DISPATCH=ctypes`` is the way out for everything else.

What is not implemented in C
----------------------------

GL, GLES 1/2/3, GLSC2, GLX, WGL and EGL are generated from the registry. **GLU, GLUT, GLE and OSMesa are not** — they are hand-maintained rather than registry-described, so there is no table to generate them from. They keep their ctypes bindings, which is about 210 entry points, none of them on a hot path.

Where the OpenGL.raw modules come from
--------------------------------------

The modules under ``OpenGL.raw`` hold constants, entry-point declarations and re-exports, and nothing else. They are not shipped as files. They are built on import from declaration tables — ``OpenGL/raw/_declarations/<API>.dat``, one per API — by a finder that PyOpenGL puts on ``sys.meta_path`` for itself. The tables describe 1,298 modules in 1.2 MB; as files those modules were 1,298 entries in the wheel, which is most of the difference between a 4.0 MB wheel and a 2.9 MB one.

Nothing has to be switched on, and an importing program sees no difference: ``from OpenGL.raw.GL.VERSION.GL_1_1 import *`` works as it always has. What changes is what a tool asking about the module finds — ``__spec__.origin`` is the table the definitions came from, and ``__file__`` names that table rather than a ``.py`` source.

Where the C extension is installed the same definitions are read from its own tables instead, since they are already resident; the two are generated together in one pass and describe the same set.

Two kinds are real files still. The packages, which have ``__init__.py`` as before, and the private modules — ``_types``, ``_errors``, ``_glgets`` — which carry classes and conditionals rather than data, so there is nothing to tabulate.

There is no switch for this, because there is nothing to switch to: the files are not shipped and the generator does not write them, so these names resolve from the tables or not at all. What the tables hold is held to what the files defined by ``tests/bindings/generated/test_virtual_modules.py``, which compares every constant and every signature against a recorded survey of the modules as files.

Regenerating and keeping up with the registry
---------------------------------------------

::

   python src/regenerate_c.py     # registry and shipped tree in, C out
   python src/check_registry.py   # what changed, and what needs a person

Maintaining or extending the generator is covered separately, in ``src/cdispatch/README.md``: how the pipeline fits together, how to add an entry point that needs hand-written C, and how to add an array element type.

``check_registry.py`` reports registry commands with no binding, bindings whose signature no longer matches, enums with no constant, and every entry point still on the ctypes path with the reason. Differences that are already known are recorded in ``src/cdispatch/registry_baseline.json`` with a reason for each, and the tool exits non-zero only for what is new since, so it can drive a scheduled job.
