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
| `accelerate/src/c/generated/pygl_<API>.c` | one C function per entry point, per namespace |
| `accelerate/src/c/generated/pygl_elements.h` | the array element descriptions stubs name |
| `accelerate/src/c/generated/pygl_glgets.h` | the pname → output-size tables |
| `accelerate/src/c/generated/pygl_generated.c` | registration of every table |
| `accelerate/src/c/generated/manifest.json` | counts, generator version, registry commit |
| `OpenGL/_dispatch/_tables.py` | array-type names and slot assignments |
| `OpenGL/<API>/__init__.pyi` | the type stubs for the whole namespace |
| `OpenGL/<API>/**/*.pyi` | one per friendly module, so an editor can see into it |
| `OpenGL/_typing.pyi` | the array aliases those annotate with; stub-only |

Rebuild afterwards; an editable install compiles the extension in place:

```bash
pip install -e .            # or: uv pip install -e . --no-build-isolation
PYOPENGL_DISPATCH=c python -m pytest tests/
```

## The pipeline

Five steps, each its own module, each tested in `tests/cdispatch/`.

**1. `extract.py` — read the shipped tree.** One `Command` per entry point,
built from the marshalled declaration tables (`OpenGL/raw/_declarations/*.dat`)
and the annotation table. Nothing is imported, so extraction needs no GL
context and no working build. The AST pass that reads a friendly module's
`wrapper.wrapper(x).setOutput(...)` chains is still here, behind
`read_chains=True`; generation does not use it (see 1c).

Two things it does that are easy to miss:

- A command declared twice keeps **both** extension names. The core
  declaration wins where there is one, and the loser's name goes on the
  winner's `extensions`, because 223 commands are declared by two extensions
  with neither in core and a driver advertising either has the function.
- A binding is keyed by **`(api, name)`**, not by name. `glTexImage2D` exists in
  GL and in GLES2 as separate bindings resolved from separate libraries.
- It **cross-checks the Khronos registry** for parameter sizing. Reading the
  friendly modules alone marks `glReadPixels` as pass-through, because
  `images.py` reaches it through a differently-named wrapper; the registry's
  `COMPSIZE(format,type,…)` says what it really is.

**1b. `modules.py` — read what the generated modules contain.** The same AST
pass, asking a different question: not what an entry point's signature is but
what each `OpenGL/raw` module *defines* — its constants, its re-exports, and
for each entry point the `@_p.types(...)` signature its declaration stated.
That becomes a C table (`pygl_modules.c`), which the finder in
`OpenGL/_dispatch/finder.py` builds module objects from. The signature is carried because running the
declaration is what recorded the ctypes binding a client demotes to, and
nothing runs it when there is no file. A module with a class or a conditional
in it is not data, so it is marked hand-written and keeps its file.

**1c. `annotations.py` — the customisations as data.** The registry gives
every signature; what it does not give is the difference between that and the
Python one, which people wrote over 28 years as `wrapper.wrapper(...)` chains.
`annotations.json` holds those: 2,079 entries, parameters keyed by name, and it
is what generation reads — `extract_tree(read_chains=False)`, no Python under
`OpenGL/` parsed at all. The parse survives for the 28 modules whose chains the
table cannot express, and for the tests that hold the two copies to each other:
`test_generation_is_data_driven.py` emits every stub from each source and
compares the C, `test_annotation_wrapping.py` checks that applying the table
builds the wrapper the chain builds.

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

The macro vocabulary is in `accelerate/src/c/pygl.h`. The shape is always the same: check
the arity, declare the cleanup frame, convert the scalars, one `PYGL_CONV_OK`,
acquire the arrays, call, check, clean up. Scalars come before arrays so that
nothing needs unwinding while only scalars have been converted.

**5. `emit_pyi.py` — the stubs.** From the same record, so
`glGenTextures(n, textures=None) -> UIntArrayResult` falls out of the size and
direction annotations rather than being written. Two kinds, described below.
`exceptional.py` supplies what the record cannot: the names `OpenGL.GL` exports
through a wrapper of its own, and the shorter call each of those takes.

## The type stubs

Two kinds, from one emitter, both written by the `stubs_root` half of
`generate()`:

| what | from | holds |
|---|---|---|
| `OpenGL/<API>/__init__.pyi` | `emit_pyi.emit_module` | every entry point in the namespace, with docstrings |
| `OpenGL/<API>/**/*.pyi` | `emit_pyi.emit_submodule` | one module's names, signatures only |
| `OpenGL/_typing.pyi` | `emit_pyi.emit_typing_stub` | the array aliases both annotate with |

The per-module kind exists because **a friendly module has no names in its
source**. `OpenGL/GL/ARB/vertex_array_object.py` says
`_define(globals(), 'OpenGL.raw.GL.ARB.vertex_array_object')` and its namespace
arrives from the declaration tables at import. Nothing reading the file can
follow that, so without a stub an editor offers no completion inside the module
and a checker types every name in it as `Any` — which is what the generated
files used to provide by existing. Deleting them took that with it; these put
it back without the files.

`generate._write_submodule_stubs` walks the module table, so what a stub
declares is what the module will actually be given: `module.constants`,
`module.commands` looked up in the command records for their signatures, and
`module.reexports` mapped from `OpenGL.raw.X` to `OpenGL.X` — except the
private ones (`_types`, `_errors`, `_glgets`), which have no friendly module
above them and are named where they are.

`generate._module_definitions` then parses the friendly module itself, for what
it states in Python rather than taking from a table: its `glInitXxx`, the
constants it aliases by hand (`GL_DEPTH_BUFFER = GL_DEPTH`), any helper it
defines. **A name the tables already describe is skipped** — a module that
customises an entry point rebinds its name, and describing that as `Any` would
throw away the signature the record knows.

Four decisions worth keeping:

- **Signatures, no docstrings.** The API-level stub carries the prose; 1,300
  copies of it would be most of the wheel. As it stands the per-module stubs
  are 1.1 MB of source and 0.38 MB of a 4.3 MB wheel.
- **No `__all__`.** A stub exports what it defines, so listing the names again
  would be a second copy of every module in every module.
- **Aliases imported by name**, not `import *`: a stub re-exports an import
  only when asked to, so naming them keeps `FloatArray` out of what
  `from OpenGL.GL.VERSION.GL_1_1 import *` means.
- **`OpenGL/_typing.pyi` is stub-only.** There is no such module at run time
  and nothing imports it; a checker resolves it like any other stub, and one
  copy of the aliases beats 1,300. `from OpenGL._typing import ...` in real
  code is an ImportError.

Both `pyproject.toml`'s `package-data` and `MANIFEST.in` have to list them, or
they are generated and never shipped. `tests/test_module_stubs.py` holds every
stub to the names its module actually ends up with — following re-exports the
way a checker does, so a name that arrives through one counts as described —
and `tests/cdispatch/test_emit_pyi.py` covers the emitter itself.

### Wrappers the registry cannot describe

`OpenGL/GL/__init__.py` ends with `from OpenGL.GL.exceptional import *`, so for
a handful of names the callable a program reaches is a wrapper written by hand
rather than the entry point the registry describes. Each takes a call the C
form cannot: `glDeleteTextures(textures)` reads the count from the array it is
given, and `glMap2d` computes the strides from the shape of the points.

The registry knows only the C form, so a stub derived from it alone contradicts
the library — it reports an error against the call the wrapper's own docstring
gives. `exceptional.py` in this directory carries one row per wrapper: the
Pythonic parameter list, what it returns, and whether the wrapper also passes
the C form through. `emit_pyi.emit_module` reads it, and emits

- **an overload pair** where both calls are real, wrapper's form first, so an
  ambiguous call resolves to the one the docstring gives; or
- **a single `def`** where only the wrapper's form is, as for the `glMap`
  family — offering the C form there would describe a call that raises
  `TypeError`.

Only the namespace that has wrappers imports `overload`, so the other seven
API stubs are unchanged by this.

`tests/bindings/generated/test_exceptional_stubs.py` holds the three things
that can go wrong: a stub demanding more arguments than the wrapper needs, a
row claiming a call the wrapper cannot take, and the C form being offered where
the wrapper does not pass it through. The middle one is what keeps the row
honest — without it the stub and the row would agree with each other and both
be wrong, since the emitter writes what the row says.

Adding a wrapper: write it in `OpenGL/GL/exceptional.py`, add it to that
module's `__all__`, add a row to `exceptional.py` here, and regenerate.

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

1. Write `pygl_hand_glFoo` in `accelerate/src/c/pygl_handwritten.c`.
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

Twenty remain. Eleven are GLX queries returning a pointer to an X11 struct —
`XVisualInfo *`, `GLXFBConfig *`, `Display *` — which a caller passes back to
Xlib rather than reads. Seven have an output argument that is not the last one,
so no arity distinguishes "the caller omitted it". The other two are a
converter and `glShaderSource`, which is hand-written beside the generated
ones.

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
| `tests/test_virtual_modules.py` | the built modules against the files, name for name |
| `tests/test_module_stubs.py` | every module's stub against the names the module has |

Run the suite under **both** implementations — that is what `tox`'s dispatch
axis is for. A test that passes under one and not the other is a defect in
whichever is wrong, and there is no way to tell which without running both.

A GL test must never call `glfw.terminate()`: the library is initialised once
for the whole run and shared, and tearing it down leaves every later test
calling into an uninitialised GLFW. Destroy your windows and leave it alone.
