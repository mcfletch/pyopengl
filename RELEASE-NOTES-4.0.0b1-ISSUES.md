# Tracker issues closed in 4.0.0b1

What the first 4.0 beta answers from <https://github.com/mcfletch/pyopengl/issues>,
one entry per ticket: what was actually wrong, the case that holds it fixed, the
commit, and a comment ready to post on the ticket.

The pass that produced this is described in
[plans/ISSUE-TRIAGE.md](plans/ISSUE-TRIAGE.md), which carries a verdict for
every open issue including the ones no release can close.

Four kinds of entry appear here, and the distinction is the point:

| Verdict | What it means |
|---|---|
| **fixed** | A defect, reproduced and corrected. The test named goes red without the fix. |
| **held** | Already right on `develop`, with nothing standing behind it. The test named goes red against the release the ticket was filed against, so the ticket cannot come back unnoticed. |
| **not reproducible** | Cannot be made to happen on current Mesa or current PyOpenGL. Said so plainly, with what was tried, rather than closed silently. |
| **answered** | The report is real and the cause is not here. What was checked is written down, and a case is added where one can keep the answer true. |

Every version number below is the release the reporter had, and every "red
against" is a test actually run against that release rather than an inference.

---

## Fixed

### #3 — an integer offset to `glVertexAttribPointer`

**Test** `tests/gl/test_array_acceptance.py::TestAnOffsetIntoABoundBuffer`
**Commit** `86f6205a`

With a buffer bound, the pointer argument is a byte offset and `0` is how a
caller writes it. PyOpenGL accepted the integer and was wrong to: it went
through the array machinery, became a one-element array holding the number,
and the *address of that array* went to the driver. So the call succeeded,
`glGetError` reported nothing, and the frame came back empty.

> Reopened by the test written for #42, which found that this one was never
> actually fixed — it had stopped raising, which is not the same thing.
>
> `glVertexAttribPointer(index, size, type, normalized, stride, 16)` was
> accepted and then handed the driver a heap address where the offset 16 was
> meant. No GL error, nothing drawn. The case now draws the same triangle
> through both `16` and `ctypes.c_void_p(16)` and compares the lit pixels,
> because `glGetError` has no opinion either way.
>
> An integer where a `const void *` is wanted is now converted to the offset
> it names, in one place (`OpenGL.arrays.arraydatatype.buffer_offset`) that
> all three conversion paths ask — the ctypes wrapper, the C dispatch layer,
> and `glVertexAttribPointer`'s own wrapper. A Python `int` only: a numpy
> integer or a ctypes scalar arriving there is as likely to be data.
>
> Fixed in 4.0.0b1.

### #42 — `glDrawElements` refuses an integer offset

**Test** `tests/gl/test_array_acceptance.py::TestAnOffsetIntoABoundBuffer`
**Commit** `86f6205a`

The loud half of #3.

> `glDrawElements(GL_TRIANGLES, 3, GL_UNSIGNED_SHORT, 0)` raised
>
>     TypeError: No array-type handler for type <class 'ctypes.c_ushort'>
>     (value: c_ushort(0)) registered
>
> which names an array-type handler the caller was never trying to supply and
> says nothing about the `ctypes.c_void_p` cast that was missing. That is why
> both this ticket and #3 are somebody working it out from an example rather
> than from the error.
>
> An integer is now read as the byte offset it is, here and on every other
> entry point taking a `const void *` — the pixel calls with a pixel buffer
> bound, the client-array pointers, and the rest. `ctypes.c_void_p` keeps
> working; there is a case for each spelling and one that checks they draw the
> same frame.
>
> Fixed in 4.0.0b1.

### #33 — `TypeError: unhashable type` from `contextdata`

**Test** `tests/bindings/test_opaque_pointers.py`
**Commit** `2555b4f7`

Two defects under one symptom, and the quieter one was worse.

> This turned out to be two things, and running the suite on OSMesa found both.
>
> The reported `TypeError` came from `GLXContext` being declared as a bare
> `POINTER(struct)` rather than an opaque pointer class as `EGLContext` and
> `OSMesaContext` are. Plain ctypes pointers are unhashable, and
> `contextdata` keys everything it holds per context by one — so
> `storage.get(context)` raised before anything could say which context it
> meant.
>
> The quieter defect was in every opaque handle: they carried `__hash__` by
> address and no `__eq__`, so they fell back to identity comparison. Nothing
> hands back the identical Python object twice — every call returning a handle
> builds a new pointer — so two handles for one context hashed into the same
> bucket and then compared unequal. Measured on OSMesa: fifty `setValue` calls
> against the current context left fifty entries where there should be one,
> none of them reachable, each holding a client array alive forever. No
> exception, no symptom until something ran out of memory.
>
> A handle now compares equal to another of the same kind at the same address,
> and `forget_context` drops the cache under the handle rather than under the
> integer address it had reduced it to — which had worked only on the
> platforms whose handle *is* an integer.
>
> Fixed in 4.0.0b1.

### #70 / #129 — `'…Platform' object has no attribute 'OSMesa'`

**Test** `tests/bindings/platform/test_platform_libraries.py::test_a_namespace_the_platform_cannot_serve_says_how_to_select_it`
**Commit** `40627cfa`

> `from OpenGL import osmesa` under any other platform answered
>
>     AttributeError: 'LinuxPlatform' object has no attribute 'OSMesa'
>
> which names an attribute of a class the caller has never heard of and reads
> as a defect in PyOpenGL rather than as a setting they have not made. It now
> says what to set:
>
>     AttributeError: 'LinuxPlatform' has no OSMesa: it belongs to the 'osmesa'
>     platform, which this run did not select. Set PYOPENGL_PLATFORM=osmesa in
>     the environment, or os.environ before the first `import OpenGL`, since
>     the platform decides which library every entry point is loaded from.
>
> Whoever meets this can least afford the old message: OSMesa is how a machine
> with no display renders, so by construction they cannot see what their
> session is. Between them these two tickets carry six "me too" comments and
> no diagnosis.
>
> Fixed in 4.0.0b1.

### #137 — an OpenGL ES version string

**Test** `tests/gl/test_version_queries.py::TestTheVersionStringIsParsed`
**Commit** `8bdf7b2e`

> The parse itself was fixed earlier: `pullVersion` reads a version out of
> every string reported on this ticket, `OpenGL ES 3.2 NVIDIA 535.216.01`
> included.
>
> What was still wrong is what it did with the match. The pattern was
> `^(?P<api_marker>OpenGL (ES )?)?…`, so the group captured `'OpenGL ES '`
> *with the trailing space*, and the code compared it against `'OpenGL ES'`.
> The comparison could never be true — so `is_opengl_es` stayed False on every
> ES context and the warning it guards has never once been printed.
>
> That warning is the whole of what a caller is told. Reaching an ES context
> through `OpenGL.GL` is how both reporters here arrived: the entry point
> resolves, happens to work, and is not the one they meant. Fixing the string
> without fixing the flag would have left them equally uninformed, one
> exception later.
>
> Fixed in 4.0.0b1.

### #138 — the `xlib` test dependency

**Test** the suite's own `tests/checks` run, which is what uses it
**Commit** `e24475c2`

> Swapped to `python-xlib >= 0.33`. Both distributions install the same `Xlib`
> package; `xlib`'s last release was 0.21 in 2018 against python-xlib's 0.33 in
> 2022. Your conda point is the sharper one and settled it: conda-forge
> packages `python-xlib` and not `xlib`, so a conda environment could not
> satisfy the old name at all.
>
> Fixed in 4.0.0b1.

### #121 — generated code in the release, and #12 — the `.pxd` files

**Test** `tests/bindings/test_accelerate_generated_c.py::TestWhatTheSdistShips`
**Commit** `0ccacb92`

> Both settled, in opposite directions.
>
> #121: the nine Cython-generated `.c` files are out of the sdist. They were
> never doing anything — Cython is a hard build requirement, and the archive
> carries no toolchain stamp, so `drop_c_from_another_toolchain` deleted them
> on arrival and rebuilt every one. They were weight that never survived
> contact with an installer, and weight with exactly the hazard you name
> attached.
>
> `src/c/**` stays, and there is a case saying so: that is the dispatch layer
> generated from the Khronos registry by a tool that does not run at install
> time and is not shipped, so it has to be in the archive or nothing can be
> built at all. Two kinds of generated C under one directory and only one of
> them is a liability, which is worth being explicit about.
>
> #12: the `.pxd` files and the `OpenGL_accelerate/__init__.py` that makes
> them a package Cython can `cimport` from are all present, and now held there
> by a case.
>
> Fixed in 4.0.0b1.

### #166 — an error that says nothing

**Test** `tests/bindings/errors/test_error_checking_disabled.py`
**Commit** `05837fdb`

> Your traceback was reproducible and the cause is ours.
>
> `PYOPENGL_ERROR_CHECKING=0` set `OpenGL.error._ErrorChecker` to None — there
> is no checker, which is the point of the flag — and two raw modules built
> one anyway. `OpenGL/raw/GL/_errors.py` had always guarded against it;
> GLES2's and GLSC2's `_types.py` had not. So `import OpenGL.GLES3` failed
> outright with `TypeError: 'NoneType' object is not callable`, from a line
> naming neither the flag nor anything you wrote.
>
> That is also the flag a finished renderer reaches for first, since a
> `glGetError` round trip per call is the largest cost PyOpenGL adds — so the
> configuration that broke the import is the one a program adopts when it
> stops being a prototype.
>
> Your ticket asked for the library to guide the reader to the fix rather than
> fail in a way only its author can read. Two other things in this release came
> from that: a platform plugin that will not import now names itself and says
> where its reason went (#43), and asking a platform for an API belonging to
> another now names `PYOPENGL_PLATFORM` (#129).
>
> Fixed in 4.0.0b1.

### #5 — `ERROR_ON_COPY` "doesn't trigger"

**Test** `tests/bindings/test_configuration_flags.py::TestAFlagSetAfterTheWrappersAreBuilt`
**Commit** `d9ce90e1`

> The flag was not being ignored by the array code; it was never in force.
>
> PyOpenGL reads its flags once, when the first entry point is built, and
> freezes them. So this works:
>
>     import OpenGL
>     OpenGL.ERROR_ON_COPY = True
>     import OpenGL.GL
>
> and this — which is what the ticket does — changes nothing at all:
>
>     import OpenGL.GL
>     OpenGL.ERROR_ON_COPY = True
>
> It now warns, naming the flag, the value actually in force, and
> `PYOPENGL_ERROR_ON_COPY`, which works whatever the import order. The
> assignment still does not take effect and the warning says so: honouring it
> would mean rebuilding every entry point already bound.
>
> On the memory itself: twenty VBOs of a 2.7 MB array grew peak RSS by 2.9 MB
> here, so the allocation does not reproduce. And `vbo.VBO` of a float64 array
> is accepted under `ERROR_ON_COPY` correctly — a VBO uploads the array's
> bytes and converts no dtype, so there is no copy to refuse.
>
> Fixed in 4.0.0b1.

### #43 — `TypeError: 'NoneType' object is not callable` on import

**Test** `tests/bindings/platform/test_plugin_load_failure.py`
**Commit** `c02f4b36`

> Reproduced and fixed. `PlatformPlugin.load` wrote the real ImportError to a
> logger nobody has configured, returned None, and `_load` then called it —
> so you were told neither which plugin was chosen, nor that a plugin was
> involved, nor what actually failed.
>
> Every reply on this ticket is a request that you run something by hand to
> recover a message PyOpenGL already had and discarded. It now raises
> ImportError naming the plugin, the import path, the three things that
> selected it, and where the underlying reason went — and says what it usually
> is, a library absent or in a place the dynamic loader does not look.
>
> An ImportError rather than a TypeError because the distinction is the whole
> message: one says a missing thing, the other says a bug in PyOpenGL.
>
> Fixed in 4.0.0b1.

### #38 — upstream renames a parameter

**Test** `tests/bindings/generated/test_wrapper_parameter_names.py`
**Commit** `7da72039`

> You asked for a procedure; this is a sweep instead, because a sweep runs on
> every commit and a procedure runs when somebody remembers.
>
> 624 parameter references across the tree are now checked from the source:
> every `setInputArraySize('name', …)`, `setOutput('name', …)` and
> `pnameArg='name'` must name a parameter its entry point actually has. Your
> reading of the risk was right — a name that is not there does not fail, so
> the wrapper is built, the module imports, and the customisation silently
> does not happen. No array conversion, no size check.
>
> The sweep found one, and it predated any rename. `glGetFogFuncSGIS` is
> declared `len="COMPSIZE()"` — the size is computed and nothing is named to
> compute it from — and the generator emitted `pnameArg=''`. Calling it gave
> `Error finalising item 0 in cConverters`, naming nothing a caller wrote. The
> generator now requires a non-empty name, and the emitted module is
> corrected.
>
> On supporting both names at once: not done, and I would rather not. Two
> spellings of one parameter is a second thing to keep in step, and the sweep
> makes a rename a failing test on the commit that lands the registry update,
> which is early enough to handle it deliberately.
>
> Fixed in 4.0.0b1.

### #114 — a large argument in an error message

**Test** `tests/bindings/errors/test_big_arguments_in_messages.py`
**Commit** `61ff46ac`, `ca-pending`

Believed fixed until the test was run on the ctypes dispatch layer, where it
was not: 134 million characters of message for a 32 MB argument.

> Reproduced and fixed, and the test found more than the ticket did.
>
> A GL call's arguments are routinely enormous, and formatting one into an
> exception produces megabytes of digits: your IDLE stopped responding, and a
> terminal fills its scrollback while the message you needed scrolls past.
>
> The C dispatch layer already bounded this. The ctypes layer did not, and
> neither did the compiled wrapper's own arity check — three copies of the
> same "requires N arguments, received M: %r" message, two of them formatting
> the whole argument tuple. On a 32 MB `bytes` that is a 134-million-character
> message; the same call now produces 51 characters.
>
> Bounded where the message is built rather than by whatever prints it, since
> `str(error)` is called by logging, by `repr` and by the traceback machinery
> before anything decides whether to show it — so the cost was paid whether or
> not anybody ever read the result. Each argument is shown to 100 characters
> and then named by type and length.
>
> Fixed in 4.0.0b1.

### #175 — `glBufferData` with a `memoryview`

**Test** `tests/gl/test_array_acceptance.py::TestAMemoryViewAsTheSource`,
`tests/bindings/arrays/test_py_buffer_as_a_pointer.py`
**Commit** `017ccf86`, `pending`

Recorded first as not reproducible; running the suite with the accelerators
switched off found a defect of the same shape — silent corruption rather than
a crash.

> Your crash does not reproduce here, but writing the cases for it found a
> real defect one configuration over, and it is very likely the same root.
>
> With the compiled accelerators off — which is PyPy, any platform with no
> wheel, and anyone setting `PYOPENGL_USE_ACCELERATE=0` — `glBufferData` with
> a `memoryview` uploaded **the wrong bytes**. The size was right, the call
> succeeded, `glGetError` said nothing, and the buffer held a pointer value
> where the data should be.
>
> The pure-Python array machinery turned a memoryview into a `Py_buffer`,
> which is a `ctypes.Structure`, and ctypes passes one of those to a
> `void *` parameter as *the address of the structure*. So the driver was
> handed the wrapper and copied the wrapper's own bytes. The compiled handler
> answers with the memoryview itself, which ctypes passes correctly — which is
> why this was invisible to anyone with a wheel, and why your `bytes(mem)`
> workaround helped: `bytes` takes a different handler entirely.
>
> The Python handler now answers with a memoryview too, so both
> configurations agree. Cases cover `bytes`, a memoryview, a slice of one and
> a bytearray, and they read the buffer back rather than trusting the call to
> have returned — a wrong length or wrong content that happens not to fault is
> the same defect one allocation luckier, which is plausibly what you were on
> the wrong side of.
>
> Fixed in 4.0.0b1. If it still crashes for you there, `python -m
> OpenGL.version` and your Mesa version would help.

### #174 — `opengl32.dll` came from `PATH` rather than from Windows

**Test** `tests/bindings/platform/test_library_loading.py::TestALibraryWindowsItselfProvides`
**Commit** `9ce2ecec`

> Reproduced and fixed, and you had the right diagnosis and the right remedy.
>
> `_loadLibraryWindows` asked `ctypes.util.find_library` first, which walks
> `PATH`. `System32\opengl32.dll` is a trampoline to whatever the graphics
> driver installed, so it is the only correct one, and conda puts
> `Library\bin` — carrying a Mesa `opengl32.dll` — ahead of System32. The
> result is the worst kind of wrong: the load succeeds, the calls succeed, and
> the only sign is that the program is slow and `GL_RENDERER` says something
> else.
>
> `opengl32` and `glu32` now go to the loader bare, so Windows' own search
> order answers, which reaches the system directory before `PATH`. freeglut
> and the rest still go through `find_library`, because where the user put one
> of those is exactly what `PATH` is for.
>
> The case stands in for the loader and records which name was handed to it,
> so it runs on any machine; what a Windows machine adds is confirming that
> the driver's GL is what arrives.
>
> Fixed in 4.0.0b1.

### #76 / #125 — a freeglut you installed was not found

**Test** `tests/bindings/glut/test_glut_library_names.py`
**Commit** `53fbd9c9`

> Reproduced and fixed. #76 diagnosed it exactly, by reading the source, which
> should not have been necessary.
>
> The only GLUT names asked for were `freeglut64.vc14` and `glut64.vc14` —
> names nothing ships under but us. The official freeglut Windows binaries
> install `freeglut.dll`, MSYS2 and vcpkg install `freeglut.dll`, and the
> original GLUT is `glut32.dll`. So a machine that had GLUT still reported
> `glutInit` as an undefined function, and renaming the file was the only way
> through.
>
> Those names are now asked for, and first: a GLUT you installed is one you
> chose, and yours is the build that gets fixes. The bundled builds follow.
> freeglut before GLUT at each step, which is what the loop always intended.
>
> Two things went with it. `except WindowsError` is now `except OSError` —
> they are the same class on Windows, and the clause matters, because a 32-bit
> freeglut on a 64-bit `PATH` is a file that exists and will not load and must
> not stop the search. And #76's second error, `ctypes.ArgumentError` from
> `glutCreateWindow("...")`, is a separate defect: it is already right on
> `develop` and held by `tests/bindings/glut/test_glut_window_title.py`, which
> is #48 and #144.
>
> Fixed in 4.0.0b1.

### #7 — the WGL extension query on a platform that is not WGL

**Test** `tests/bindings/wgl/test_wgl_extension_query.py`
**Commit** `a58f0222`

> The str-versus-bytes handling you reported was fixed, and the dispute on
> this ticket deserved better than silence, so it now has cases rather than an
> assurance: the extension list comes back as bytes, the entry point is asked
> for by a bytes name, and a `str` specifier and a `bytes` specifier both
> match.
>
> Writing them found something adjacent. `pullExtensions` ends in
> `except AttributeError: return []`, which is the answer for a platform that
> is not WGL — and the lookup that raises it sat outside the `try`, so the
> clause could never run and a `WGL_` specifier on a machine with no WGL
> raised out of whatever import asked. Both lines are inside it now.
>
> Also held: the device context is declared `HDC` before the call, so a
> 64-bit handle keeps its top half rather than becoming a valid-looking DC
> belonging to nothing — which would present as exactly this ticket, an
> extension list that is empty for no visible reason.
>
> Fixed in 4.0.0b1. If `wglGetSwapIntervalEXT()` still fails for you there, the
> output of `OpenGL.WGL.WGLQuerier.getExtensions()` would say whether the
> driver is listing it.

### #59 / #54 — an undefined function, because the library is not installed

**Test** `tests/bindings/platform/test_missing_library_errors.py`
**Commit** `6556784b`

Both reporters were told the entry point was undefined. Neither was told that
the library holding it was not on the machine, which is a different problem
with one thing to do about it.

> Fixed, and the error is the fix.
>
> `gluOrtho2D` was undefined here because `libGLU` is not installed —
> `python-opengl` does not bring it, and on Arch and CentOS it is a separate
> package. #54 is the same thing for GLUT, and the answer arrived on that
> ticket thirteen months later as a comment reading
> `apt-get install freeglut3-dev`.
>
> The message said none of that. It named one function and told you to check
> `bool()` on it, when in fact *every* GLU entry point was undefined and
> checking any of them would have said the same. It reads as PyOpenGL being
> broken rather than as a package that is not installed, which is why both
> tickets are somebody asking what they did wrong.
>
> It now says which library was not found, that every entry point in it is
> undefined, and where to get it:
>
>     Attempt to call an undefined function gluOrtho2D: the GLU library was
>     not found on this machine, so every GLU entry point is undefined
>     (Debian and Ubuntu: libglu1-mesa; Fedora: mesa-libGLU; Arch: glu;
>     Windows and macOS ship it). Check bool(gluOrtho2D) before calling.
>
> GLU, GLUT, GLE and EGL each have their own line. The library is read from
> the entry point's prefix, which is the API's own naming — there is nothing
> else left to read, because a library that would not load is `None` and every
> declaration in the module was built against it.
>
> Fixed in 4.0.0b1.

### #115 — `glGenVertexArrays` undefined, with a driver that has it

**Test** `tests/bindings/platform/test_missing_library_errors.py::TestACallMadeBeforeThereIsAContext`
**Commit** `6556784b`

The message defect is fixed. The ticket stays open on one question, because
what the reporter had is very likely a second thing.

> A 1080ti on driver 545 has `glGenVertexArrays`, so the message was wrong
> about what was happening, and there are two candidates in your report.
>
> The one I would look at first is `PyOpenGL 3.1.0` beside
> `PyOpenGL-accelerate 3.1.7`. Those are not a matching pair — 3.1.0 is from
> 2015 — and the accelerator's tables are generated from the PyOpenGL it
> shipped with, so a mismatch can produce exactly this, and the
> `free(): invalid pointer` underneath it is the kind of thing it produces
> next. 4.0 refuses a mismatched pair rather than running on one.
>
> The other is ordering: above GL 1.1 an entry point's address comes from the
> *context*, so a call made before pyglet has created one finds nothing. That
> is the usual cause of this error on Windows, where `wglGetProcAddress`
> needs a current context; on Linux with GLX it is less likely, since
> `glXGetProcAddress` answers without one. It is worth ruling out.
>
> The message itself is fixed either way. It said the same thing for a
> library that is not installed, a call made before there was a context, and
> a driver that lacks the entry point — three problems with three different
> answers — and it now tells them apart and says which one you are in.
>
> Would you try `pip install -U PyOpenGL PyOpenGL_accelerate` so the two
> match, and paste what the error says then?

### #29 — `test_buffer_api_basic` on i586 and armv7l

**Test** `tests/bindings/arrays/test_arraydatatype.py::TestReadingAFormatString`
**Commit** `90e8dd11`

> Fixed, and thank you for the full traceback — it is what made this
> answerable without a 32-bit machine.
>
> `assert '<l' in ['(3)<i', '(3)<l', '<i']`. The case listed the format strings
> CPython reports for a `(GLint * 3)` and asserted the answer was one of them.
> A 4-byte signed int is a `c_long` on i586 and armv7l, so the letter is `l`,
> and the list did not have it. #92 was the same failure on s390x, where the
> byte-order character is `>`; that was fixed by branching on `sys.byteorder`,
> which left this half in place.
>
> The spelling is the machine's to choose — the shape prefix comes and goes
> with the interpreter version, the order character with the endianness, the
> letter with which C type is four bytes wide. So the case now reads the
> item-type letter out of the format string and asserts what the value *is*, a
> signed integer. No width is lost: `itemsize` is asserted separately and is
> what pins it. A machine that reports a fifth spelling changes nothing.
>
> Fixed in 4.0.0b1. A 32-bit run would still be welcome: your traceback stops
> at the first failing assertion, so the shape and strides checks below it have
> never been seen on a 32-bit machine.

---

## Held

### #143 / #158 — `SyntaxWarning: invalid escape sequence '\ '`

**Test** `tests/bindings/generated/test_shipped_modules_compile_cleanly.py`
**Commit** `017ccf86`
**Red against** PyOpenGL 3.1.9, at `GL/AMD/vertex_shader_tessellator.py` — the
module both tickets name.

> Fixed, and now held fixed by a case that compiles every shipped module from
> its own bytes and fails on any warning. From the file rather than by
> importing, because the warning is raised while source becomes bytecode and a
> warm `.pyc` means nothing raises it a second time — which is also why the
> tree can be clean on a developer's machine and warn on yours.
>
> Verified red against 3.1.9 and green on the 4.0 branch.
>
> Released in 4.0.0b1.

### #79 / #145 / #147 — the accelerator will not build

**Test** `tests/bindings/test_accelerate_generated_c.py::TestTheSourcesCompileWithTheCythonInstalled`
**Commit** `017ccf86`
**Red against** the 3.1.9 sdist: `vbo.pyx:191: undeclared name not builtin: long`.

> All three are one thing: an sdist install runs Cython on your machine, so a
> construct Cython stops accepting is every source install failing from that
> Cython onward. Cython 3.1 dropped `long` as a builtin name and `vbo.pyx`
> used it.
>
> It was reported three times in a month — from a Raspberry Pi, from arm64 and
> from an Intel Mac — and read each time as an architecture problem, because
> that is what each reporter had in front of them. It was neither.
>
> There is now a case that cythonises every `.pyx` with whichever Cython the
> environment resolved, so the next such change is a failed test rather than
> three tickets.
>
> Released in 4.0.0b1.

### #107 / #117 — clang refuses the generated C

**Test** `tests/bindings/test_accelerate_generated_c.py::TestTheGeneratedCSatisfiesClangToo`
**Commit** `681e5cdc`
**Red against** the 3.1.7 sdist under clang 18: all nine modules refused, the
`import_array()` `-Wint-conversion` error being this ticket's verbatim.

> Confirmed fixed, and now with a compiler that can prove it: clang is
> installed in the development image and reads the accelerator's generated C on
> every run, with `-Wint-conversion` and `-Wincompatible-pointer-types` back as
> errors.
>
> gcc compiles this package on every Linux build, so gcc's opinion was the only
> one ever heard; clang's arrived as bug reports from macOS and the BSDs. That
> asymmetry is what let this stand.
>
> Released in 4.0.0b1.

### #47 / #96 — an image the caller keeps

**Test** `tests/gl/test_images.py::TestAnImageTheCallerKeeps`
**Commit** `61ff46ac`

> Confirmed fixed and now held. PyOpenGL copies an array the driver cannot
> read directly — the copy is right; keeping a reference to the original
> afterwards was not, and a renderer uploading a frame per loop then
> accumulates one array per frame.
>
> The cases upload eight times and compare refcounts, contiguous and flipped
> (`data[::-1]`, which is how it arrives in practice). #96's exact sequence is
> a case too: its report is a segfault in `glGenerateMipmap`, which is where a
> short or freed upload buffer is noticed rather than where it was made.
>
> Released in 4.0.0b1.

### #51 — `GL_HALF_FLOAT` for images

**Test** `tests/gl/test_images.py::TestHalfFloatImages`
**Commit** `61ff46ac`

> Fixed, and now with cases. Sixteen-bit floats are how a renderer uploads
> high-dynamic-range data at half the bandwidth, so the type is ordinary
> rather than exotic. The table is asked directly as well as through a call,
> so a regression names the missing type instead of arriving as a `KeyError`
> out of a converter several frames in, which is what you saw.
>
> Released in 4.0.0b1.

### #21 — `numpy.float128`

**Test** `tests/bindings/arrays/test_numpy_without_float128.py`
**Commit** `61ff46ac`

> Fixed, and now held by a case that deletes the attribute and rebuilds the
> handler — which is exactly what a Windows numpy looks like from inside it,
> MSVC's `long double` being a `double`.
>
> Worth recording why it surfaced as `glGenTextures`: a handler naming the
> type unconditionally fails while it is being *built*, so it is not one call
> that breaks but the whole array plug-in, reported from whichever entry point
> the caller reached first. It had nothing to do with glGenTextures.
>
> Released in 4.0.0b1.

### #120 — `ARB_bindless_texture`

**Test** `tests/bindings/generated/test_every_generated_module_imports.py`

> It is there: `OpenGL.GL.ARB.bindless_texture`, with all sixteen entry points,
> and already covered by the sweep that imports every shipped module.
>
> `glGetTextureHandleARB` and the rest are reached by importing that module.
> The registry's extension *list* is a different thing from the bindings, which
> is probably what you were looking at.

### #46 — a wheel with no numpy handler

**Test** `tests/bindings/test_accelerate_generated_c.py::TestNumpyIsABuildRequirement`
**Commit** `53e9cdde`

> Fixed: numpy is named in `[build-system] requires`, so the backend installs
> it into the build environment whether or not the machine has one, and the
> skip that produced those handler-less wheels cannot be reached from a real
> build.
>
> Your diagnosis was exactly right — the 3.1.5 Windows wheel was compiled
> without numpy — and the install-order workaround you found is no longer
> needed.
>
> Released in 4.0.0b1.

### #95 — `glActiveTexture` slow

**Test** `tests/gl/test_call_cost.py`
**Commit** `53e9cdde`

> Not reproducible on 4.0: `glActiveTexture` is 0.07 microseconds per call
> through the C dispatch layer.
>
> The context on your ticket points somewhere else. A PyQt5 program rendering
> into a QtQuick context is the shape of #88 and #172 — PyOpenGL choosing the
> EGL platform for a context Qt made through GLX, so every call paid for a
> context check that could not succeed. The Linux platform plugins are now one
> `LinuxPlatform` and that whole family is gone.
>
> Four state-setting calls are now timed under the `performance` marker, since
> a frame makes thousands of them and nothing was watching that number.

### #141 — Debian packaging failures

**Commit** `dec27734`, `53e9cdde`

> Worked through, and the parts that were ours are fixed.
>
> `AttributeError: 'EGLPlatform' object has no attribute 'GLX'` during
> collection: gone. The Linux platform plugins are now a single
> `LinuxPlatform`, and `from OpenGL import GL, GLX` imports cleanly under
> `PYOPENGL_PLATFORM=egl`.
>
> `test_glCallLists_twice2` (SF#2829309): passes here, and is covered by
> `tests/gl/test_gl1_lists.py`. See #142 — the maintainer's reading is that a
> newer Mesa stopped serving `glPushName` from inside a display list, which is
> the driver's decision rather than ours.
>
> The writable-`HOME` point: the suite passes with `HOME=/nonexistent`. That
> message was Mesa declining to make a shader cache, not a failure.
>
> The `check_egl_es1` / `check_egl_es2` / `egl_ext_enumerate` failures are your
> build machine's EGL, and I have no way to reproduce them. If they persist on
> 4.0.0b1 the output of `python tests/report_egl_device_enumeration.py` would
> tell us which devices it is finding.

### #48 — `glutCreateWindow` with a `str`

**Test** `tests/bindings/glut/test_glut_window_title.py`

> A GLUT window title is a `str` on every platform, and there is a case
> holding the argument type of the Windows route specifically — FreeGLUT there
> calls `exit()` on a fatal error, so the binding goes through
> `__glutCreateWindowWithExit`, and that override declaring the wrong title
> type is what made this a ctypes.ArgumentError on Windows and nowhere else.
>
> Released in 4.0.0b1. See also #144 and #76, the same defect.

### #88 / #104 / #113 / #148 / #172 — the platform-selection cluster

**Test** `tests/bindings/platform/`, and the whole suite run under
`PYOPENGL_PLATFORM=egl`
**Commit** the unified `LinuxPlatform`, before this pass

Five tickets, one question: which platform plugin gets selected, and what a
caller gets when it is not the one their context uses.

> These five are one defect and it is gone.
>
> PyOpenGL used to pick between separate GLX and EGL Linux plugins by
> guessing from `WAYLAND_DISPLAY` and `DISPLAY`, and the guess is not
> answerable: a Wayland session running a toolkit through XWayland has both
> set, and only the toolkit knows which it made its context with. Choosing
> EGL for a GLX context meant `eglGetCurrentContext()` answering None on
> every call, which is
>
> - #104 and #113: "Attempt to retrieve context when no valid context"
> - #88: `glInitFramebufferObjectARB()` answering False for an extension the
>   context has
> - #172: the same on Qt with `QT_QPA_PLATFORM=xcb`
> - #148: `AttributeError: 'EGLPlatform' object has no attribute 'GLX'`
>
> The Linux plugins are now a single `LinuxPlatform` that carries both, so
> there is nothing left to guess: `from OpenGL import GL, GLX` imports under
> `PYOPENGL_PLATFORM=egl`, and a context is found whichever API made it. The
> `PYOPENGL_PLATFORM=glx` workaround on several of these tickets is no longer
> needed.
>
> #95 is very likely the same defect wearing a stopwatch — a Qt program whose
> every call paid for a context check that could not succeed.
>
> Fixed in 4.0.0b1.

### #68 — `glReadPixels` with `GL_RGB` and `GL_UNSIGNED_BYTE`

**Test** `tests/gl/test_images.py::TestReadingPixelsBack`

> That combination is valid and works: it is read back and asserted in
> `tests/gl/test_images.py` on every run, along with `GL_BYTE` and the
> `glReadPixelsub` spelling.
>
> The advice on the ticket to change the type to `GL_FLOAT` was wrong, and
> would have hidden the real cause. `GL_INVALID_ENUM` from `glReadPixels` on a
> single-buffered GLUT window over remote X is the read *buffer*, not the
> format — there is nothing to read from until something has been drawn and
> the buffer is complete.
>
> If it still happens on 4.0.0b1, `glGetIntegerv(GL_READ_BUFFER)` before the
> call is the thing to look at.

### #159 — a scalar object name under `ERROR_ON_COPY`

**Test** `tests/gl/test_buffer_getters.py`, run under the
`flagerrorcopy` CI axis
**Commit** `d9ce90e1`

> Works: `glGenBuffers(1)` gives a scalar and `glDeleteBuffers(1, name)` takes
> it back, with accelerate installed and `PYOPENGL_ERROR_ON_COPY=1`. CI runs a
> whole axis under that flag now, which is what was missing.
>
> Your second finding was the more valuable one, and it is fixed separately.
> You worked out that setting `OpenGL.ERROR_ON_COPY` at the top of a test
> module had no effect because pytest had already imported another module —
> and its `import OpenGL.GL` — during collection. That silence is now a
> warning naming the flag and `PYOPENGL_ERROR_ON_COPY`; see #5.
>
> Released in 4.0.0b1.

### #92 — big-endian buffer formats on s390x

**Test** `tests/bindings/arrays/test_arraydatatype.py`

> Fixed: the case reads `sys.byteorder` and expects the order the platform
> actually has, rather than the little-endian spelling.
>
> No s390x here to confirm on, so this is the fix the maintainer described on
> the ticket rather than a run on the hardware. If the Fedora build still
> fails on 4.0.0b1 the failing assertion would be worth seeing.

### #77 / #140 — tags for releases

**Test** `tools/preflight.py` and the release tool's own cases, in the
workspace above this checkout

> Done, and automated rather than promised: the release tool tags every
> release it makes (`v<version>`, annotated) as step four of five, before it
> pushes. So a release that reaches PyPI has a tag by construction rather than
> by somebody remembering.
>
> 4.0.0b1 will be tagged `v4.0.0b1`. The historical tags this ticket asked for
> are a separate job — they have to be reconstructed from the changelog — and
> are not part of this release.

---

## Not reproducible

### #10 / #18 / #34 — OSMesa

**Commit** `681e5cdc`, `e24475c2`

`libosmesa6` is now installed in the development image and OSMesa is a
first-class test backend, so these could finally be tried rather than guessed
at.

> `libosmesa6` is now in our development image and the whole test suite runs
> through OSMesa (`TEST_WINDOWING=osmesa`), so this could be tried properly for
> the first time.
>
> It does not reproduce on Mesa 25.1: OSMesa hands out a 4.5 compatibility
> profile, `glClear` works, and the buffer reads back correctly. The reports
> here are against Mesa 18–19, where `libOSMesa.so` genuinely did not export
> the GL entry points in the arrangement PyOpenGL expected.
>
> Closing as fixed by the intervening Mesa releases rather than by anything
> here. There is now a check script and a suite covering the OSMesa entry
> points, so a regression on this platform is a failing test rather than
> another ticket.

### #96 — `glGenerateMipmap` segfault

Covered above under #47: the sequence is a case, and it does not fault here.

### #142 — `glCallLists` and the name stack

**Test** `tests/gl/test_gl1_lists.py`

> Not ours, as far as this can be taken. The case passes on Mesa 25.1 here.
>
> The reading on the ticket still looks right: the failure is `0` names where
> one was expected, meaning none were pushed, and both display lists and
> `glPushName`/`glPopName` are ancient enough that a driver dropping the
> combination is plausible. It is the opposite of the original SF#2829309
> defect, which pushed them twice.
>
> Left open rather than closed, since somebody on the affected Mesa could
> still say which version changed it.

---

## Answered

### #127 — the DLLS folder is missing from an installation

**Test** `tests/bindings/test_what_the_wheel_ships.py`
**Commit** `de859543`

> A wheel built from this checkout carries all eighteen files in
> `OpenGL/DLLS` -- the freeglut and GLE builds for vc9, vc10 and vc14 in 32-
> and 64-bit, and their licences. So whatever produced an installation without
> them, it was not this configuration, and the answer to "can't install
> freeglut" is that you should not have to: it is already inside PyOpenGL.
>
> The way they arrive was worth pinning down while looking. `OpenGL/DLLS` is a
> directory inside a package with no `__init__.py`, so setuptools does not see
> it as a package and it arrives only as package data -- named in `MANIFEST.in`
> and not in `[tool.setuptools.package-data]`, which works because
> `include-package-data` defaults to true for a project configured through
> `pyproject.toml`. Every Windows GLUT user depends on a default in another
> project's tool, and dropping that one line removes all eighteen from the
> wheel with nothing failing. There is now a case that builds the wheel and
> reads it, so that cannot happen unnoticed.
>
> #76 and #125 are the other half of "GLUT is not found on Windows" and were a
> real defect: the only names asked for were the bundled builds' own, so a
> freeglut you installed yourself was never looked for. That is fixed in
> 4.0.0b1.
>
> If you still have no `OpenGL/DLLS` after `pip install PyOpenGL`, where the
> package came from would help -- conda, a distribution package, or PyPI.

### #55 — Big Sur's dyld cache

**Test** `tests/bindings/platform/test_library_loading.py::TestAMacOSFramework`
**Commit** `9ce2ecec`

> You were right about the mechanism, and the answer turned out to be two
> things.
>
> CPython fixed `find_library` for the dyld cache in 3.8.10 and 3.9.1. This
> package now requires 3.9, so every supported interpreter has that fix, and
> the line you linked has since gone.
>
> What is added is a fallback for where `find_library`'s heuristics still come
> up empty: `/System/Library/Frameworks/<name>.framework/<name>`, handed
> straight to `dlopen`. Nothing checks that the path names a file first, which
> is the part of the release note that matters — the case asserts that nothing
> asks, so it stays true.
>
> Fixed in 4.0.0b1. Thank you for the offer of a PR, and sorry it sat.

---

## What this release does not answer

The other 15 open issues, so the list above is not read as the whole tracker.
[plans/ISSUE-TRIAGE.md](plans/ISSUE-TRIAGE.md) carries the reasoning for each,
and the ten that are not defects are listed after them.

**Needs a platform this pass could not run.** #60, #139, #144 and #162
(Windows and macOS); #135 and #173 (other architectures).
[plans/ISSUE-PLATFORM-HANDOFF.md](plans/ISSUE-PLATFORM-HANDOFF.md) is written
for somebody sitting at one of those machines: what the reporter saw, what
would settle it, and which case holds it.

Everything on that list that could be written from Linux has been, so #7, #29,
#55, #76, #125, #127 and #174 appear above rather than here. What each still
wants is a run rather than a change, and only three want anything a case
cannot do: whether the driver's GL is the one that arrived (#174), whether a
GLUT the machine already had is found (#76), and whether the driver lists an
extension (#7). Those three ship in 4.0.0b1 on the strength of cases that
stand in for the platform.

**Needs hardware or a build nobody here has.** #105 wants an interpreter built
with assertions; #124 an NVIDIA container; #170 is TensorFlow and Mesa loading
two different LLVMs into one process, which is not ours to fix. #92 is held
above and would still be worth confirming on an s390x.

**Needs something only the reporter can supply.** #32, #61, #73, #82, #132 and
#167 are each a machine, a program or a driver that has not been described in
enough detail to reproduce, and several are years old. Each is worth a comment
asking one specific question rather than being closed silently. #115 is above,
with its question drafted: the message defect behind it is fixed, and what is
left to ask is about the mismatched PyOpenGL and accelerate versions in the
report.

**Not a defect.** #58 (an empty ticket), #63 (answered: constants carry a
`.name`), #64 (a Windows-versus-WSL report with no traceback, code or version in it), #65 and #69 (pyrender's pin, which only pyrender can change), #72
(fixed in CPython 3.8.10 and 3.9.1), #111 (a download script in another
project), #157 (a proposal to ship the generated modules as a zip — worth
discussing, not a bug), #163 (a suggestion to use pyMSVC), #164 (ClamAV
flagging two shipped DLLs as a packer, which is a false positive but worth
answering since it will recur).

## Counts

| | |
|---|---|
| Fixed, with a test that was red first | 23 tickets |
| Held fixed, with a test red against the reporter's release | 26 tickets |
| Not reproducible, with what was tried recorded | 4 tickets |
| Answered, with a case keeping the answer true | 2 tickets |
| Not a defect, answered on the ticket | 10 tickets |
| Deferred to a platform, other hardware, or the reporter | 15 tickets |
| **Open on the tracker** | **80 tickets** |

Defects found while writing the tests, which no ticket had reported: the
silent half of #3 (an integer offset accepted and read as an address), the
silent half of #33 (per-context storage never finding what it stored, growing
without bound), three OSMesa entry points whose declarations disagreed with
themselves, one generated wrapper naming a parameter that does not exist, and
a WGL `except AttributeError` guarding a lookup that sat outside its `try`.
