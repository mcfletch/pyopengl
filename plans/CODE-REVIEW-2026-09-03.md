# Code review — PyOpenGL, 474c1a8..805f0917 (2026-09-03)

**Scope.** The 68 commits from `474c1a8` to `805f0917` (2026-08-31 → 2026-09-03):
the C dispatch layer moving into `pyopengl_accelerate`, the annotation table and
the generation rebuild (phases 12–15), the virtual `OpenGL.raw` modules, the
review series 4.5–14.9, and the four behaviour changes that followed —
`compileProgram` validation, glBegin-block recovery, `forget_context` safety, and
`OpenGL.EGL.devices`. Hand-written material only: `accelerate/src/c/`,
`OpenGL/_dispatch/`, `OpenGL/_declarations.py`, `OpenGL/GL/shaders.py`,
`OpenGL/EGL/devices.py`, `src/cdispatch/`. The 2,800 generated files are read
only where a finding needs the emitted form as evidence.

**Status: all 17 findings fixed**, each Red/Green with the failing test written
first. The suite is 1,832 passed / 419 skipped / 1,092 subtests, up from 1,768,
with no core dumps.

**One thing left open, and it is not a finding above.** The pass/skip split of a
full run varies by up to three tests, all in `tests/gles`: an ES context created
after a GLX one in the same process sometimes reports fewer extensions, and
`require_extension` then skips. `test_disjoint_timer_query` is the one that moves
most. Run on its own the extension is always there, so it is about which driver
the ES backend lands on rather than about any of this code — and the same
variation shows on `805f0917` with the Python from before this review, so it
predates it. One run in about fifty also produced a single failure that was not
captured and has not recurred in fifty-three consecutive runs since. Both are
worth a session of their own, against `tests/glcontext_egl.py`, which picks its
device with the third hand-rolled copy of the enumeration that
`OpenGL.EGL.devices` now exists to replace.

**Overall.** This is a large, careful rewrite of the hottest path in the library,
and the design decisions are sound and unusually well argued in the source. The
per-context table, the retire-rather-than-free rule for a forgotten context, the
"the fast path may accelerate, never reject" rule for arrays, and the thread-local
glBegin suspension are all right, and each carries the reasoning that makes it
reviewable. `tests/cdispatch` and `tests/gl` were green before this review too:
622 passed, 293 skipped, 817 subtests — which is the point of B1 below.

One finding is a blocker. The output-array bounds guard added to
`pygl_array_out` — the check whose own comment says it exists to stop
"256 bytes into 4, which corrupts the heap" — measures the wrong buffer on two of
its three input paths and reads uninitialised stack memory on the third. Both
failures let the driver do exactly what the guard was written to prevent. It
reproduces in four lines and ends in `Fatal Python error: Aborted`, which
[../CLAUDE.md](../CLAUDE.md) makes a stop-and-fix condition.

The rest cluster in two places. **Guards that do not guard**: the
accelerate/PyOpenGL version check is inert because the attribute it reads is
never set, and `_read_table` promises a diagnostic ImportError for a damaged
table but does not catch what a damaged table actually raises. And **the API
argument added to stop cross-API confusion is not passed on the two paths that
still need it** — `demote_and_call` and `record_custom` both key on the bare
name, which is the mistake `ctypes_callable`'s own docstring exists to describe.

Everything below has a reproduction or a citation.

---

## Summary of findings

| ID | State | Severity | Area | Finding |
|----|-------|----------|------|---------|
| [B1](#b1) | ✅ Fixed | **Blocker** | `accelerate/src/c/pygl_runtime.c` | The output-array bounds guard checks the caller's object rather than the buffer the driver is handed, and reads `view.len` uninitialised; heap corruption and `Fatal Python error: Aborted` |
| [M1](#m1) | ✅ Fixed | Major | `OpenGL/_dispatch/__init__.py` | `_versions_match()` can never fail: `__pyopengl_version__` is not defined by the extension |
| [M2](#m2) | ✅ Fixed | Major | `OpenGL/_dispatch/__init__.py`, `support.py` | `use_debug_output()` overrides `ERROR_CHECKING=False`, and the `GLError` it raises carries a driver message id in `err` rather than a GL error code |
| [M3](#m3) | ✅ Fixed | Major | `OpenGL/_dispatch/support.py` | `demote_and_call` and `record_custom` drop the API, reintroducing the cross-API mix-up `ctypes_callable(api=…)` was added to fix |
| [M4](#m4) | ✅ Fixed | Major | `accelerate/src/c/pygl_runtime.c` | `pygl_check_error`'s GL_KHR_debug branch can return `-1` with no exception set |
| [m1](#m1-minor) | ✅ Fixed | minor | `OpenGL/_declarations.py` | `_read_table` promises a diagnostic ImportError for a damaged table and does not catch what `marshal` raises for one |
| [m2](#m2-minor) | ✅ Fixed | minor | `_declarations.py` / `_dispatch/finder.py` | Two near-identical `Declaration` classes with opposite safety postures; one uses `eval()`, the other explains why it must not |
| [m3](#m3-minor) | ✅ Fixed | minor | `OpenGL/_dispatch/finder.py` | Module docstring says virtual modules are off by default; they are on, in two places |
| [m4](#m4-minor) | ✅ Fixed | minor | `OpenGL/GL/shaders.py` | `_sampler_types()` rescans `vars(OpenGL.GL)` on every link; `validate=True` silently validates nothing for a multi-sampler program |
| [m5](#m5-minor) | ✅ Fixed | minor | `accelerate/src/c/pygl_runtime.c` | `pygl_debug_callback` can report a stale message; `pygl_argument_error` clobbers a pending exception |
| [m6](#m6-minor) | ✅ Fixed | minor | `OpenGL/_dispatch/__init__.py` | `_installed_callbacks` grows without bound; `use_debug_output(False)` leaves the driver callback installed |
| [m7](#m7-minor) | ✅ Fixed | minor | `accelerate/src/c/pygl_runtime.c` | Retired tables are 43 KB each, not "about 23 KB", and `generation` is written and never read |
| [m8](#m8-minor) | ✅ Fixed | minor | `tests/gl/test_review_fixes.py` | The bounds-check test covers only the path that works |
| [m9](#m9-minor) | ✅ Fixed | minor | `OpenGL/_dispatch/support.py` | `signature_for` compiles and `exec`s generated source to build a `Signature` |
| [m10](#m10-minor) | ✅ Fixed | minor | `OpenGL/EGL/devices.py` | New public module with no entry in `documentation/` |
| [m11](#m11-minor) | ✅ Fixed | minor | `src/fetch_registries.py` | Generated bindings are built from an unpinned, unverified upstream fetch |
| [m12](#m12-minor) | ✅ Fixed | minor | `OpenGL/_dispatch/__init__.py` | `make_current`/`forget_context` act on `AVAILABLE` rather than `ACTIVE` |

---

<a name="b1"></a>
## B1 — Blocker — the output-array bounds guard does not guard

`accelerate/src/c/pygl_runtime.c:913-925`

```c
if (exact && count > 0 && element->itemsize > 0 && out->owner == object) {
    Py_ssize_t needed = count * (Py_ssize_t)element->itemsize;
    if (out->view.len < needed) {
```

The guard's own comment states its purpose:

> Without this the driver writes count elements into whatever the caller
> supplied: `glGenTextures(64, a)` with a four-byte array is 256 bytes into 4,
> which corrupts the heap and is only noticed much later.

Two independent defects stop it doing that.

**(a) It measures the caller's object, not the buffer the driver is handed.**
`out->owner == object` is true only when `pygl_array_acquire` took the
buffer-protocol fast path or the ctypes-pointer branch. Whenever
`pygl_array_convert` produced a *copy* — a non-contiguous array, a list, an array
of a convertible type — `out->owner` is the copy and the whole `if` is skipped.
The driver then writes `count` elements into a buffer that
`ArrayDatatype.asArray` sized from the caller's length, and nothing checks it.

**(b) `out->view` is uninitialised whenever `have_view` is 0.**
`PYGL_FRAME(n)` (`pygl.h:475`) declares `PyGLBuf _bufs[(n)]` on the stack with no
initialiser. `pygl_array_acquire` (`pygl_runtime.c:718-768`) sets `owner`,
`have_view`, `block` and `pointer` — never `view`. So on the ctypes-pointer
branch, where `owner == object` and `have_view == 0`, `out->view.len` is whatever
the previous stack frame left there. `pygl_array_in_sized` gets this right
(`if (out->have_view)` at line 801); `pygl_array_out` does not.

### Reproduction

`exact` is set only where the count comes from an argument
(`src/cdispatch/emit_c.py:403`), which is the `glGen*`/`glDelete*`/`glGetv`
family. Against the tree as it stands, with a hidden GLFW window current:

```python
import numpy as np, OpenGL.GL as GL
base = np.zeros((8,), 'I'); strided = base[::2]    # 4 elements, non-contiguous
for i in range(200):
    GL.glGenTextures(1024, strided)                # 4096 bytes into a 16-byte copy
```

```
corrupted double-linked list
Fatal Python error: Aborted
Extension modules: …, OpenGL_accelerate.dispatch, …
Aborted (core dumped)
```

No diagnostic is raised for any of the 200 calls; the process dies in glibc's
allocator. Path (b), separately:

```python
buf = (ctypes.c_uint * 1)()                        # room for exactly one name
p   = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint))
for i in range(8):
    GL.glGenTextures(2, p)                         # asks for two
```

```
same call, eight times -> {'0 bytes': 1, 'accepted': 7}
```

The *same call* reports `output array holds 0 bytes` once and is accepted seven
times, across three separate runs with identical counts. That is the
uninitialised read: the first frame happened to find a zero, later ones find
something ≥ 8.

### Fix

Measure the buffer the driver will actually be given, whatever produced it, and
treat "cannot be measured" as "cannot be checked" rather than as zero:

```c
if (exact && count > 0 && element->itemsize > 0) {
    Py_ssize_t needed = count * (Py_ssize_t)element->itemsize;
    Py_ssize_t have = -1;                  /* -1: nothing here can say */
    if (out->have_view) {
        have = out->view.len;
    } else if (out->owner != NULL && !pygl_is_ctypes_pointer(out->owner)) {
        have = pygl_byte_count(element, out->owner);   /* arrayByteCount, -1 on failure */
    }
    if (have >= 0 && have < needed) {
        PyErr_Format(PyExc_ValueError, …);
        pygl_release(out);
        return -1;
    }
}
```

`pygl_array_in_sized:804-815` already performs the `arrayByteCount` call this
needs; lifting it into a `pygl_byte_count` helper removes the duplication at the
same time. A raw ctypes pointer genuinely carries no length, so it stays
unchecked — but unchecked deliberately, not by reading a stack slot.

Independently, close the uninitialised read at its source: every acquire helper
(`pygl_array_acquire`, `pygl_array_out`, `pygl_array_typed`, `pygl_string_array`,
`pygl_image`) already writes the same four fields on entry, so add
`out->view.len = 0; out->view.buf = NULL;` to that group. Two stores, off the
matched-buffer fast path, and no later reader can find garbage.

### Tests to add

`tests/gl/test_review_fixes.py::TestOutputArraySafety` covers exactly one input
shape — see [m8](#m8-minor). The three that matter are:

```python
GL.glGenTextures(64, numpy.zeros(8, 'uint32')[::2])   # converted copy
GL.glGenTextures(2,  ctypes.cast((ctypes.c_uint * 1)(),
                                 ctypes.POINTER(ctypes.c_uint)))   # raw pointer
GL.glGenTextures(64, [0] * 4)                          # list, converted
```

The first two must raise `ValueError`; the third must raise or be accepted
consistently, never one and then the other.

### Remediation — ✅ Fixed

**Red.** `TestOutputArraySafety::test_an_undersized_array_is_refused_rather_than_overrun`
became a `parametrize` over `_undersized_arrays()`, one case per shape the
acquire path branches on — matched buffer, non-contiguous copy, wrong-type copy,
list — plus
`test_a_raw_pointer_is_measured_or_left_alone_but_never_guessed`, which makes
the *same* call eight times and asserts one answer. The `matched-buffer` case
passed; `converted-copy` took the process down while pytest was formatting the
failure:

```
.Fatal Python error: Segmentation fault
Current thread … (most recent call first):
  Garbage-collecting
```

**Green.** Three changes in `accelerate/src/c/pygl_runtime.c`:

- `pygl_buf_reset()` is the one place a frame slot is initialised, and it now
  writes `view.buf` and `view.len` as well as the four fields the seven
  open-coded copies wrote. The comment says why a field that is only *valid*
  under `have_view` still has to be *written*.
- `pygl_byte_count(element, buffer)` answers how much storage the acquired
  argument holds, or `-1` where nothing can say — a raw pointer, a ctypes
  scalar, an object `arrayByteCount` refuses. It measures `buffer`, so a
  conversion's copy is what gets measured.
- The `exact` guard drops `out->owner == object` and reads
  `pygl_byte_count(element, out)`, refusing only on `have >= 0 && have < needed`
  so that "cannot say" stays distinct from "zero".

`pygl_array_in_sized` had its own inline copy of the `arrayByteCount` call and
now uses the helper, which is what stops the two paths disagreeing again.

**Green, verified.** `tests/gl/test_review_fixes.py` 26 passed; the whole
PyOpenGL suite 1,768 passed / 419 skipped / 1,092 subtests, no core dumps. The
original reproduction now says what it should:

```
ValueError: glGenTextures: output array holds 16 bytes, but the call writes
4096 (1024 items of 4 bytes). Pass a larger array, or None to have one allocated.
```

and the raw-pointer call answers `{'accepted': 8}` — one answer, eight times.

---

<a name="m1"></a>
## M1 — Major — the version guard can never fail

`OpenGL/_dispatch/__init__.py:69-82`

```python
theirs = getattr(_c, '__pyopengl_version__', None)
return theirs is None or theirs == ours
```

The docstring is explicit about the stakes:

> They share the generated slot numbering and table layout, so a mismatched pair
> does not fail cleanly — it dispatches through the wrong indices.

Nothing defines `__pyopengl_version__`. It appears twice in the whole tree, both
times in this file reading it; `pygl_exec` adds `GLProc` and `entry_points` to
the module and nothing else. At run time:

```python
>>> from OpenGL._dispatch import _c
>>> [n for n in dir(_c) if 'version' in n.lower()]
[]
```

So `theirs is None` is always true and the guard always passes. The one case it
was written for — an older `pyopengl_accelerate` left behind by a partial
upgrade — is precisely the case that would not carry the attribute, so it is
waved through into dispatch on the wrong slot indices.

**Fix.** Define it in `pygl_exec`, from the same version the wheel is built with:

```c
if (PyModule_AddStringConstant(module, "__pyopengl_version__",
                               PYOPENGL_VERSION) < 0) {
    return -1;
}
```

with `PYOPENGL_VERSION` supplied as a `-D` from `accelerate/setup.py`, then make
the absence of the attribute a mismatch rather than a pass:

```python
theirs = getattr(_c, '__pyopengl_version__', None)
return theirs == ours
```

A test that asserts `_c.__pyopengl_version__ == OpenGL.version.__version__` is
what stops this going inert again.


### Remediation — ✅ Fixed

**Red.** `tests/test_dispatch_selection.py::TestVersionPairing` — three cases:
the extension states a version, an extension that will not say is a mismatch,
and a different version is a mismatch. Two failed
(`AssertionError: assert not True`, and no such attribute).

**Green.** `accelerate/setup.py` reads its own `__version__` out of the source
(importing the package during its own build would need the extensions that are
not built yet) and passes it as `-DPYOPENGL_VERSION`; `pygl_exec` adds it with
`PyModule_AddStringConstant`. `_versions_match` now requires equality, so an
extension that does not say which tables it holds is a mismatch — which is the
case the guard exists for, since an accelerate old enough to be dangerous is
the one that would not carry the attribute.

Verified at run time: `accelerate says 4.0.0a4 | pyopengl says 4.0.0a4`.

---

<a name="m2"></a>
## M2 — Major — `use_debug_output()` reverses a caller's settings, and mislabels the error

`OpenGL/_dispatch/__init__.py:333-374`, `support.py:386-398`, `pygl.h:330-336`

The docstring says:

> What a caller sees does not change: the same exception, raised from the same
> call.

Both halves of that are untrue.

**Error checking is forced on.** `pygl_check_needed` in debug mode returns
`pygl_debug_pending` and never consults the per-slot `PYGL_F_CHECK_ERRORS` flag,
so `OpenGL.ERROR_CHECKING = False` and `set_error_checking(False, glFoo)` both
stop having any effect the moment debug output is enabled:

```python
import OpenGL; OpenGL.ERROR_CHECKING = False
…
glEnable(0xDEAD)                       #   silent, as documented
_dispatch.use_debug_output()           # -> True
glEnable(0xDEAD)                       #   now raises: GLError
```

**The exception carries the wrong number.** `raise_debug_error` puts the driver's
debug *message id* into `GLError.err`, which every consumer reads as a GL error
constant:

```python
err.err == 2          # GL_INVALID_ENUM is 0x500
```

`OpenGL.error.GLError` documents `err` as the GL error code and formats it as
one, so a program that branches on `err.err` — or simply prints the exception —
gets a meaningless value that varies by driver.

**Fix.** Two independent changes:

1. In `pygl_check_needed`, gate the debug branch on the same flag as the
   glGetError branch:
   ```c
   if (!(pygl_current->flags[self->info->slot] & PYGL_F_CHECK_ERRORS)) {
       return 0;
   }
   return pygl_error_mode == PYGL_ERRORS_DEBUG ? pygl_debug_pending
        : 1;
   ```
   With that, debug output becomes what the docstring claims — a cheaper way to
   notice the errors the caller already asked to be told about.
2. Record the GL error code in the callback. `glDebugMessageCallback` does not
   supply one, so either call `glGetError` once from `pygl_check_error`'s debug
   branch before raising (it is off the hot path — an error has already been
   reported), or map `GL_DEBUG_TYPE_ERROR` sources to codes in
   `raise_debug_error` and pass the message id in a separate attribute. Either
   way `err.err` must mean what `GLError` says it means.


### Remediation — ✅ Fixed

**Red.** `tests/gl/test_debug_output_parity.py`, four subprocess cases —
`ERROR_CHECKING = False`, a per-entry-point `set_error_checking(False, …)`,
checking left on, and the error code. Three failed, the last with
`assert 'raised 0x2' == 'raised 0x500'`.

**Green.**

- `pygl_check_needed` (`pygl.h`) reads the per-slot `PYGL_F_CHECK_ERRORS` flag
  first and consults `pygl_debug_pending` only after it. Debug output is now a
  cheaper way to notice the errors the caller already asked about, which is
  what the docstring claimed.
- `pygl_error_code()` factors out the glGetError slot resolution both branches
  need, and the debug branch calls it: GL_KHR_debug says *that* an error
  happened and what the driver called it in prose, and the code still comes
  from glGetError.
- `raise_debug_error(code, identifier, message, name, arguments)` puts the GL
  error code in `err` where `GLError` documents it, the driver's text in
  `description`, and the driver's message identifier on `debugMessageID` for
  anyone who wants it.

---

<a name="m3"></a>
## M3 — Major — the API argument is dropped on the two paths that still need it

`OpenGL/_dispatch/support.py:243-264, 286-318`

`ctypes_callable`'s docstring states the problem the `api` argument solves:

> `glClear` exists in GL and in GLES2 as separate bindings resolved from separate
> libraries, so scanning for the first name that matches can hand back the
> desktop GL function for a GLES2 entry point — and on a system serving both,
> demoting then binds the wrong library.

`demote_and_call` then calls it without one:

```python
binding = ctypes_callable(proc.__name__)     # support.py:314
```

`proc` is a `GLProc` and carries its API in `info->api`, but nothing exposes it
to Python, so the scan falls back to `_API_NAMES` order — `GL` first. Demoting a
GLES2 entry point on a system serving both therefore binds the desktop GL
function, which is the exact failure the parameter exists to prevent.

`record_custom` and `_swallowed` have the same shape: keyed on
`proc.__name__` alone, so a customisation swallowed for `GL.glClear` is replayed
onto `GLES2.glClear`'s wrapper when that one demotes.

**Fix.** Expose the API on `GLProc` — a one-line getset beside `deprecated`:

```c
static PyObject *GLProc_get_api(GLProc *self, void *closure)
{
    return PyUnicode_FromString(pygl_api_name(self->info->api));
}
```

then key both on `(proc.api, proc.__name__)`:

```python
binding = ctypes_callable(proc.__name__, getattr(proc, 'api', None))
remembered = _swallowed.setdefault((proc.api, proc.__name__), {})
```

A test that demotes `OpenGL.GLES2.glClear` and asserts `binding.DLL is
platform.PLATFORM.GLES2` covers it.


### Remediation — ✅ Fixed

**Red.** `tests/test_attribute_surface_api.py` — five cases over the two
`glClear`s. Four failed, including `module 'OpenGL._dispatch.support' has no
attribute 'swallowed_for'`.

**Green.** `GLProc.api` is a new read-only getset answering
`pygl_api_name(self->info->api)`. `demote_and_call` passes it to
`ctypes_callable`, and `_swallowed` is keyed on `(api, name)` through a
`_key_for(proc)` helper — which falls back to `None` for a plain ctypes binding
reached through the same chain, rather than inventing an answer. `swallowed_for`
is the public reader, so the key is stated in one place.

---

<a name="m4"></a>
## M4 — Major — the debug branch can return `-1` with nothing raised

`accelerate/src/c/pygl_runtime.c:513-525`

```c
result = PyObject_CallMethod(pygl_support, "raise_debug_error", "IssO", …);
Py_XDECREF(tuple);
Py_XDECREF(result);
return -1;
```

The glGetError branch forty lines below guards this case, and says why:

```c
if (!PyErr_Occurred()) {
    /* raise_gl_error is supposed to raise.  Returning -1 with nothing set
     * would surface much later as a SystemError about a function that
     * "returned a result with an exception set" -- or worse, be missed. */
```

The debug branch has no such guard, so any client that replaces
`support.raise_debug_error` — or any future edit that lets it return normally —
produces a stub returning `NULL` with no exception, which CPython reports as a
`SystemError` from an unrelated frame.

**Fix.** Lift the check into a small helper both branches call, so the two paths
cannot drift again:

```c
static void pygl_ensure_raised(GLProc *self, unsigned int code)
{
    if (!PyErr_Occurred()) {
        PyErr_Format(pygl_null_function_error,
                     "%s failed with GL error 0x%X", self->info->name, code);
    }
}
```


### Remediation — ✅ Fixed

**Red.** `test_a_raiser_that_declines_does_not_become_a_SystemError`,
parametrised over both notice mechanisms: a client replaces the raiser with one
that returns. The glGetError case passed, and with the guard removed to confirm
the test bites, the debug case gave

```
SystemError <OpenGL entry point glEnable> returned NULL without setting an exception
```

**Green.** `pygl_ensure_raised(self, code)` holds the check both branches need
and both call it, so the two cannot drift again. The guard was removed and
restored to verify red, and the tree is back as it was.

---

<a name="m1-minor"></a>
## m1 — `_read_table` does not catch what a damaged table raises

`OpenGL/_declarations.py:52-71`

```python
try:
    blob = _table(name).read_bytes()
except (OSError, KeyError) as error:
    raise ImportError('PyOpenGL cannot read its declaration table %r …')
return marshal.loads(blob)
```

The docstring promises that a failure to read a table is fatal *with an
explanation*, because the alternative is a missing module several frames from the
missing file. But the `marshal.loads` is outside the `try`, and a truncated or
corrupt `.dat` — a partial wheel extraction, a bad mirror, a filesystem error —
raises `ValueError: bad marshal data` or `EOFError` from inside an import of
`OpenGL.GL`, which is exactly the unexplained failure the function was written to
avoid. These tables are now the only description of `OpenGL.raw` there is, so a
damaged one is a total failure of the installation and deserves the sentence.

CPython also documents `marshal` as *not* safe against malformed input: for some
inputs it does not raise at all. That is a second reason to hold the bytes at
arm's length rather than a reason to change format — `marshal` is the right
choice for the speed, and these files are package data.

**Fix.** Bring the load inside the guard:

```python
try:
    blob = _table(name).read_bytes()
    return marshal.loads(blob)
except (OSError, KeyError, EOFError, ValueError, TypeError) as error:
    raise ImportError(…) from error
```

Consider adding a length-and-digest header written by `modules.py:386` and
checked here, so a damaged table is reported as damaged rather than left to
`marshal` to notice or not.


### Remediation — ✅ Fixed

**Red.** `tests/test_packaged_loaders.py::TestADamagedTableSaysSo`, three
damaged tables — empty, truncated, wrong format. All three gave
`ValueError: bad marshal data (unknown type code)` from inside the import.

**Green.** The `marshal.loads` moved inside the `try` and the caught set became
`(OSError, KeyError, EOFError, ValueError, TypeError)`; the message now says
"dropped or damaged them". `contents_for`'s per-module `marshal.loads` got the
same treatment, naming the module it could not read.

`clear_caches()` also clears `_annotations`, which it was missing — the tests
that compare the two sources were keeping a stale annotation table across the
switch.

---

<a name="m2-minor"></a>
## m2 — two `Declaration` classes, with opposite answers to the same question

`OpenGL/_declarations.py:477-547` and `OpenGL/_dispatch/finder.py:194-298`

Both classes hold `(api, name, extension, module, arguments, types)`, both resolve
the type text against `{ctypes, arrays, _cs}`, and both end in the same
`platform.nullFunction(...)` call with the same eight keyword arguments. They are
one class written twice, and they will drift.

They already differ on the point that matters. `finder._resolve_type` walks the
expression as an AST and says why:

> They are still read rather than executed: the text arrives from a data file,
> and a data file that can run code is a different kind of file.

`_declarations.Declaration._resolve_types` calls `eval(text, namespace)` on the
same text from the same tables. So the ctypes route — the one an installation
without the compiled extension takes — bypasses the protection the C route
documents.

**Fix.** Keep one class. `_declarations.Declaration` is the one with the type
cache, so move `finder._resolve_type`/`_evaluate` beside it, have
`_resolve_types` use them, and delete `finder._Declaration` and `_as_sequence`
in favour of an import.

While doing it, tighten `_evaluate`: it currently permits any `ast.Call` on any
attribute reachable from `ctypes`, which includes `ctypes.CDLL` and
`ctypes.memmove`. The vocabulary a declaration is actually written in is
`ctypes.POINTER`, `ctypes.CFUNCTYPE` and the `arrays.*` names, so an allowlist
checked at the call node makes the comment's claim true:

```python
_CALLABLE = {(ctypes, 'POINTER'), (ctypes, 'CFUNCTYPE')}
```

`clear_caches()` should also clear `_annotations`, which it currently misses —
the tests that compare the two sources keep a stale annotation table across the
switch.


### Remediation — ✅ Fixed

**Red.** `tests/test_declaration_types.py`, 18 cases: the vocabulary, what is
refused, that both routes share one reader, and that a declaration builds its
binding. All 18 failed.

**Green.** `OpenGL._declarations` now owns `resolve_type`, `_evaluate`,
`as_sequence` and the one `Declaration` class; `finder` imports and re-exports
them, and `finder._Declaration`, `finder._as_sequence`, `finder._resolve_type`
and `finder._evaluate` are gone. The ctypes route no longer calls `eval()`.

The evaluator is tighter than either was: a call must be an attribute access
naming one of `_TYPE_CONSTRUCTORS` (`POINTER`, `CFUNCTYPE`, `WINFUNCTYPE`), so
`ctypes.CDLL("libc.so.6")` is refused by name; and a dunder is refused.

**What the sweep caught.** The first form of the dunder guard was
`node.attr.startswith('__')`, and sweeping all 23,426 type expressions in the
shipped tree found the one it broke: GLX declares `__GLXextFuncPtr`, an ordinary
type of ours. The guard is now "starts *and* ends with `__`", and
`TestEveryExpressionTheGeneratorWrote` runs that sweep so a future tightening
cannot refuse a real declaration silently — a refusal that would otherwise
surface only when something demoted that one entry point.

---

<a name="m3-minor"></a>
## m3 — the finder docstring states the wrong default

`OpenGL/_dispatch/finder.py:15`

> ``PYOPENGL_VIRTUAL_MODULES=1`` uses it.  It is off by default, and the
> measurement is why:

It is on by default, in both places that read the variable:

- `finder.py:315` — `os.environ.get('PYOPENGL_VIRTUAL_MODULES', '1')`
- `OpenGL/_configflags.py:50` — the same default

and `documentation/c-dispatch.html:407` documents `PYOPENGL_VIRTUAL_MODULES=0` as
the way to turn it *off*, which agrees with the code and not with the docstring.
Since the paragraph then spends nine lines justifying a default the module does
not have, a reader is left with a wrong model of what their process is doing.

**Fix.** Restate the paragraph for the default that is there: the finder is on,
`PYOPENGL_VIRTUAL_MODULES=0` goes back to the files, and the measurements
explain why the *files* are still shipped rather than why the finder is off.

Second, smaller point: `_virtual_modules_wanted()` is a private re-parse of a
flag `_configflags.VIRTUAL_MODULES` already parses, and the comment explains that
importing `_configflags` here would freeze the other flags too early. That
reasoning is right, but two parses of one variable can disagree after an edit.
Move the parse into a module of its own — or into `finder` — and have
`_configflags` import *it*, so there is one expression.


### Remediation — ✅ Fixed

**Red.** `tests/test_virtual_modules.py::TestTheFlagIsParsedInOneplace` — the
two readings agree, `_configflags` does not parse the variable itself, and eight
settings mean what they should. Ten of the eleven failed.

**Green.** The parse moved to `OpenGL._rawfinder.virtual_modules_wanted()` —
the module that already owns this subject and imports nothing from PyOpenGL, so
`_configflags` can read it without the cycle that ruled out the obvious home.
`finder.virtual_modules_wanted` is an alias to it and `_configflags.VIRTUAL_MODULES`
calls it. An empty value now means unset, because that is what an unexported
shell variable expands to.

The module docstring says what the default is: on, because there are no files to
be off in favour of. The measurements stayed, reframed as the reason the *files*
were removed rather than shadowed, which is what they actually argue.

---

<a name="m4-minor"></a>
## m4 — `compileProgram`'s sampler scan is expensive, and silently validates nothing

`OpenGL/GL/shaders.py:89-131, 144-160, 268-274`

Three points, in descending order of consequence.

**`validate=True` no longer means validation.** `check_validate(when_meaningful=True)`
returns early for any program declaring two sampler targets — which the commit
message correctly notes is "any lit shader with shadow maps", i.e. most real
programs. The caller asked for validation and gets none, with nothing said. The
skip is well argued for the sampler-aliasing case, but it discards every *other*
answer `glValidateProgram` gives about that program.

*Fix:* log the skip at `info` so it appears in a session that is being debugged,
and record it on the object (`program.validation_deferred = True`) so a caller
can ask.

**`_sampler_types()` rebuilds its set on every call**, scanning `vars(GL)` — the
full re-exported `OpenGL.GL` namespace — for every `compileProgram` in the
process. It depends on nothing but the module, so it is a module-level constant
built once:

```python
_SAMPLER_TYPES = None

def _sampler_types():
    global _SAMPLER_TYPES
    if _SAMPLER_TYPES is None:
        _SAMPLER_TYPES = frozenset(…)
    return _SAMPLER_TYPES
```

`_distinct_sampler_targets` should also stop at two, since that is all the caller
asks:

```python
if len(targets) > 1:
    return len(targets)
```

which turns a full `glGetActiveUniform` sweep of every uniform into, typically,
two or three queries.

**The membership test is looser than the name suggests.** `'SAMPLER' in
name.split('_')` matches `GL_SAMPLER_BINDING` and `GL_SAMPLER`, which are a pname
and an object-type token rather than uniform types. Nothing collides today, so
this is a correctness hazard rather than a bug; restricting to the values
`glGetActiveUniform` can return — or simply excluding the known non-types — makes
the set mean what its docstring says.


### Remediation — ✅ Fixed

**Red.** `tests/gl/test_compile_program_validation.py` gained four cases — the
skip is recorded, an explicit check clears it, the sampler set is built once,
and it holds no enum that is not a uniform type. All four failed.

**Green.**

- `ShaderProgram.validation_deferred` records a skip and `check_validate` logs
  it at `info`, naming the program and saying what to do. A caller who asked for
  validation and did not get it can now find that out.
- `_sampler_types()` builds its frozenset on the first ask and keeps it, and
  excludes `GL_SAMPLER`, `GL_SAMPLER_BINDING` and `GL_MAX_SAMPLES` — a pname, an
  object-type token and a limit, none of which is ever a `glGetActiveUniform`
  answer.
- `_distinct_sampler_targets` stops at two, because two is the whole of what the
  caller asks. A link no longer costs a `glGetActiveUniform` round trip per
  uniform.

---

<a name="m5-minor"></a>
## m5 — two small C hygiene defects

**A stale debug message.** `pygl_runtime.c:452-480`. When the driver passes
`message == NULL` with `length > 0` — permitted by GL_KHR_debug, and what a
driver reporting a message it could not format does — `limit` keeps the
non-zero length, the `memcpy` is skipped, and `pygl_debug_message[limit] = '\0'`
terminates *after* bytes left by the previous callback. The exception then
carries the previous error's text.

*Fix:* `if (message == NULL) { limit = 0; }` before the truncation.

**A clobbered exception.** `pygl_runtime.c:416-442`. If `PyObject_Str(value)`
fails — a `__str__` that raises, or a MemoryError — the code calls
`PyErr_Restore(type, value, traceback)` while the `PyObject_Str` failure is still
pending. `PyErr_Restore` overwrites rather than chains, so the second exception
is discarded silently.

*Fix:* `PyErr_Clear()` immediately before the `PyErr_Restore`, so the discard is
deliberate and visible.


### Remediation — ✅ Fixed

`pygl_debug_callback` sets `limit` to zero when `message` is NULL, so a driver
reporting a length with no text cannot leave the previous callback's bytes in
front of the terminator.

`pygl_argument_error` calls `PyErr_Clear()` before `PyErr_Restore`, so
discarding whatever `__str__` raised is a decision rather than an overwrite.

Both are covered by the existing `TestABadScalarRaisesWhatCtypesRaises` and
`tests/gl/test_debug_error_checking.py`; neither is separately reachable from
Python without a driver that behaves that way, and inventing a fake driver to
reach two lines would test the fake.

---

<a name="m6-minor"></a>
## m6 — the debug callback list only grows, and turning it off does not

`OpenGL/_dispatch/__init__.py:333-377`

`_installed_callbacks.append(callback)` runs on every successful
`use_debug_output(True)` and nothing removes entries. Each holds a ctypes
function object; a program that enables debug output per context accumulates one
per context for the life of the process.

`use_debug_output(False)` sets the error mode back to `0` but leaves
`GL_DEBUG_OUTPUT` and `GL_DEBUG_OUTPUT_SYNCHRONOUS` enabled and the callback
registered, so the driver goes on formatting and delivering every error message
synchronously — the cost the mode was chosen to avoid — for no reader.
`GL_DEBUG_OUTPUT_SYNCHRONOUS` in particular serialises the driver.

**Fix.** Key the list by context and drop the entry on disable, and undo the GL
state:

```python
if not enable:
    _c.set_error_mode(0)
    glDisable(_DEBUG_OUTPUT_SYNCHRONOUS)
    glDisable(_DEBUG_OUTPUT)
    glDebugMessageCallback(None, None)
    _installed_callbacks.pop(gl_context_key(), None)
    return True
```


### Remediation — ✅ Fixed

**Red.** `test_turning_debug_output_off_undoes_what_turning_it_on_did` enables
four times and disables once. Failed with `held == '4'`.

**Green.** `_installed_callbacks` is a dict keyed by context handle rather than
a list, so an enable replaces rather than appends and a disable removes.
`use_debug_output(False)` now also disables `GL_DEBUG_OUTPUT_SYNCHRONOUS` and
`GL_DEBUG_OUTPUT` and clears the driver's callback — the synchronous output it
had enabled serialises the driver, which is the cost the switch exists to stop
paying.

---

<a name="m7-minor"></a>
## m7 — the retired-table comment understates the cost, and `generation` is dead

`accelerate/src/c/pygl_runtime.c:92-108, 220-227 (pygl.h)`

The retire-rather-than-free decision is right, and the reasoning — another
thread's `pygl_current` still points at the table — is exactly the argument that
justifies it. Two details are off.

**The number.** The comment says "A retired table is about 23 KB". With 4,859
commands it is `4859 * 8 + 4859` = 43,731 bytes, close to double. At 43 KB
apiece, an application that creates and destroys a context per document window
over a long session pays 4.3 MB per hundred windows, permanently. That is still
the right trade against a use-after-free, but the comment should say the real
number so the next reader can weigh it.

**A reclamation path is worth having.** The tables are unreachable, not
unfreeable: what makes freeing unsafe is that a thread may still hold the
pointer. A retired table could carry an epoch and be freed once every thread has
been observed to have switched — or more simply, freed from `pygl_py_configure`
or an explicit `dispatch.reclaim()` a long-running host can call at a quiescent
point. Either is a small amount of code and turns an unbounded cost into a
bounded one.

**`generation` is written and never read.** `pygl_py_forget_context:1994`
increments it; `pygl.h:224` describes it as guarding "a handle the driver
reused". Nothing reads it, and nothing needs to — a reused handle finds no table,
because `forget_context` sets `handle = NULL`. Delete the field and the comment,
or read it; a field whose comment claims a guarantee the code does not provide is
worse than no field.


### Remediation — ✅ Fixed

**Red.** `tests/gl/test_forget_context_safety.py::TestRetiredTablesCanBeReclaimed`
— two cases. Both failed: no such attribute `reclaim_retired`.

**Green.**

- The comment says 43 KB and where the number comes from (nine bytes per entry
  point, 4,859 commands), rather than "about 23 KB".
- `dispatch.reclaim_retired()` frees the retired list and returns how many, with
  `OpenGL._dispatch.reclaim_retired()` in front of it. Its docstring states the
  judgement it asks the caller to make and why nothing here can make it: no
  thread may still be dispatching through a destroyed context. A program with
  one or two contexts need never call it.
- `generation` is gone from `PyGLDispatch`, and the `handle` field carries the
  comment that describes the guarantee the code actually provides — a reused
  handle finds no table because `forget_context` cleared it.

---

<a name="m8-minor"></a>
## m8 — the bounds-check test covers only the path that works

`tests/gl/test_review_fixes.py:179-196`

```python
small = numpy.zeros(1, dtype='uint32')
with pytest.raises(ValueError, match='output array holds'):
    GL.glGenTextures(64, small)
```

A contiguous `uint32` array of one takes the buffer-protocol fast path, where
`have_view` is 1 and `owner == object` — the single combination on which
[B1](#b1) is not reachable. The two shapes that corrupt the heap have no test.
See B1's *Tests to add*.

The wider point: a guard against memory corruption needs its test to enumerate
the *input kinds* the acquire function distinguishes — matched buffer, converted
copy, ctypes pointer, ctypes scalar, `None` — not one representative value. That
list is four lines of `pytest.mark.parametrize` and would have caught this.


### Remediation — ✅ Fixed

Covered by [B1](#b1): the single case became a `parametrize` over the four input
shapes the acquire path branches on, plus a repeat-consistency case for a raw
pointer and an acceptance case for a correctly-sized converted array.

---

<a name="m9-minor"></a>
## m9 — `signature_for` compiles generated source

`OpenGL/_dispatch/support.py:364-383`

```python
exec(compile('def %s%s: pass' % (name, text), '<signature>', 'exec'), namespace)
```

The inputs are the generator's own `name` and `text_signature` from `.rodata`, so
this is not an injection vector today. It is still string-built source compiled
at run time on a path — `inspect.signature`, and so pydoc, Sphinx autodoc and
PyOpenGL's own documentation generator — that a client reaches. A stray quote or
bracket in a future generated signature becomes a `SyntaxError` from
`inspect.signature(glFoo)` rather than a missing signature.

Also, `_signatures` is keyed on `name` alone while the signature depends on
`text_signature` too; two APIs declaring the same name with different arity
would collide.

**Fix.** Build the `Signature` directly, which is both safer and faster:

```python
parameters = [inspect.Parameter(arg, inspect.Parameter.POSITIONAL_ONLY, …)
              for arg in argument_names]
signature = inspect.Signature(parameters)
```

`GLProc` already exposes `argNames`, and `required_args` gives the split between
required and defaulted, so the text signature is not needed to build it. Key the
cache on `(name, text_signature)` if the text form is kept.


### Remediation — ✅ Fixed

**Red.** `TestSignaturesAreBuiltNotCompiled` — five cases covering what the
signature must contain and that the module compiles no source. The last failed.

**Green.** `signature_for(proc)` takes the entry point rather than
`(name, text_signature)`, caches on `(api, name)`, and builds the
`inspect.Signature` by *reading* the text with `_parameters()` — a ten-line
reader for the grammar the generator writes (`$module`, names, `=None`, `/`).
Nothing is compiled or executed, so a generated signature that would not parse
can no longer surface as a `SyntaxError` raised against whatever pydoc, Sphinx
or PyOpenGL's own documentation generator was documenting.

Found while doing it: `required_args` is not the required count — it holds the
friendly call's arity, and was read by nothing. Its comment in `pygl.h` now says
what it holds, and points at `text_signature` for which arguments are optional.

---

<a name="m10-minor"></a>
## m10 — `OpenGL.EGL.devices` is undocumented

`OpenGL/EGL/devices.py` is new public API — `__all__`, four exported names, a
class with a documented `software` property — and the commit adds no page under
`documentation/`. [../CLAUDE.md](../CLAUDE.md) makes documentation part of the
change, and this one has a strong claim on a page: the module's own commit
message describes it as the fix for a segfault three separate callers had each
worked around, which is precisely the thing a reader needs to be able to find.

The module is also not re-exported from `OpenGL/EGL/__init__.py`, so a caller has
to know to `from OpenGL.EGL import devices` rather than reaching it from the
package they already imported.

**Fix.** A section in the EGL documentation covering `devices()`, `DeviceInfo`,
what `software` means and how it is decided, and the
`eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, device.handle, None)` call the
handle is for — the docstring already has all of this and needs only a home.

Two smaller notes on the module itself:

- `DeviceInfo._key()` excludes `handle`, which is the field that identifies the
  device, and includes `index`, which is a property of the enumeration. Two
  devices with the same driver name and extensions at different indices compare
  unequal, and the same device re-enumerated at a different index also compares
  unequal. If `EGLDeviceEXT` is not hashable, key on
  `ctypes.cast(handle, c_void_p).value`.
- `_device_string` swallows the exception but leaves EGL's own error state set,
  so the next `eglGetError` a caller makes sees an error from a query this module
  made and discarded. `eglGetError()` before returning `''` clears it.


### Remediation — ✅ Fixed

**Red.** `tests/test_egl_devices.py` gained three classes — the handle is the
identity, a failed query leaves no EGL error behind, and the module is
documented and reachable. Five cases failed.

**Green.**

- `documentation/egl-devices.html`: what `devices()` reports, what each
  `DeviceInfo` field means, how the software question is decided and in what
  order, the `driCreateNewScreen3` crash that makes it matter, and the
  `eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)` call a
  handle is for. Linked from `readme.rst` under a new section.
- `OpenGL.EGL.devices` is bound in `OpenGL/EGL/__init__.py`, so a caller who has
  imported the package reaches it as `EGL.devices.devices()`.
- `DeviceInfo._key()` is the handle's address, through `_address_of`. The device
  is the handle; `index` is a property of one enumeration.
- `_device_string` clears the EGL error its failed query recorded, so a caller's
  next `eglGetError` does not read this module's.

---

<a name="m11-minor"></a>
## m11 — the registries are fetched unpinned and unverified

`src/fetch_registries.py`

```python
result = _run(['git', 'clone', '--depth', '1', url, path])
…
_run(['git', 'reset', '--hard', 'FETCH_HEAD'], cwd=path)
```

The content of the shipped bindings — every enum value, every signature — is
whatever `github.com/KhronosGroup/OpenGL-Registry` returned at build time. There
is no recorded commit, no signature check, and the docstring argues against
pinning:

> pinning a copy of somebody else's registry in the tree only means carrying a
> stale one.

That reasoning is sound for *vendoring*, but it is a different question from
*recording what was used*. As it stands, two builds of the same PyOpenGL tag can
produce different bindings and nothing says so; and a compromised or transiently
wrong upstream produces wrong bindings that pass every test, because the tests
are generated from the same input.

`fetch_all()` already returns the commit SHAs and prints them. The remaining step
is to write them where a build can check them.

**Fix.** Record the fetched SHAs in a small lock file next to
`registry_baseline.json`, have `regenerate_c.py` fail if what it fetched differs
from the lock unless `--update-registries` was passed, and stamp them into the
generated header so a shipped wheel can say which registry it was built from.
That keeps the "always generate from current inputs" property for the person
updating, and gives everyone else a reproducible build.


### Remediation — ✅ Fixed

**Red.** `tests/cdispatch/test_registry_provenance.py` — nine cases over the
lock file, the comparison, and the generator's option. Eight failed.

**Green.** `src/cdispatch/registry_lock.json` records the commit and URL of each
registry the shipped bindings were generated from, with the date.
`fetch_registries` gained `read_lock`, `write_lock` and `differences_from`, and
`regenerate_c.py` stops with a diagnostic naming both commits when a fetch finds
something the lock does not record. `--update-registries` takes the newer ones
and records them, so moving forward is a decision with a diff attached.

The docstring keeps the argument against vendoring, which is right, and
separates it from the question this answers: recording *which* commit was used
costs a hundred bytes and does not carry anybody else's tree.

---

<a name="m12-minor"></a>
## m12 — `make_current` and `forget_context` act on the wrong flag

`OpenGL/_dispatch/__init__.py:417-432`

```python
def make_current(handle):
    _end_suspended_block()
    if AVAILABLE:
        _c.make_current(int(handle or 0))
```

`AVAILABLE` means the extension imported; `ACTIVE` means it is the
implementation. With `PYOPENGL_DISPATCH=ctypes` the first is true and the second
is false, so these calls reach into a layer that has never been configured
(`pygl_support` is `NULL`) and allocate a 43 KB dispatch table per context for a
process that will never dispatch through one.

Nothing breaks — the tables are simply unused — but the guard says something the
code does not mean, and an application following the documentation's advice to
call `make_current` pays for tables it cannot use.

**Fix.** `if ACTIVE:` in both, matching `suspend_error_checking` and
`set_error_checking` immediately above and below them.


### Remediation — ✅ Fixed

`make_current` and `forget_context` test `ACTIVE`, matching
`suspend_error_checking` and `set_error_checking` either side of them. With
`PYOPENGL_DISPATCH=ctypes` they are now no-ops rather than allocating a 43 KB
dispatch table per context for a process that will never dispatch through one.

`forget_context`'s docstring says what it does — retire, not free — and points
at `reclaim_retired` for the rest.

---

## Documentation changed

- **`documentation/egl-devices.html`** — new. What `OpenGL.EGL.devices` reports,
  what each `DeviceInfo` field means, how the software question is decided and in
  what order, the Mesa crash that makes it matter, and the
  `eglGetPlatformDisplayEXT` call a handle is for ([m10](#m10-minor)).
- **`readme.rst`** — a "Rendering without a display server" section linking it.
- **`OpenGL/_dispatch/finder.py`** — the module docstring states the default the
  code has, and the measurements are reframed as the reason the generated files
  were *removed* rather than shadowed, which is what they argue
  ([m3](#m3-minor)).
- **`OpenGL/_dispatch/__init__.py`** — `use_debug_output`'s docstring now
  describes behaviour that is true ([M2](#m2)); `forget_context` says it retires
  rather than frees and points at the new `reclaim_retired`
  ([m7](#m7-minor), [m12](#m12-minor)).
- **`OpenGL/GL/shaders.py`** — `check_validate` documents `validation_deferred`
  ([m4](#m4-minor)).
- **`src/fetch_registries.py`, `src/regenerate_c.py`** — both docstrings describe
  the lock file, why recording a commit is not vendoring, and what
  `--update-registries` is for ([m11](#m11-minor)).
- **`accelerate/src/c/pygl.h`** — the `PyGLDispatch` and `required_args` comments
  describe what the code does rather than what was intended
  ([m7](#m7-minor), [m9](#m9-minor)).

`documentation/c-dispatch.html` needed no change: its
`PYOPENGL_VIRTUAL_MODULES=0` paragraph already agreed with the code, and it was
the finder's docstring that did not.

---

## New tests

| File | What it holds |
|------|---------------|
| `tests/test_declaration_types.py` | The type-expression vocabulary, what is refused, that one reader serves both routes, and a sweep of all 23,426 expressions in the shipped tree |
| `tests/gl/test_debug_output_parity.py` | That GL_KHR_debug reporting is a cheaper notice and not a different policy; that `err` is a GL error code; that disabling undoes enabling; that a raiser which declines is not a `SystemError` |
| `tests/test_attribute_surface_api.py` | `GLProc.api`, the two `glClear`s, and signatures built rather than compiled |
| `tests/cdispatch/test_registry_provenance.py` | The registry lock file and the comparison against it |
| `tests/gl/test_review_fixes.py` | Undersized output arrays, parametrised over the four shapes the acquire path branches on |
| `tests/test_dispatch_selection.py` | That a mismatched accelerate/PyOpenGL pair is refused |
| `tests/test_packaged_loaders.py` | That a damaged declaration table says so |
| `tests/test_virtual_modules.py` | That the flag is parsed in one place |
| `tests/test_egl_devices.py` | Device identity, the EGL error a failed query leaves, and that the module is documented |
| `tests/gl/test_forget_context_safety.py` | That retired tables can be reclaimed |
| `tests/gl/test_compile_program_validation.py` | That a deferred validation is recorded, and what the sampler-type set holds |
