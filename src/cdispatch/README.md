# The C dispatch generator

How the C implementation of the entry points is produced, and how to change it.
For what the layer *does*, see `documentation/c-dispatch.html`; this is the
other half — how to maintain it.

## Running it

```bash
python src/regenerate_c.py     # read the tree and the registry, write the C
python src/check_registry.py   # what upstream changed, and what needs a person
```

`regenerate_c.py` is idempotent and rewrites a file only when its content
changes, so running it on an unchanged tree produces an empty diff. It writes:

| output | what it is |
|---|---|
| `src/c/generated/pygl_<API>.c` | one C function per entry point, per namespace |
| `src/c/generated/pygl_elements.h` | the array element descriptions stubs name |
| `src/c/generated/pygl_glgets.h` | the pname → output-size tables |
| `src/c/generated/pygl_generated.c` | registration of every table |
| `src/c/generated/manifest.json` | counts, generator version, registry commit |
| `OpenGL/_dispatch/_tables.py` | array-type names and slot assignments |
| `OpenGL/<API>/__init__.pyi` | the type stubs |

Rebuild afterwards; an editable install compiles the extension in place:

```bash
pip install -e .            # or: uv pip install -e . --no-build-isolation
PYOPENGL_DISPATCH=c python -m pytest tests/
```

## The pipeline

Five steps, each its own module, each tested in `tests/cdispatch/`.

**1. `extract.py` — read the shipped tree.** `OpenGL/raw/**` is parsed by AST,
not imported, so extraction needs no GL context and no working build. Each
`@_f @_p.types(...) def glFoo(a, b): pass` becomes a `Command`. The friendly
modules above them are parsed the same way, and their
`wrapper.wrapper(x).setOutput(...)` chains become the annotations.

Two things it does that are easy to miss:

- A binding is keyed by **`(api, name)`**, not by name. `glTexImage2D` exists in
  GL and in GLES2 as separate bindings resolved from separate libraries.
- It **cross-checks the Khronos registry** for parameter sizing. Reading the
  friendly modules alone marks `glReadPixels` as pass-through, because
  `images.py` reaches it through a differently-named wrapper; the registry's
  `COMPSIZE(format,type,…)` says what it really is.

**2. `model.py` — the command record.** One record per entry point, and
everything emitted is a field in it:

```
command   := name, api, feature, deprecated, return-type, [parameter]
parameter := name, c-type, direction, size-spec, retain?, output-order?
size-spec := none | Fixed(n) | FromArg(index, divisor) | GLGetTable(pname-arg)
           | ImageSize(...) | StringArray | Computed(helper)
```

**3. `ctypes_model.py` — the type vocabulary.** Which converter macro reads a
parameter, which C type the stub casts the slot to, and — for arrays — which
`struct` format code a buffer must export to take the fast path.

**4. `emit_c.py` — the stub.** Macro invocations only, so a registry update
produces a diff where each new entry point is one readable block:

```c
static PyObject *
pygl_GL_glGenTextures(GLProc *self, PyObject *const *_a, size_t _nargsf)
{
    PYGL_ARITY_RANGE(1, 2);
    PYGL_FRAME(1);
    PYGL_SZ(0, n);
    PYGL_CONV_OK();
    PYGL_ARRAY_OUT(1, textures, &pygl_elem_GLuint, (Py_ssize_t)(n));
    PYGL_CALL_V((int, void *), (n, textures));
    PYGL_CHECK();
    PyObject *_value = pygl_output_value(&_bufs[textures_slot], &pygl_elem_GLuint,
                                         (Py_ssize_t)(n));
    PYGL_CLEANUP();
    return _value;
_fail:
    PYGL_CLEANUP();
    return NULL;
}
```

The macro vocabulary is in `src/c/pygl.h`. The shape is always the same: check
the arity, declare the cleanup frame, convert the scalars, one `PYGL_CONV_OK`,
acquire the arrays, call, check, clean up. Scalars come before arrays so that
nothing needs unwinding while only scalars have been converted.

**5. `emit_pyi.py` — the stubs.** From the same record, so
`glGenTextures(n, textures=None) -> UIntArrayResult` falls out of the size and
direction annotations rather than being written.

## The rule everything else follows

> The fast path may accelerate, never reject.

A buffer whose format matches is used directly. **Anything else falls through to
`ArrayDatatype`**, which converts exactly as it does today. A mismatch is a
cheap branch, not an error. Any new validation added to the C must be justified
against this: if it can refuse an argument the ctypes layer accepts, it is
wrong, and `tests/gl/test_array_acceptance.py` is where that is caught.

## Adding an entry point that needs real C

Some entry points promise a computation rather than a description of their
arguments. `glShaderSource` takes one string or several, as `str` or `bytes`,
and works out the count and the lengths. No table expresses that.

1. Write `pygl_hand_glFoo` in `src/c/pygl_handwritten.c`.
2. Add a row to `ENTRIES` in `handwritten.py`: which APIs it serves, the C
   symbol, the argument names the friendly form takes, its signature line, and
   `c_arg_names` — what `argNames` should keep reporting, which is what it
   reports today.
3. `python src/regenerate_c.py`, rebuild, test.

The generator then emits its metadata and table entry pointing at your function,
and a customisation call that restates what it already does returns the entry
point rather than demoting it.

## Adding an array element type

Add a row to `_ELEMENTS` in `ctypes_model.py` naming the `struct` format code,
the item size and the `OpenGL.arrays` class the slow path converts through.
**No C changes and no stub changes.** An element type with no format code never
matches, so every call for it takes the Python path — correct, if unaccelerated,
from the day the type appears.

## Why an entry point might not be emitted

`emit_c.exclusion_reason(command)` answers for any command, and
`check_registry.py` prints the tally. Every command on the ctypes path has a
reason; none is there by accident, and `tests/cdispatch/test_coverage.py`
asserts that.

The families still excluded are the four Tier 3 ones the plan schedules one per
release — images, the variadic entry points, client-side array pointers, string
arrays — plus struct-pointer returns and five commands whose outputs are not
their trailing arguments.

## Keeping up with upstream

`.github/workflows/registry-update.yml` pulls the registry weekly,
regenerates, and opens a pull request when anything changed.

The shipped tree already lags the registry — 7 commands, 3 argument-name
differences, 158 enums — none of it caused by this work. Those are recorded in
`registry_baseline.json` with a reason, so the tooling reports only what is new
since. After a deliberate regeneration, `python src/check_registry.py
--write-baseline` records what remains.

## Where the tests are

| file | what it holds |
|---|---|
| `tests/cdispatch/` | the generator: model, extraction, emission, coverage |
| `tests/test_attribute_surface.py` | every entry point's attributes, both implementations compared |
| `tests/test_dispatch_selection.py` | choosing, and falling back where no extension was built |
| `tests/gl/test_array_acceptance.py` | the accelerate-never-reject rule |
| `tests/gl/test_buffer_lifetime.py` | buffers released on every path out of a call |
| `tests/gl/test_multi_context.py` | N contexts, N tables |
| `tests/gl/test_threaded_dispatch.py` | a thread that has never dispatched |
| `tests/gl/test_debug_error_checking.py` | `GL_KHR_debug` |
| `tests/gl/test_no_context_calls.py` | `CONTEXT_CHECKING` |
| `tests/gl/test_late_context_resolution.py` | probing before a context exists |

Run the suite under **both** implementations — that is what `tox`'s dispatch
axis is for. A test that passes under one and not the other is a defect in
whichever is wrong, and there is no way to tell which without running both.

A GL test must never call `glfw.terminate()`: the library is initialised once
for the whole run and shared, and tearing it down leaves every later test
calling into an uninitialised GLFW. Destroy your windows and leave it alone.
