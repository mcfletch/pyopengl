# Registry-generated C dispatch

**Status:** Proposed. A working prototype exists and is measured; nothing has
landed. Replacing the ctypes call path with C generated from the Khronos
registry, at measured parity with an empty Python function call. Two questions
that were open when the prototype was written — buffer release discipline and
return-value conversion — are answered here.

**Scope:** the ~3,500 registry-defined entry points in `OpenGL/raw`. GLU, GLUT
and GLE are out of scope and stay on ctypes.

**Four requirements the design is held to**, each with its own section and its
own tests:

1. **The C is the implementation of the friendly API**, not a fast substrate
   under a Python one. No `wrapper.wrapper` on the call path and no Cython
   accelerator standing in for it.
2. **N contexts live in one process, each holding its own entry point for every
   function.**
3. **New array element types remain addable**, both from the registry and by
   client registration.
4. **Every capability the transition costs is enumerated** rather than
   discovered later.

## Why

A GL call through PyOpenGL costs roughly 500 ns, and roughly 470 ns of that is
the binding, not the driver. On the reference machine below, the driver's
`glBindTexture` takes about 11 ns. The engine sits on top of this, so the cost is
paid by every client of every library in the stack, on every call, forever.

Reference machine for every number in this document: Intel i7-12700, NVIDIA
GeForce RTX 3060 Ti, driver 580.173.02, GLX via GLFW, CPython 3.12.3,
`OpenGL_accelerate` installed and active.

| call | ns | ns with `ERROR_CHECKING=False` |
|---|---|---|
| `GL.glBindTexture` (friendly wrapper) | 498 | 350 |
| `raw.glBindTexture` (ctypes + errcheck) | 477 | 332 |
| bare `CFUNCTYPE` on the same proc address | 319 | 312 |
| `GL.glUniformMatrix4fv` (numpy 4×4) | 1216 | 1089 |
| `raw.glUniformMatrix4fv` (numpy 4×4) | 823 | 656 |
| empty Python function, same call site | 33 | — |

Floors on the same machine: ctypes call to `abs(int)` 210 ns, cffi ABI mode
132 ns.

## What is true today

Three separable costs, largest first.

**ctypes marshalling, ~280 ns per scalar call.** `PyCFuncPtr.__call__` rebuilds
argument conversion generically every time: a `PyCArgObject` per argument, an
`ffi_cif` walk, a per-call `argtypes` check. It is not specialisable. Against an
11 ns driver call it is about 97% of the cost of `glBindTexture`.

**Error checking, ~140 ns per call.** A real `glGetError` round-trip after every
entry point. It is also decided at binding-construction time, so assigning
`OpenGL.ERROR_CHECKING` at runtime has no effect on functions already bound.

**Array marshalling, ~430 ns per call** for a numpy 4×4 above the raw call.
Turning `ARRAY_SIZE_CHECKING` and `STORE_POINTERS` off moves it by ~10 ns, so
this is the format-handler and converter chain itself rather than the safety
checks.

The `Wrapper`/`LateBind` layer costs ~10–20 ns for scalar calls.
`OpenGL_accelerate` has already taken what there is to take there.

Two structural facts shape the design:

- **3,508 unique commands** across 5,300 definitions (the difference is aliases
  and vendor-suffixed variants) in 1,431 `OpenGL/raw` modules. 1,101 distinct
  Python-level signatures; 476 distinct ABI signature classes once pointer types
  collapse to `void *`; maximum arity 23.
- `import OpenGL.GL` costs 48 ms and 24 MB for 183 modules. Importing the whole
  `OpenGL.GL.*` tree costs 188 ms and 74 MB for 648 modules.

**Function pointers are bound once per process, not per context.**
`constructFunction` resolves a proc address and `_NullFunctionPointer.load()`
installs it on the class permanently. Where two contexts differ in capability —
a discrete-GPU context beside a software one, a 4.6 core context beside a 2.1
compatibility one, GLES beside desktop GL — whichever context resolved first
determines the binding for the whole process. This is a correctness defect
independent of speed.

## The design

One extension module containing one generated C function per entry point,
written as macro invocations, dispatched through a per-context slot table.

A generated entry point reads:

```c
static PyObject *
pygl_glUniformMatrix4fv(GLProc *self, PyObject *const *_a, size_t _nargsf)
{
    GL_ENTER(4);
    GL_I(0, location);
    GL_SZ(1, count);
    GL_B(2, transpose);
    GL_ARRAY(3, value, 'f');
    GL_CONV_OK();
    GL_FP(void (*)(GLint, GLsizei, GLboolean, const void *))
        (location, count, transpose, value);
    Py_RETURN_NONE;
}
```

The whole macro vocabulary is `GL_ENTER` (arity check), about a dozen scalar
converters (`GL_U`, `GL_I`, `GL_SZ`, `GL_F`, `GL_D`, `GL_B`, `GL_Q`),
`GL_ARRAY`, `GL_CONV_OK` (one `PyErr_Occurred()` after the bulk of the scalar
conversions rather than a branch per argument), and `GL_FP` (slot load and
cast).

The callable is one extension type with `tp_vectorcall_offset` set:

```c
typedef struct {
    PyObject_HEAD
    vectorcallfunc  vectorcall;   /* the generated stub */
    uint16_t        slot;         /* index into the per-context dispatch table */
    const GLCommand *info;        /* name, argNames, argtypes, restype, extension */
} GLProc;
```

### Measured

The prototype implements the above for `glBindTexture` and
`glUniformMatrix4fv`, including the arity and array-dtype checks:

| | current | prototype | |
|---|---|---|---|
| `glBindTexture(GL_TEXTURE_2D, 0)` | 498 ns | **43 ns** | 11.6× |
| `glUniformMatrix4fv(loc, 1, False, numpy 4×4)` | 1216 ns | **80 ns** | 15.2× |

With the slot pointed at an empty C function, so that the driver's contribution
is removed:

| | ns |
|---|---|
| stub → no-op C function, two scalar arguments | 31.7 |
| **empty Python function, same call site** | **33.0** |
| stub → no-op C function, three scalars and an array | 69.3 |

Dispatch through the abstraction costs what calling an empty Python function
costs. What remains is CPython's call protocol; the arity check, the
conversions, the thread-local slot load and the indirect call are together below
the noise floor of the measurement. Buffer acquisition for a numpy array is
about 37 ns, against ~430 ns for the current handler chain.

### Scale

One C function per entry point, generated for all 3,508 commands from the real
signature distribution:

| | |
|---|---|
| generated C | 36,198 lines, 1.2 MB |
| compile, `gcc -O2`, single translation unit | **7 s** |
| `.text` | **618 KB** (~176 bytes per entry point) |
| stripped shared object | 861 KB |

Seven seconds and 600 KB. An earlier draft of this design proposed 476
signature-class routines plus a per-command descriptor of argument-kind bytes,
to hold code size down. The measurement removes the reason for it. One function
per entry point is chosen instead because it is better on the axis that matters
over a decade of registry churn: the generated file is greppable and diffable, a
registry update produces a diff where each new function is one readable block,
and an entry point needing something unusual gets a hand-written body sitting
inline beside the generated ones with no table plumbing.

Split the output by API (GL, GLES, EGL, GLX, WGL) into a handful of translation
units so wheel builds parallelise.

### Alternatives, and why not

- **SWIG** — generates from C headers rather than `gl.xml`, and every decision
  that matters here (array element types, output parameters, per-context
  dispatch) would be re-expressed as typemaps duplicating `wrapper.py` in a
  language less suited to it.
- **cffi** — ABI mode is 132 ns, better than ctypes and far worse than 43 ns.
  API mode gives up the runtime pointer rebinding per-context dispatch needs.
- **Cython for all entry points** — Cython emits substantial C per `def`;
  3,508 declarations would be written to express what a dozen macros express.
  Cython keeps its place in `accelerate/` for the format handlers and VBO, which
  serve the array fall-through path; the wrapper, latebind and error-checker
  accelerators go away with the Python layer they accelerate.
- **Rust** — `extern "C"` calls from Rust are free, so the objection is not FFI
  cost. It is that every stub body is a transmuted raw function pointer and a
  `Py_buffer`, so the whole thing is `unsafe` and Rust's safety model has
  nothing to work with; PyO3's argument extraction lands about where hand-written
  C does; and it adds a toolchain to cross-platform wheel builds. PyOpenGL owns
  about eleven nanoseconds of indirect call, which is not enough work to justify
  it.

## Per-context dispatch

The requirement is N live contexts in one process, each with **its own function
pointer for every entry point**, resolved in that context and never shared with
another. This is not a hypothetical: `wglGetProcAddress` returns
context-specific pointers by specification, and a process holding a
discrete-GPU context beside a software one, or a 4.6 core context beside a 2.1
compatibility one, or GLES beside desktop GL, gets genuinely different addresses
for the same name.

### The structure

```c
typedef struct {
    void      *slots[GL_COMMAND_COUNT];   /* one entry point per command */
    uint8_t    flags[GL_COMMAND_COUNT];   /* per-slot error-check bit, etc. */
    void      *handle;                    /* the platform context handle */
    unsigned   generation;
} GLDispatch;

extern __thread const GLDispatch *gl_current;   /* initial-exec TLS */
#define GL_SLOT(i) (gl_current->slots[(i)])
```

`GL_FP` reads `gl_current->slots[self->slot]`: one TLS load, one indexed load,
below the measurement floor. At the current command count a table is 28 KB of
pointers plus 3.5 KB of flags — 32 KB per context, so a hundred contexts cost
3 MB.

**One `GLProc` object, N tables.** `OpenGL.GL.glBindTexture` is a single
process-wide Python object holding a *slot index*, never an address. Everything
that varies per context lives in the table. This is what lets the module-level
names, the virtual packages and any binding a client has already captured in a
local variable all remain correct when the current context changes — including
the common pattern of hoisting a binding into a local for a tight loop.

### Lifecycle

- **Creation.** A table is allocated on the first call made under a context
  handle the layer has not seen, with every slot pointing at `resolve_stub`.
  Tables are keyed by the platform context handle in a process-wide map.
- **Resolution.** `resolve_stub` runs the existing
  `getExtensionProcedure`/`checkExtension` logic *for the current context*,
  writes the resulting address into that context's slot, and re-dispatches.
  Absent functions get `null_stub`, which raises `NullFunctionError`. These are
  today's latebind semantics, in C, at no steady-state cost — and per context,
  so a resolution in one context can never determine another's binding.
- **Switching.** The platform layer assigns `gl_current` wherever it already
  observes `makeCurrent`, which is where `contextdata` is keyed. Assignment is a
  pointer store.
- **Destruction.** `contextdata.cleanupContext` already exists and already runs
  on context teardown; freeing the dispatch table joins it. A `generation`
  counter guards against a handle being reused by the driver for a new context:
  a table whose generation does not match is discarded and rebuilt rather than
  inherited.
- **No current context.** `gl_current` initialises to a static table whose every
  slot is `no_context_stub`, raising `error.NoContext`. This subsumes
  `CONTEXT_CHECKING` and its `_CheckContext` wrapper, and it is on always
  because it costs nothing — an improvement on today, where the check is off by
  default because it is expensive.

### Threads

The design is thread-correct because it matches how GL itself works: a context
is current *per thread*, and `gl_current` is thread-local, so two threads
rendering into two contexts simultaneously each dispatch through their own
table with no synchronisation on the call path.

The table *contents* are shared state only in the case where one context is
made current on different threads at different times, which the GL already
serialises. The one place needing care is the process-wide handle→table map:
lookups and insertions take a lock, but that is on the `makeCurrent` path, not
the call path. Slot writes are single-word stores of a value every writer would
compute identically, so a benign race writes the same address twice.

### The Python-visible consequences

Per-context dispatch has to reach the Python surface, not just the C one:

- **`bool(glFoo)` becomes a question about the current context.** Today it
  resolves once and caches for the process. Under the table it consults the
  current context's slot, so the same expression correctly answers `True` in a
  context that has the extension and `False` in one that does not. This is a
  behaviour change, and it is a fix; it is called out in the losses inventory
  below because code that caches the answer across a context switch was
  previously "right" by accident.
- **`glInitXxxARB()` and `extensions.hasGLExtension`** likewise answer for the
  current context. `checkExtension` already caches per context in `contextdata`;
  that cache and the dispatch table become two views of one fact.
- **Testing needs two contexts of differing capability in one process**, which
  is a fixture the suite does not have today. Building it is part of Phase 3,
  not an afterthought: a core context and a compatibility context, and where the
  platform allows it, contexts on two different drivers.

## Virtual packages

`OpenGL.GL.ARB.vertex_buffer_object` becomes a `MetaPathFinder` that builds the
module from the command and enum tables on demand: constants, `GLProc`
instances, `_EXTENSION_NAME`, `glInit…` predicate. The module object is real and
cached in `sys.modules`, so `from … import *` is unchanged. What goes away is
1,431 files being compiled, executed and kept resident.

Two constraints:

- **The `OpenGL/GL/*.py` files are not purely generated.** They carry
  hand-written material below `### END AUTOGENERATED SECTION` — aliases, `glget`
  registrations, exceptional wrappers — in 1,299 files. The finder must consult a
  real file first and let it extend the virtual module. In practice: keep real
  files for modules with hand content, synthesise the rest. The generator already
  distinguishes them, since it already preserves that section.
- **Packaging.** `pkgutil.walk_packages`, `importlib.resources` and PyInstaller
  need the finder to enumerate. The plug-in-driven PyInstaller hook grows a case
  for the virtual namespace.

This phase is gated on moving the hand-written annotations out of the generated
files and into a data file keyed by command name, so that regeneration never has
to preserve hand edits in place.

## Arrays

### The rule: the fast path may accelerate, never reject

What the current layer accepts for a single `GLfloatArray` parameter
(`glUniformMatrix4fv`), measured:

| passed | result |
|---|---|
| `float32` numpy | accepted |
| `float64` numpy | accepted, converted |
| `int32` numpy | accepted, converted |
| list of lists | accepted, converted |
| flat list | accepted, converted |
| `bytes` | accepted |
| `ctypes.c_float * 16` | accepted |
| `memoryview` | accepted |

Conversion, not rejection, is the contract. Callers rely on it: passing a
`float64` array to a `float32` uniform is ordinary client code, and the engine
does it.

The prototype gets this wrong — it raises `TypeError: expected array of 'f',
got 'd'`. That behaviour must not ship. The rule for the C path is:

> **Exact format match takes the fast path. Everything else — a different
> element type, a non-contiguous buffer, an object with no buffer protocol at
> all — falls through to `ArrayDatatype` and the format-handler registry, which
> behaves exactly as it does today. The C layer never raises on an argument the
> Python layer would have accepted.**

So the C code is a *match test*, not a *validation*. A mismatch is a cheap
`goto slow_path`, not an error. The only thing the fast path can raise is what
the Python path would also have raised, and it raises it by delegating.

### New element types

Two independent extension routes, both of which stay open:

**New GL types from the registry.** `OpenGL/arrays/arraydatatype.py` defines 18
array classes today — `GLfloatArray`, `GLdoubleArray`, `GLfloat16Array`,
`GLfixedArray`, `GLint64Array`, `GLuint64Array` and the rest. When Khronos adds
an element type, the generator adds a row to the element-type table:

```c
typedef struct {
    const char *buffer_format;   /* struct-module code, e.g. "f", "e", "q" */
    uint8_t     itemsize;
    uint16_t    datatype_index;  /* the ArrayDatatype subclass for the slow path */
} GLElementType;
```

The generated stub names an index into that table; `GL_ARRAY` compares
`view.format` against `buffer_format` and, on any mismatch, hands the object and
the `datatype_index` to the Python handler chain. **A new element type is a new
table row plus a new `ArrayDatatype` subclass. It needs no new C code and no
change to any generated stub.** An element type whose buffer format is not
expressible as a `struct` code simply gets an empty `buffer_format`, which never
matches, which means every call for it takes the existing Python path — correct,
if unaccelerated, from the day the type appears.

**Client-registered types.** The `FormatHandler` plug-in registry has twelve
entries today (`none`, `bytes`, `str`, `list`, `numbers`, `ctypesarrays`,
`ctypesparameter`, `ctypespointer`, `numpy`, `buffer`, `vbo`, `vbooffset`) and
third parties register their own — a VBO-like object, an array library other
than numpy, a GPU buffer wrapper. Because mismatch means fall-through rather
than error, **a client type registered today keeps working under the C path with
no change and no knowledge of it.** If such a type also exports a buffer with a
matching format, it gets the fast path for free.

This is the property that makes the design safe: the C layer's knowledge of
array types is an optimisation table, and the authority on what is acceptable
stays in Python where clients can extend it.

### Where the retained Python layer sits

`ArrayDatatype`, the handler registry and every existing handler stay exactly as
they are, as the fall-through path and the extension point. The friendly API
built on top of them moves into C — see the next section.

## The C layer is the friendly API

The target is not a fast raw layer with Python friendliness on top. **The
generated C is the implementation of the API clients already use** —
`OpenGL.GL.glGenTextures(n)` returns an array because a C stub allocated it,
not because a Python wrapper wrapped a C stub. No `wrapper.wrapper` on the call
path, no Cython accelerator standing in for it.

This is achievable because the friendly layer is far more regular than its
2,700 customisation calls suggest. The census, over everything outside
`OpenGL/raw`:

| customisation | uses |
|---|---|
| `setInputArraySize` | 2,029 |
| `setOutput` | 687 |
| `setPyConverter` | 39 |
| `setCConverter` | 21 |
| `setReturnValues` | 13 |
| `setStoreValues` | 8 |
| `setImageInput` | 8 |
| `setDimensionsAsInts` | 7 |
| `setCResolver` | 4 |

Of 3,705 unique commands, **2,135 (57.6%) carry no customisation at all.** Of
the 2,716 calls in the two dominant methods, all but a handful fall into five
mechanical forms.

### Tier 1 — pass-through (2,135 commands)

Nothing to convert. The generated stub as already described.

### Tier 2 — declarative annotations (2,713 of 2,716 calls)

Each of these is **data in the descriptor table**, interpreted by the generator
and compiled into the stub. None of them needs code written per entry point.

| form | uses | what it becomes |
|---|---|---|
| `setInputArraySize(name, None)` | 1,353 | nothing — it marks a parameter as an unchecked input array, which is already the default. It exists to document that the size *could* have been checked against another argument. |
| `setInputArraySize(name, N)` | 673 | one integer per parameter; C compares `view.len / itemsize` against it. |
| `setOutput(name, size=(N,), orPassIn=True)` | 206 | one integer per parameter; allocate an output array of that length, or write into the caller's if one was passed. |
| `setOutput(..., size=lambda x: (x // k,), pnameArg=…)` | 196 | one argument index and one divisor. **The entire lambda space is three bodies:** `(x,)` ×188, `(x//4,)` ×6, `(x//8,)` ×2. |
| `setOutput(..., size=_glgets…, pnameArg=…)` | 285 | a lookup in the generated `_glget_size_mapping` table — 2,215 entries — keyed on the pname argument. In C, a static sorted table and a binary search. |

The three `setInputArraySize` calls outside these forms are hand cases and join
Tier 3.

Two details this tier has to carry: `orPassIn=True` (accept a caller-supplied
output array and return it, rather than allocating) appears on every
`setOutput`, so it is the normal path, not an exception; and some `_glgets`
sizes are a `LookupInt`, meaning the size itself comes from a runtime
`glGetIntegerv`. The C table stores those as "resolve by querying pname P" and
the stub makes the query.

### Tier 3 — closed families that need real C (~100 calls, 5 areas)

Every hand-written converter in the tree lives in eleven files, and they group
into five families. Each is a genuine computation, each is fully specified, and
each gets hand-written C sitting inline in the generated file beside the
generated stubs.

**(a) Output strings** — `glGetShaderInfoLog`, `glGetProgramInfoLog`,
`glGetActiveUniform`, `glGetActiveAttrib`, `glGetShaderSource` and relatives.
Query the length, allocate, call, trim to the returned length, hand back
`bytes`. Currently `setPyConverter`/`setCConverter`/`setCResolver` in
`GL/VERSION/GL_2_0.py`, `GL/ARB/shader_objects.py`, `GLES2/VERSION/GLES2_2_0.py`
(6 calls each). One C helper serves the family.

**(b) Input string arrays** — `glShaderSource`. A `str`, or a list of them,
becomes `char **` plus a `GLint *` of lengths. Currently `conv.stringArray` and
`conv.totalCount`. One C helper.

**(c) Pixels and images** — `glTexImage1D/2D/3D`, `glTexSubImage*`,
`glReadPixels`, `glDrawPixels`, `glCompressedTexImage*` and the `ARB/imaging`
set. The output or input size is a function of `format`, `type`, the
dimensions, and the current pixel-store state. `GL/images.py` (630 lines),
`GL/ARB/imaging.py` and `GL/VERSION/GL_1_2_images.py` hold it today, via
`setImageInput` ×8 and `setDimensionsAsInts` ×7. This is the largest genuine
computation in the friendly layer, it is specified by the GL spec rather than
inferred, and it sits on the texture-upload path — so it is both the most work
and the most worth doing.

**(d) Client-side array pointers** — the `glVertexPointer` /
`glTexCoordPointer` / `glVertexAttribPointer` family. `GL/pointers.py` (308
lines, 39 calls, and every `setStoreValues` in the tree). The array must outlive
the call, which is the retain annotation already decided under buffer release;
this family is where it is used. The retention itself is a `contextdata` write,
which the C layer performs against the current context's table rather than
through Python.

**(e) Variadic dispatch** — `glVertex`, `glColor`, `glNormal`, `glRasterPos`,
`glMaterial`, `glTexParameter`, `glCallLists`, `glMap1`, `glMap2`, and the
variadic `glDeleteTextures`. `GL/exceptional.py` (264 lines) dispatches on
argument count and type to one of several real entry points, via
`lazywrapper.lazy` rather than `wrapper.wrapper`. In C this is a dispatcher stub
that inspects `nargs` and the argument types and tail-calls the appropriate
generated stub — the same decision, made faster, in the same place. The
`lazywrapper` mechanism has twenty other uses across the tree, each a
hand-written Python function curried over a base function; they are enumerated
and converted individually with the family they belong to.

### Tier 4 — stays Python, deliberately

The line: **anything that wraps a single entry point becomes C; anything that
composes several entry points into a convenience object, or is the registry
clients extend, stays Python.**

- `OpenGL.GL.shaders` — `compileShader`, `compileProgram`, `ShaderProgram`.
  These are a helper library built *on* entry points, not a wrapper *of* one.
- `OpenGL.arrays.vbo.VBO` — a class with its own lifecycle and buffer
  management.
- `ArrayDatatype`, `formathandler` and the twelve registered handlers — the
  extension point required by the array-type rule above. Putting this in C would
  close the door the arrays section deliberately holds open.
- `OpenGL.GL.feedback`, `OpenGL.GL.selection`, `OpenGL.GL.framebufferobjects`,
  `OpenGL.GL.vboimplementation` — small helper libraries and compatibility
  shims.
- The plug-in, platform and `contextdata` machinery.

`OpenGL/wrapper.py` is a fifth case: **it stops being on PyOpenGL's call path
but stays a supported public facility**, because third parties use
`wrapper.wrapper()` to wrap their own extension functions. It keeps working,
over the ctypes callable, for anyone who does that.

### What this deletes

Once C implements the friendly API, these have no remaining role on the call
path:

- `OpenGL/latebind.py` and `OpenGL/lazywrapper.py` — replaced by the slot table
  and by generated dispatcher stubs.
- `OpenGL_accelerate`'s `wrapper.pyx`, `latebind.pyx`, `errorchecker.pyx` and
  `arraydatatype.pyx` — they exist to make the Python wrapper layer cheaper, and
  there is no Python wrapper layer left to make cheaper.
- `OpenGL/wrapper.py`'s runtime machinery — `finaliseCall` and the nested
  closure explosion it builds. The authoring vocabulary survives as the
  annotation data the generator consumes, and the module survives for third
  parties.

`OpenGL_accelerate` reduces to the format handlers (`formathandler.pyx`,
`numpy_formathandler.pyx`, `buffers_formathandler.pyx`,
`nones_formathandler.pyx`, `vbo.pyx`), which serve the array fall-through path
and stay useful.

### The clean final model

Every entry point is described by one record, and everything above is a field
in it:

```
command  := name, feature, deprecated, return-kind, [parameter]
parameter := name, c-type, direction, size-spec, retain?, element-type?
direction := in | out | in-out
size-spec := none | fixed(N) | from-arg(index, divisor)
           | glget-table(pname-arg) | image(format-arg, type-arg, dims)
           | string-array | computed(<one of the Tier 3 helpers>)
```

The generator turns records into stubs; the registry supplies most fields; the
annotation data file supplies `direction`, `size-spec` and `retain`. There is
one description of each entry point, in one place, and both the C and the `.pyi`
are derived from it. That is the modelling outcome this section exists for: the
friendly API stops being 2,716 imperative customisation calls scattered across
296 files and becomes a table.

### Consequences to design for

- **Output arrays are allocated in C.** `glGenTextures(n)` returns a numpy
  array today, so the C path allocates through numpy's C API for the default
  array module and calls back into Python for any other configured module. The
  returned object must be indistinguishable from today's, which the differential
  harness checks by type and by value.
- **`contextdata` is written from C** on the retain path. It stays a Python
  module; the C side calls into it, which is acceptable because the retain path
  is not the hot path.
- **The annotations must move out of the generated files before any of this**,
  into the data file keyed by command name. This is already Phase 6's
  precondition for virtual packages; the friendly-API conversion needs it too
  and needs it earlier.

## Error checking

Two changes:

- Move the flag from binding-construction time to **a per-slot byte in the
  dispatch table**, so `OpenGL.ERROR_CHECKING = True` takes effect at runtime and
  can be scoped to one context or one entry point. A predictable branch is ~1 ns;
  the cost is the `glGetError`.
- Prefer **`GL_KHR_debug` / `glDebugMessageCallback`** where the context offers
  it: no per-call cost, and the message identifies the offending call rather than
  being attributed after the fact. Per-call `glGetError` remains for contexts
  without it.

## Decided: buffer release discipline

`PyObject_GetBuffer` raises the exporter's export count. Failing to release
blocks `numpy` resize, blocks `memoryview.release()`, and leaks a reference. The
prototype gets this wrong: `GL_ARRAY` releases its own buffer when *it* fails,
but if a later argument fails, an earlier successfully acquired buffer leaks.
Functions with two or more array parameters are ordinary —
`glPrioritizeTextures(n, textures, priorities)`, most of `glMultiDraw*` — so
this is a live case, and the macro layer gets it right 3,508 times or wrong
3,508 times.

**Decision.** The generator emits one shape for every entry point:

1. All scalar conversions first, in declaration order, then a single
   `GL_CONV_OK()`. Scalar conversion cannot fail *destructively*, so nothing
   needs unwinding at this point.
2. Then array acquisitions, into a generated frame array with a count:

```c
GLBuf _bufs[N]; int _nb = 0;
#define GL_ARRAY(i, name, fmt) \
    if (gl_as_array(_a[i], fmt, &_bufs[_nb]) < 0) goto _fail; \
    const void *name = _bufs[_nb++].view.buf
...
_fail:
    while (_nb) gl_release(&_bufs[--_nb]);
    return NULL;
_done:
    while (_nb) gl_release(&_bufs[--_nb]);
```

3. The call, then fall through to `_done`.

One counter increment per array argument, one uniform cleanup path, no
per-function labels for the generator to get creative with. Functions with no
array arguments get neither the frame array nor the labels.

Reordering scalars before arrays is free — the conversions are independent, and
the call passes them in signature order regardless.

The same frame carries the fall-through case. When `gl_as_array` does not match
and delegates to the Python handler chain, what comes back is an owned object —
often a freshly converted array — whose lifetime must cover the call. It goes
into the same frame slot as a strong reference, and the same `_fail`/`_done`
loop drops it. One cleanup path for both, which is the reason to have a frame at
all rather than per-argument releases.

**Related decision: pointers that outlive the call.** Releasing the buffer at
return is correct for immediate-use calls and wrong for the pointer-registering
family — `glVertexPointer`, `glTexCoordPointer`, `glVertexAttribPointer` with a
client array, `glDrawElements` with a client-side index array — where the GL
reads the memory after the call returns. That is what `STORE_POINTERS` and
`contextdata` exist for today. The generator needs a per-parameter *retain*
annotation, sourced from the same data file as the other hand annotations; a
retained parameter keeps the object and its buffer view alive in `contextdata`
against the current context instead of releasing at return. Losing this is a
segfault, not a leak, so the differential harness must cover it explicitly:
draw from a client-side array, drop the Python reference, collect, draw again.

## Decided: return-value conversion

The governing rule is that **the new layer returns the same Python object the
ctypes layer returns today**, and the differential harness is what enforces it
rather than anyone's recollection. Current behaviour, measured:

| call | returns | type |
|---|---|---|
| `glIsTexture(0)` | `0` | `int` |
| `glGetError()` | `0` | `int` |
| `glGetString(GL_VENDOR)` | `b'NVIDIA Corporation'` | `bytes` |

**Decisions:**

- `void` → `Py_RETURN_NONE`.
- Integer types → `PyLong_FromLong` / `FromLongLong` / `FromUnsignedLongLong`.
  Plain `int`.
- **`GLboolean` returns stay `int`, not `bool`.** `bool` is defensible and would
  be a gratuitous break; `glIsTexture` returns `0` today and will return `0`.
  Changing it is a separate, deliberate API decision, not a side effect of this
  work.
- **`GLenum` returns stay plain `int`, not `Constant`.** That is what they are
  today.
- **Pointer returns get hand-written bodies.** `glGetString` →
  `bytes`, `glMapBuffer` → the existing pointer object, `GLsync` → the existing
  opaque type from `_opaque.py`. These are a handful of functions; they sit in
  the generated file as hand-written entries.
- **`GLhandleARB` is `void *` on macOS and `unsigned int` elsewhere.** The
  generator emits this one platform-conditionally. It is the only such
  divergence in the registry and it is worth a named test.

**Decision on exception types.** Bad scalar arguments currently raise
`ctypes.ArgumentError`; wrong arity raises `TypeError`. A C stub would naturally
raise `TypeError` for both. Since compatibility is the point of this exercise,
the stub raises `ctypes.ArgumentError` for argument-conversion failures, from a
reference cached at module init. Message text is explicitly *not* part of the
contract (see below).

## Type declarations and docstrings

Both come off the same pass, from the same command record.

### Type declarations

The registry supplies parameter names and types; the annotation data file
supplies the friendly signature, so both forms are derivable:

```python
def glUniformMatrix4fv(location: int, count: int, transpose: bool,
                       value: SupportsFloat32Array) -> None: ...
def glGenTextures(n: int) -> NDArray[uint32]: ...
```

The second is the one that makes stubs worth shipping rather than merely
possible, and it exists because the `size-spec` and `direction` fields already
record which parameter becomes the return value. Narrowing `GLenum` parameters
via the registry's `<group>` attribute is later work.

### Docstrings

**Entry points have no docstring today** — `glBindTexture.__doc__` is `None`.
Everything here is new capability rather than preserved capability, so there is
no compatibility risk and no reason to do it by halves. Two parts, with
different sources and different risk.

**The signature line, unconditionally.** Buildable from the command record
alone, with no external source:

```
glBindTexture(target, texture) -> None
glGenTextures(n) -> textures
```

The same string goes into `__text_signature__`, so `inspect.signature()` — which
raises today — answers for every entry point, and IDE and REPL introspection
work without importing anything.

**The purpose line, gated on licensing.** `gl.xml` carries no prose: the
registry has zero `<refpurpose>` or equivalent elements, so per-function
descriptions have to come from the Khronos OpenGL-Refpages, which is a separate
repository of DocBook XML and is not vendored here.

Before any of it is vendored or read, **its licensing must be determined
per-file and recorded**, under [CLEAN-ROOM.md](../CLEAN-ROOM.md). The refpages
carry a mix of licences across files; some of what Khronos publishes is
permissive and some is not, and CC-BY-SA in particular is named in the workspace
rules as forbidden to copy. This is a gate, not a formality:

- If a file's licence is permissive and attribution-compatible with our BSD
  terms, its `<refpurpose>` may be vendored, with attribution, and emitted into
  the generated C and the `.pyi`.
- If it is not, that command gets its signature line and nothing else. A missing
  purpose line is a small loss; a licence violation in a 28-year-old library
  that other people ship is not a recoverable one.
- The determination is recorded in a spec file under `specs/` and cited from the
  generator, so the next person does not have to re-derive it.

There is precedent to follow rather than invent: the generator already extracts
`Overview (from the spec)` prose into extension module docstrings from the
extension text files vendored under `src/khronosapi/extensions/`. Whatever
determination was made for those is the starting point, and if none was
recorded, recording it is part of this work.

**Where the strings live.** In the C, as a static string per command exposed
through a `__doc__` getset on `GLProc`. About 3,500 short strings is on the
order of 200 KB of `.rodata`, it costs nothing until something reads it, and it
means `help(glBindTexture)` works at an interactive prompt with no stub files
present. The same strings are emitted into the `.pyi` so that editors show them
without importing PyOpenGL at all.

## Registry currency and coverage

Everything above is generated in one pass from the vendored registry, which
makes these cheap:

- **Coverage is a test.** Walk `gl.xml`, `gles*.xml`, `egl.xml`, `glx.xml` and
  `wgl.xml`; assert every `<command>` in every `<feature>` and `<extension>` has
  a binding with a matching signature, and every `<enum>` has a constant with a
  matching value. Complete registry coverage becomes a red test when it lapses
  rather than a claim. `src/checkdefs.py` is the ancestor of this; it checks that
  modules import, not that they are complete.
- **A scheduled regeneration job** pulls the registry, regenerates, runs the
  suite and opens a PR whose body is the diff summary: new enums, new commands,
  new extensions, and — the one line needing a human — any command whose
  generated body is not a pure macro expansion.
- **Provenance in the artifacts.** Generated files carry the registry commit
  hash and generator version, so the question "which registry is this wheel
  built from" is answerable from an installed wheel.

## Migration and compatibility

### The compatibility contract

Written down before any code moves, published in the documentation, and asserted
by tests.

**Preserved.** Every public name in every `OpenGL.*` module, at the same import
path. Call signatures and return values. `bool(glFoo)` with resolve-on-test
semantics. The attributes clients and `wrapper.py` read from a binding:
`__name__`, `__doc__`, `argNames`, `argtypes`, `restype`, `DLL`, `extension`,
`deprecated`. Acceptability to `wrapper.wrapper(...)`,
`setOutput`/`setInputArraySize`/`setPyConverter`/`setCConverter`. The
`ArrayDatatype` and format-handler plug-in registries, including third-party
registrations. Exception *types*, including `ctypes.ArgumentError` for bad
arguments and `NullFunctionError` for absent entry points. The `OpenGL.raw.*`
namespace.

**Explicitly not preserved.** Enumerated in full in the next section. Nothing
belongs on that list that is not written there.

### What the transition costs

Every capability that is removed, degraded or changed, with what replaces it.
This list is the contract's other half, and it is meant to be complete: an item
discovered later that is not here is a defect in this plan, not an acceptable
surprise.

**Lost outright**

| capability | why | replacement |
|---|---|---|
| Per-call tracing via `OpenGL.FULL_LOGGING` | `logs.logOnFailDec` wraps the ctypes callable with a Python function that logs every call's arguments. There is no equivalent in a C stub that does not cost what the stub saves. | `FULL_LOGGING` selects the ctypes dispatch wholesale for the process. Tracing is a debugging mode, so paying the old cost while tracing is the right trade; it must be documented as switching dispatch, not merely adding logging. |
| Mutating `glFoo.argtypes` to change marshalling | Argument conversion is compiled into the stub. | Assignment demotes that one entry point to ctypes for the life of the process, as `errcheck` does. Reading `argtypes` is unaffected. |
| `module.__file__` on registry modules (Phase 6 only) | A synthesised module has no file. | `__spec__` is populated and `__file__` is set to the generator's source-of-record path where a tool needs something. Introspection tools that require a real file are named in the phase's test set. |
| Reading installed `.py` source to discover a signature (Phase 6 only) | The files stop existing for synthesised modules. | The `.pyi` stubs from Phase 7, `help()`, and `glFoo.argNames`, all of which are better sources. Phase 6 does not land before Phase 7 is at least drafted for this reason. |
| Monkeypatching a *converter* on a PyOpenGL entry point — reaching into `glFoo.pyConverters` or re-running `wrapper.wrapper()` over a shipped binding to alter its behaviour | The friendly behaviour is compiled in, not assembled at import. | `wrapper.wrapper()` over the ctypes callable, reachable through the demotion hatch. This was never documented as an extension point, but it is discoverable, so it is listed. |
| `OpenGL/latebind.py` and `OpenGL/lazywrapper.py` as importable modules | Nothing is left for them to do. | Both are kept as thin shims through one release with a deprecation warning, then removed. `wrapper.py` is *not* on this list — it stays supported. |

**Changed, deliberately**

| behaviour | today | after | rationale |
|---|---|---|---|
| Exception message text for argument errors | ctypes' wording | our wording | Types are preserved; text was never a contract, and matching ctypes' phrasing character-for-character would constrain the C layer for no benefit. |
| `repr()` of a binding | ctypes' or `_NullFunctionPointer`'s | `<OpenGL entry point glBindTexture>` | The old text is not useful and not documented. |
| `type(glBindTexture)` | `ctypes` function pointer subclass or `_NullFunctionPointer` | `GLProc` | Nothing documented depends on it. `isinstance` checks against `ctypes._CFuncPtr` in client code would break; the differential harness looks for this idiom in the canary projects. |
| `OpenGL.ERROR_CHECKING` assigned after import | no effect on already-bound functions | takes effect | A fix. Code that assigned it expecting nothing to happen now gets what it asked for. |
| `bool(glFoo)`, `glInitXxx()` | resolved once, cached process-wide | answered for the current context | A fix, and the point of the exercise. Code that cached the answer and then switched contexts was previously correct only by coincidence. |
| A call with no current context | undefined unless `CONTEXT_CHECKING` is on, which is off by default | always raises `error.NoContext` | The check became free, so it is always on. Code that relied on a no-context call silently doing nothing now gets an exception. |

**Explicitly *not* lost, though it might be assumed to be**

- **Array-type conversion.** `float64` for a `float32` parameter, lists, `bytes`,
  ctypes arrays, memoryviews — all still accepted and converted, because
  mismatch means fall-through, not error. See the arrays section.
- **The `FormatHandler` plug-in registry**, all twelve current handlers, and
  third-party registrations.
- **VBO offsets and `None` as a null pointer.**
- **Passing ctypes objects** — `c_void_p`, `byref`, ctypes arrays — which reach
  the existing handlers by fall-through.
- **`wrapper.wrapper(...)` with arbitrary `setPyConverter`/`setCConverter`.** A
  converter may legitimately produce a ctypes object the C stub cannot consume;
  a wrapper carrying custom C converters therefore binds to the ctypes callable
  rather than the stub. This is chosen at wrapper-finalisation time, once, not
  per call.
- **`glFoo.DLL`** stays the real ctypes library object, so
  `glFoo.DLL.somethingElse` keeps working.
- **`FORWARD_COMPATIBLE_ONLY`** and the deprecated-entry-point behaviour.
- **Every friendly-API behaviour** — `glGenTextures(n)` returning an array,
  `orPassIn` accepting a caller-supplied output, `glGetIntegerv(pname)` sizing
  its output from the pname, variadic `glColor`/`glVertex`, image size
  computation. These move into C; they do not change. That the implementation
  language changed is not a client-visible fact, and the differential harness is
  what keeps it that way.
- **`OpenGL.GL.shaders`, `OpenGL.arrays.vbo.VBO`** and the other helper
  libraries, which stay Python.
- **Docstrings** — gained, not lost. Entry points have `__doc__ = None` today.
- **Monkeypatching a module attribute** (`OpenGL.GL.glBindTexture = mine`),
  including on synthesised modules.
- **The ctypes implementation itself**, which is not scheduled for removal.

**The escape hatch.** Assigning `glFoo.errcheck = f` demotes that entry point to
the ctypes path for the life of the process. This keeps a genuinely used
debugging affordance working without putting a settable callback in the hot
path, and it gives anyone with an unanticipated need a per-function way out.

**The global escape hatch.** `PYOPENGL_DISPATCH=ctypes` selects the current
implementation wholesale, and keeps doing so after the default flips. The ctypes
path is the reference semantics, the bootstrap route for a new platform, and
what runs where no wheel exists; it is not scheduled for removal.

### Staging

Each phase is shippable, and each has an exit criterion that must hold before
the next begins. The ordering is set by dependency, not by appetite: the
annotation data comes first because everything else reads it, and the harness
comes before anything switches because it is what makes switching safe.

**Phase 0 — infrastructure, no behaviour change.** Generator backend, macro
header, `GLProc` type, build integration, one translation unit per API. The
module is built and importable but nothing uses it.
*Exit:* wheels build on every supported platform; `.text` and compile time
within the budget measured above.

**Phase 1 — annotation extraction.** Lift the hand-written material out of the
generated `.py` files into the data file keyed by command name, producing the
command record described above. A pure refactor of where the information lives,
with no behaviour change, and a precondition for Tier 2, for the `.pyi`, and for
virtual packages.
*Exit:* regenerating from the extracted annotations reproduces the current
generated tree **byte-identically**. That equality is the whole point of doing
this as a separate phase.

**Phase 2 — the differential harness.** Built before anything switches. Detail
below.
*Exit:* the harness runs both implementations over every entry point it can
reach and reports zero unexplained differences.

**Phase 3 — Tier 1 and the array path; the opt-in switch.** Pass-through entry
points working end to end, which requires the array fast path and its
fall-through, plus the retain annotation. `PYOPENGL_DISPATCH=c` selects the new
path; default stays `ctypes`. Ship it and say so in the release notes.
*Exit:* the array-acceptance matrix is identical under both settings; client
array lifetime tests pass; the full suite is green under both settings on every
CI platform.

**Phase 4 — Tier 2, the declarative annotations.** Fixed-size input checks,
constant and computed output sizes, and the `_glgets` table. This is the phase
that makes the C layer the friendly API for the large majority of commands.
*Exit:* every Tier 2 command differentially identical, including `orPassIn` with
and without a caller-supplied array, and including the `LookupInt` sizes that
require a runtime query.

**Phase 5 — Tier 3, one family per release.** Output strings, input string
arrays, pixels and images, client-array pointers, variadic dispatch. Each is
independently shippable and independently revertible, and each retires a
hand-written Python module when it lands.
*Exit, per family:* differentially identical, and the Python module it replaces
is unreferenced.

**Phase 6 — per-context dispatch table.** Fixes the process-global binding
defect. Brings with it the multi-context fixture the suite does not have today:
N contexts live in one process, each resolving its own entry points. At minimum
a core context beside a compatibility context; where the platform allows,
contexts on two different drivers, which is the case that actually produces
different addresses for the same name. Tests assert that a slot resolved in one
context does not appear in another's table, that `bool(glFoo)` and `glInitXxx()`
answer per context, that a binding hoisted into a local before a context switch
dispatches correctly after it, that a call with no current context raises
`NoContext`, and that tables are freed on context teardown.
*Exit:* the multi-context tests pass on all three platforms; no regression under
either dispatch setting.

**Phase 7 — error checking.** Per-slot flag and `KHR_debug`.
*Exit:* error-reporting tests pass under both mechanisms; runtime assignment of
`ERROR_CHECKING` is covered.

**Phase 8 — docstrings and `.pyi`.** Signature lines and `__text_signature__`
unconditionally; purpose lines only for commands whose source licence has been
determined and recorded.
*Exit:* `inspect.signature()` answers for every entry point; mypy and pyright
accept a corpus of real client code including the engine; the licence
determination is written down in `specs/` and cited from the generator.

**Phase 9 — virtual packages.**
*Exit:* the API-surface snapshot is unchanged; import time and resident size
improve; PyInstaller and `pkgutil.walk_packages` cases pass.

**Phase 10 — flip the default** to `c`, in a minor release, with the opt-out
documented. Ctypes remains selectable indefinitely.

**Phase 11 — retire what is dead.** `latebind.py` and `lazywrapper.py` behind a
deprecation warning; the `wrapper`, `latebind`, `errorchecker` and
`arraydatatype` modules removed from `OpenGL_accelerate`. `wrapper.py` stays.
*Exit:* nothing in the tree imports them, and the deprecation has shipped in at
least one prior release.

### Testing

**The differential harness** is the core instrument. For every entry point, with
both implementations loaded in one process:

- Call each with the same generated arguments and assert identical return values
  (value *and* type), identical exception types, and identical resulting GL
  state where the call has observable state.
- Generate arguments from the registry types: valid values, boundary values,
  wrong types, wrong arity, wrong array dtype, wrong array length, `None`.
- Compare `glGetError()` after each pair, so a call that succeeds in one
  implementation and faults in the other is caught even when both return `None`.
- Entry points that cannot be called blind (anything taking a live object name,
  anything that blocks, `glDebugMessageCallback` and friends) go on an explicit
  exclusion list with a stated reason, and each gets a hand-written case
  instead. The list is reviewed, not allowed to grow silently.

**The friendly-API equivalence tests.** The differential harness above compares
the two implementations of each entry point; these compare the *behaviour the
API promises*, which is what clients actually depend on. Per tier: every
fixed-size input check accepts the right length and rejects the wrong one
identically; every output-sizing form returns an array of the same length and
dtype, both allocating and with `orPassIn`; every `_glgets` pname returns the
size the table says, including the `LookupInt` ones; and for Tier 3, a
hand-written case per family — an info log longer than any guess, a
`glShaderSource` with one string and with a list, a `glReadPixels` at every
combination of format and type with a non-default `glPixelStorei` alignment, a
client array that outlives its Python reference, and each variadic form at every
arity and argument type it accepts.

**The array-acceptance matrix.** For every array parameter kind, every input
form crossed with every implementation: matching dtype, every non-matching
numeric dtype, flat list, nested list, `bytes`, `bytearray`, `array.array`,
`memoryview`, non-contiguous slice, ctypes array, ctypes pointer, `c_void_p`,
`byref`, VBO, VBO offset, integer offset, `None`, and an object from a
test-registered third-party `FormatHandler`. Assert the same acceptance, the
same conversion result and the same exception where one is raised. This is the
test that holds the "accelerate, never reject" rule in place, and it is the one
that would have caught the prototype's dtype rejection immediately.

**The multi-context tests** described in Phase 3, run under both
implementations so that the per-context answers can be compared against the
process-global ones and each difference accounted for deliberately.

**The attribute-surface test.** For every binding under both implementations,
assert the same set of public attributes with the same values. This is what
catches a client reading `argNames` or `restype` that no functional test would
touch.

**The API-surface snapshot.** Serialise every public name in every `OpenGL.*`
module, with its kind and — for callables — its argument names, to a checked-in
file. A test asserts no unintended change. This is the safety net for the
virtual-package phase specifically, where a missing name is a silent
`ImportError` for someone else months later.

**The registry coverage test**, as described above, so completeness is asserted
at the same time as compatibility.

**The existing suite, under both implementations.** `PYOPENGL_DISPATCH` becomes
a CI matrix axis crossed with platform. Any test that passes under one and not
the other blocks the phase.

**The downstream suites.** This workspace is the integration bed and the root
`CLAUDE.md` already names OpenGLContext as PyOpenGL's primary test suite. Run
OpenGLContext, the forest demo, glisteel and twig-bb under both settings.
OpenGLContext's reference-image tests are the strongest end-to-end assertion
available: identical images under both dispatch paths exercises thousands of
calls with real arguments in real sequences, and it fails visibly rather than
subtly. Run these serially, per the workspace rule about concurrent GL suites.

**Third-party canaries.** Assemble a small set of public PyOpenGL-dependent
projects with usable test suites and run them under both settings before Phase 8.
The value is finding the attribute or idiom nobody here thought of; the list
should be named in the PR that proposes the flip.

**Memory and lifetime.** A dedicated pass under a leak check: buffer export
counts return to baseline after calls that take arrays, including the error
paths and including the multi-array functions from the buffer-release decision;
retained client arrays survive collection and are released when the context goes
away.

### Rollback

Each phase is behind either `PYOPENGL_DISPATCH` or its own flag, so rollback is
configuration rather than reversion, and a client hitting a problem in the field
has the same lever. Nothing in the plan removes the ctypes implementation, and
Phase 8 changes a default rather than deleting a path.

## Risks

- **A client depends on something in the losses inventory.** Mitigated by the
  long opt-in period, by the per-function demotion that covers `errcheck` and
  `argtypes`, and by `PYOPENGL_DISPATCH=ctypes` for everything else. The item
  most likely to be hit without warning is `isinstance` against a ctypes
  function-pointer type; the canary projects are searched for that idiom
  specifically.
- **The C layer rejects something the Python layer accepted.** The single
  largest compatibility hazard, because it is silent in review and loud in the
  field. The "accelerate, never reject" rule and the array-acceptance matrix
  exist for it, and any new C-level validation added later must be justified
  against that rule.
- **Buffer lifetime.** The failure mode is a crash rather than a wrong answer.
  This is why the retain annotation and its tests are in the same phase as the
  fast path rather than after it.
- **Platform divergence in the generated C.** Windows and macOS see less
  developer traffic than Linux here. The differential harness must run on all
  three before Phase 2 exits, not only before Phase 8.
- **Build toolchain.** A generated 600 KB C module raises the floor for building
  from source. The ctypes path remains, so a source install without a compiler
  still works, and this needs stating in the install documentation rather than
  being discovered.

## Documentation

The following ship with the phases that create them, not afterwards:

- **Phase 2** — the compatibility contract, the losses inventory, and the
  `PYOPENGL_DISPATCH` setting. The inventory is user documentation, not an
  internal note: a client needs to be able to read the list and decide whether
  any of it applies to them before they switch.
- **Phase 3** — how bindings are resolved per context, what `bool(glFoo)` and
  `glInitXxx()` now mean, and the guarantee that N contexts hold N independent
  sets of entry points. This is a semantic change and needs its own section
  rather than a footnote.
- **Phase 4** — which objects take the array fast path, that a non-matching type
  is converted rather than refused, and how to register a new array type so that
  it is accepted, with the note that acceleration is optional and acceptance is
  not.
- **Phase 5** — the `KHR_debug` mechanism, how to select it, and the runtime
  `ERROR_CHECKING` behaviour.
- **Phase 6** — the virtual-package namespace and what it means for packaging
  and introspection tools.
- **Phase 7** — the stubs and how to use them.
- **Phase 8** — the install-from-source note about the compiler, and the opt-out.

## Prototype

The prototype and both benchmark scripts were built in a session scratchpad and
are not in the repository. Reproducing them needs: the macro set and `GLProc`
type sketched above, a `set_slot(index, address)` entry point to install proc
addresses obtained from `platform.PLATFORM.getExtensionProcedure`, and a slot
pointed at an empty C function of matching signature to separate the
abstraction's cost from the driver's. Landing them under `src/` as the seed of
Phase 0 is the natural next step.

Two defects in the prototype, both load-bearing for the design and both fixed by
decisions above rather than by tinkering:

- **It rejects a non-matching array dtype.** Current PyOpenGL converts. The
  arrays section replaces the check with a fall-through.
- **It leaks a `Py_buffer` when a later argument fails.** The buffer-release
  decision replaces the per-macro release with a frame array and a single
  cleanup path.

Neither affects the measurements: the fall-through costs a comparison already
being made, and the cleanup path costs one counter increment per array argument.

## Cross-references

- `src/xml_generate.py`, `src/codegenerator.py`, `src/xmlreg.py` — the existing
  registry pass this extends.
- `OpenGL/platform/baseplatform.py` — `constructFunction`, `createBaseFunction`,
  `_NullFunctionPointer`; the semantics the slot table has to reproduce.
- `OpenGL/wrapper.py`, `OpenGL/latebind.py`, `OpenGL/lazywrapper.py` — the
  friendly layer being reimplemented; `wrapper.py` survives as a public facility
  for third parties, the other two do not survive at all.
- `OpenGL/GL/exceptional.py`, `images.py`, `pointers.py`, `glget.py` — the Tier 3
  families, and the best statement of what the friendly API actually promises.
- `OpenGL/raw/GL/_glgets.py`, `_lookupint.py` — the 2,215-entry output-size
  table Tier 2 compiles into C.
- `OpenGL/arrays/arraydatatype.py` — the handler registry the fast path falls
  through to.
- `accelerate/src/*.pyx` — where Cython keeps its place.

---

## What landed

Implemented on the `c-dispatch` branch. The design above held; what follows is
what changed under measurement, and where the implementation stands.

### Corrections to the plan, from measurement

- **A binding is `(api, name)`, not `name`.** `glTexImage2D` exists in GL and
  in GLES2 as separate bindings resolved from separate libraries. The plan's
  3,508 unique commands are **4,839 bindings** across GL, GLES1/2/3, GLSC2,
  GLX, WGL and EGL. EGL is in scope after all: its registry is not vendored,
  but the shipped `OpenGL/raw/EGL` tree carries the same facts.
- **Which context is current cannot be known cheaply, and cannot be observed
  at all.** An application makes a context current inside glfw, Qt or SDL,
  which call the window-system library directly; PyOpenGL is not on that path.
  Asking the driver costs **97 ns**, against `glGetError`'s 7 ns, so it cannot
  go on the call path by default. The default re-reads the current context
  whenever an entry point needs resolving and otherwise assumes it has not
  changed — which is **no worse than the ctypes implementation**, which holds
  one binding per process and cannot distinguish contexts at all.
  `PYOPENGL_CONTEXT_TRACKING=verify` pays the 97 ns for exactness (177 ns per
  call against 383 for ctypes), and `make_current` is exact and free for a
  program willing to call it. Requiring the application's toolkit to route
  through PyOpenGL is not an option and is not asked for.
- **The no-context check must stay behind `CONTEXT_CHECKING`.** The plan made
  it always-on because it had become free. Free is not the only question:
  deleting GL objects from a cleanup handler that runs after the context is
  gone is ordinary, and it is a silent no-op today. Turning that into an
  exception breaks working applications at shutdown, which is where they are
  least able to handle it — PyOpenGL's own suite does it, which is how this
  was found. The flag is honoured, off by default as it is today, and when it
  is on every call verifies rather than only the calls that happen to hit an
  unresolved slot.
- **Error checking through `GL_KHR_debug` is worth more than estimated.**
  Checking costs **0.8 ns** rather than the 11 ns of a `glGetError` round
  trip, so leaving it on stops being a trade against speed.
- **The friendly modules are not the only source of truth.** Reading them
  alone marks `glReadPixels` as pass-through, because `images.py` reaches it
  through a differently-named wrapper. The extractor cross-checks the
  registry's `COMPSIZE(format,type,…)` lengths, so the image family is
  identified by what it is.
- **An output must be the trailing argument.** Seven commands
  (`glGetPerfMonitorGroupsAMD` and relatives) have an output in the middle,
  where no arity makes "the caller omitted it" unambiguous. They stay on
  ctypes with that reason recorded.
- **A command is declared by more than one extension, and any of them will
  do.** 223 entry points are declared by two extensions with neither in core —
  `glUniform1i64NV` by both `GL_NV_gpu_shader5` and `GL_AMD_gpu_shader_int64`,
  the EGL sync and image entry points by two KHR extensions each. Recording one
  name and checking only that one refuses a function the context provides: an
  NVIDIA driver advertises `GL_NV_gpu_shader5` and not the AMD extension, so
  `glUniform1i64NV` resolved as absent. Each command now carries every
  extension that declares it, and resolution accepts any one of them. What
  `proc.extension` reports is unchanged, so the attribute surface does not
  move.

- **Virtual packages save nothing while the files are still imported.** Phase
  9's exit asked for import time and resident size to improve. Built, they do
  not: `import OpenGL.GL` takes 58 ms warm and 62 MB either way, and holds the
  same 309 modules, because the friendly modules import the raw ones eagerly
  and a module object is a module object however it was filled. Cold, the same
  import is 185 ms from files against 166 ms from the tables, and a walk of the
  whole raw tree is 333 ms against 352 — one gain, one loss. So the finder
  ships **off by default**, under `PYOPENGL_VIRTUAL_MODULES=1`.

  What it is for is the step after. The definitions now live in the C tables,
  including the `@_p.types(...)` signature each declaration stated, so the
  1,278 files have nothing in them that is not held elsewhere and can be
  removed rather than shadowed — and removing them is what would pay. A test
  compares the two module-for-module, which is what makes that a decision
  rather than a gamble. Two kinds keep their files either way: the packages
  and the private modules (`_types`, `_errors`, `_glgets`) carry classes and
  conditionals, and whatever is imported before the first entry point is built
  is loaded before the finder can exist.

### Measured

Reference machine as above, `OpenGL_accelerate` active, error checking on.

| call | ctypes | C | |
|---|---|---|---|
| `glBindTexture(GL_TEXTURE_2D, 0)` | 407 ns | 58 ns | 7.0× |
| `glUniform1f(loc, 1.0)` | 382 ns | 51 ns | 7.5× |
| `glUniformMatrix4fv(loc,1,False,numpy 4×4)` | 1184 ns | 106 ns | 11.2× |
| `glGetIntegerv(GL_MAX_TEXTURE_SIZE)` | 1280 ns | 513 ns | 2.5× |
| empty Python function | 32 ns | 32 ns | — |

`glGetIntegerv` gains least because allocating the output array dominates what
is left.

**Per frame, which is the number that decides whether any of this matters.**
A frame of 2,000 objects, each doing a bind, three uniforms and a draw — the
shape a tutorial teaches and a great deal of shipped application code still
has:

| | ms/frame | ns/call | GL calls inside a 16.7 ms frame |
|---|---|---|---|
| ctypes | 6.77 | 677 | ~25,000 |
| C | **0.78** | **78** | **~214,000** |

8.7×. Under ctypes that frame spends 40% of a 60 fps budget in Python
dispatch; under C, 4.7%.

**Optimised code sees almost none of this, and that is the expected result.**
A draw-call-bound frame went 5.00 ms to 0.48 ms, but glisteel gains 1.05× and
`crowd_demo` about 1.0×, because both are GPU- and compute-bound and neither
comes near the ceiling. OpenGLContext batches, so it is the *worst* case for
demonstrating the work rather than the best. What moved is the ceiling: the
gain belongs to naive client code, not to ours.

**Import and resident size**, `import OpenGL.GL`, minimum of twelve runs:

| | import | RSS |
|---|---|---|
| before this work | 72.2 ms | 60 MB |
| ctypes | 53.5 ms | 34 MB |
| **C** | **34.2 ms** | **30 MB** |

Three defects account for the difference, none of them a trade:

- `createFunction` ended in `entry_point_for(...) or binding`, and `or` asks
  the left operand whether it is true — which for an entry point means
  "resolvable in the current context". Importing asked the driver which
  context was current **2,286 times** and attempted as many resolutions, at
  the one moment when there is no context and no answer can be right.
- A ctypes binding was built for every entry point and discarded on the line
  that built it. **1,143 per import.** It exists for demotion and for the
  `argtypes`/`restype`/`DLL` attributes, which few callers ever read, so it is
  now built when something asks.
- **The GL driver was loaded at import.** A module-level `if
  _simple.glGetCompressedTexImage:` in `GL_1_3.py` asks whether an entry point
  resolves; answering it asked which context was current; answering *that*
  probed EGL and then GLX, which mapped `libnvidia-gpucomp` (19.5 MB) and
  `libnvidia-glcore` (7.0 MB) before the program had a context. The context
  question is now answered only from an interface already loaded in the
  process, and `None` means "ask again later" rather than "there is none".

### Wheel size

| | before | after |
|---|---|---|
| `pyopengl` | 3.06 MB, `py3-none-any` | 6.39 MB, `cp312-linux_x86_64` |
| `pyopengl_accelerate` | 3.08 MB | 3.08 MB, untouched |

The extension is 2.89 MB of the increase. The larger change is that one
universal wheel becomes one per platform × Python version. **This is why the C
build belongs in `pyopengl_accelerate`** — see next steps.

### Coverage

**4,819 of 4,839 bindings (99.6%).** What remains, with the reason each is
still on ctypes, is what `src/check_registry.py` prints:

| | |
|---|---|
| outputs that are not the trailing arguments | 7 |
| GLX queries returning a pointer to a struct | 11 |
| other converters | 1 |
| hand-written beside the generated ones (`glShaderSource`) | 1 |

The struct-pointer returns hand back an `XVisualInfo *`, a `GLXFBConfig *` or a
`Display *`, which is an X11 type rather than a GL one, and what a caller does
with it is pass it back to Xlib.  Seven outputs sit among the inputs rather
than after them, which the calling convention the stubs are written in does
not express.

### Phases

| phase | state |
|---|---|
| 0 infrastructure | done |
| 1 annotation extraction | done, cross-checked against the registry |
| 2 differential harness | the attribute-surface comparison, the array-acceptance matrix, and both implementations over every suite; not a per-entry-point argument generator |
| 3 Tier 1, arrays, opt-in switch | done |
| 4 Tier 2 declarative annotations | done, including the 1,798-entry `_glgets` table |
| 5 Tier 3 families | done: images, typed arrays, string arrays, retained client pointers and `glShaderSource`, taking coverage to 99.6% |
| 6 per-context dispatch | done, with the multi-context tests as its exit criterion |
| 7 error checking | done, including `GL_KHR_debug` |
| 8 docstrings and `.pyi` | done, and it serves **both** implementations: the stubs are emitted from the command record, cover all commands rather than the C-implemented subset, and `py.typed` ships, so a type checker uses them under `PYOPENGL_DISPATCH=ctypes` with nothing to port |
| 9 virtual packages | built, and off by default: the exit criterion is not met (below) |
| 10 flip the default | done: `PYOPENGL_DISPATCH` defaults to `c`, and `ctypes` remains selectable |
| 11 retire what is dead | unblocked by phase 14: moving the extension into accelerate puts the superseded Cython modules beside it |
| 12 annotations as data | the table is written and checked against the parse on every run; the generator still parses, and stops once signatures come from the registry |
| 13 friendly modules reduced to definitions | next: 987 of 1,289 already are; 259 carry only `setInputArraySize`/`setOutput`, both of which the table already expresses; 43 keep hand-written code |
| 14 the extension moves to `pyopengl_accelerate` | keeps `pyopengl` a universal wheel and makes "is accelerate installed?" the whole dispatch question |
| 15 delete `OpenGL/raw/**` | after 12 and 13, the files hold nothing that is not held elsewhere |
| — EGL from its registry | done: both registries fetched on every generation, 41 commands and 4 types added, 158 covered by tests |
| — test windows hidden | done: `TEST_VISIBLE` defaulted to mapping a window per context, which took over the screen of whoever ran the suite and held each frame 0.2 s; the run is 172 s → 21 s |

The differential work found two divergences no functional test would have
caught, both in attributes a client reads without calling anything:
`glShaderSource.argNames` reported the raw declaration's names rather than the
ones its callers see, and a command promoted into core is declared twice, so
which declaration the ctypes namespace holds depends on import order. The
second is now decided deliberately — the core declaration wins, because it
resolves without an extension check — and the test asserts the property that
matters rather than the string: no entry point that resolves under ctypes
fails to resolve under C.

### The generated modules, and what replaced them

Every module under `OpenGL/raw` was purely generated. Two things now hold the
same facts: the C extension, in `.rodata`, and
`OpenGL/raw/_declarations/<API>.dat`, marshalled per module so that a program
using forty of them does not parse the other twelve hundred. Both are written
by the same generator pass, so they cannot drift.

A friendly module no longer imports a generated one. It says:

```python
from OpenGL._declarations import define as _define
_EXTENSION_NAME = _define(globals(), 'OpenGL.raw.GL.VERSION.GL_1_1')
```

`src/migrate_raw_imports.py` performed that rewrite across 1,289 modules and is
idempotent, so it can be run again as new ones are generated.

**Verified by comparison, not by inspection.** Every public name and every
constant value of all 1,208 importable friendly modules was captured before and
after, under both implementations, and compared. Nothing moved, nothing broke,
and **70 modules that had never imported at all now do** — `GL.NV.draw_vulkan_image`,
`EGL.KHR.debug` and others died on types missing from `_types`, and the type
text is now only evaluated if a ctypes binding is actually wanted.

**It bought no speed, and that is worth recording.** Import went 43.6 ms to
42.8 ms on the C path and 44.5 ms to 53.3 ms on the pure-Python one; the work
the generated module bodies did moved into `define()` rather than disappearing.
Most of the pure-Python regression came back by memoising type-expression
evaluation and making the data file an index of per-module blobs. The
justification for the change is not speed: it is that the declarations become
data with one source, and that 1,287 machine-written Python modules — which
were carrying the 70 dead modules above — stop being the source of truth.

### Next steps

**1. Invert the generator: annotations as data, nothing parsing Python.**

The generator currently reads `OpenGL/raw/**` — which says *"Autogenerated by
xml_generate script, do not edit"* at the top of every file — to recover facts
that were in `gl.xml` one step earlier. That is a redundant hop, and it makes
generated Python the source of truth for a generator. Of 4,839 commands:

| | commands | where the information lives |
|---|---|---|
| plain pass-through | 3,660 | entirely in the registry XML |
| carrying a customisation | 1,179 | hand-authored in the friendly modules |

Only the 1,179 need reading. The plan is one extraction, then never again:

- extract those customisations to a reviewed annotation table, checked in and
  maintained as data;
- capture into it the facts that live only in the shipped tree — EGL, whose
  registry is not vendored, and the recorded drift (7 commands, 3 argument-name
  differences, 158 enums);
- thereafter `registry XML + annotation table -> C, .pyi, .dat, and the
  declaration half of the friendly modules`. Nothing parses Python. A new
  registry release regenerates everything; a new *convention* is an edit to the
  table.

**2. Drive the ctypes wrapping from the same annotations.** The annotations
say what the Python signature is; today the C consumes them and the ctypes path
gets the same information by executing procedural wrapper chains at import.
Both should be generated from the one table, including the type-punned
variants (`glVertex3f` and relatives, `glDrawPixelsub`) that
`OpenGL/GL/pointers.py` and `OpenGL/GL/images.py` build procedurally today.

**3. Reduce the friendly modules to the definitions.** Of the 1,289 that take
definitions:

| | count | |
|---|---|---|
| already just the definitions | 987 | 76.6% |
| mechanical wrapper chains only — annotatable | 259 | 20.1% |
| genuinely hand-written code | 43 | 3.3% |

Absorbing the 259 leaves **1,246 of 1,289 (96.7%)** holding nothing but the
definitions. The 43 that remain are where hand-written code belongs:
`GLUT/freeglut.py` (67 statements), `GL_2_0.py`, `ARB/imaging.py`,
`GL/shaders.py`.

The vocabulary to absorb is narrower than the count suggests. Across the whole
friendly tree:

| call | occurrences | modules |
|---|---|---|
| `setInputArraySize` | 2,027 | 259 |
| `setOutput` | 687 | 122 |
| everything else | ~80 | ~12 |

The two that matter are the two the annotation table already expresses — a
size spec and `out`. So this is not a matter of inventing vocabulary but of
generating the friendly modules *from* the annotations that were extracted
from them. The tail — `setPyConverter`, `setCConverter`,
`setDimensionsAsInts`, `setCResolver`, `StringLengths`, and the 24
`createBaseFunction` calls that all live in one module — stays hand-written,
alongside the 43.

**4. Correct EGL — done.** `src/fetch_registries.py` fetches both Khronos
repositories (EGL is published separately), `src/regenerate_c.py` runs it
first, and `src/generate_egl.py` binds what the registry declares and the tree
lacks. Bindings 4,839 → 4,880. Four types were named by declarations and
defined by nothing — `EGLDEBUGPROCKHR`, `EGLLabelKHR`, `EGLObjectKHR`,
`EGLClientPixmapHI` — so the three `EGL_KHR_debug` entry points could not be
built at all; and the registry's `EGL_CAST(EGLnsecsANDROID,-1)` values, which
the older generator emitted commented out, are emitted as values.
`tests/test_egl_bindings.py` covers all 158 commands.

**5. Move the C build into `pyopengl_accelerate`.** It is the optional
compiled companion, released from this repository alongside `pyopengl`, and
"is accelerate installed?" is already the question that selects the existing
accelerators. Consequences: `pyopengl` stays `py3-none-any` with the `.dat`
tables in it, `accelerate` carries the extension, PyPy simply does not install
accelerate, and there is no wheel matrix on the core package. The two are built
and released together from one checkout, so requiring exactly equal versions is
acceptable and should be enforced. The Cython `wrapper`, `latebind`,
`errorchecker` and `arraydatatype` in accelerate are largely superseded by the
C dispatch, so this also puts them where they can be retired together
(Phase 11).

**6. Then delete `OpenGL/raw/**`.** Once the declarations are generated from
the table and the friendly modules take them from `define()`, the 1,287
generated files hold nothing that is not held elsewhere. Removing them takes
0.70 MB off the wheel. `PYOPENGL_VIRTUAL_MODULES` becomes the compatibility
path for third-party `from OpenGL.raw.X import *` and should then default on,
since it would be the only thing making those names resolve.

### Beyond the phases

`.github/workflows/registry-update.yml` pulls the registry weekly,
regenerates, fails only on drift the baseline does not record, and opens a
pull request whose body is the report. `tox.ini` gains a dispatch axis, so
both implementations are tested rather than one.

`src/check_registry.py` compares the shipped bindings against the registry.
It found the shipped tree already lags: **7 registry commands with no binding,
3 argument-name differences and 158 enums with no constant**, none of them
caused by this work. They are recorded in `registry_baseline.json` with a
reason, so the tool reports only what is new since.
