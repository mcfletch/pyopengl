# Static gates, from what the last three years of fixes were

A reading of the 427 commits on this repository since 2023-10-27, of which 132
are a fix or carry one. The question is not what each defect was but what
*kind* it was, and which kinds a tool that reads the tree could refuse to let
back in.

Commits here carry a prefix, so the first pass was mechanical: `FIX`, `BUGFIX`,
`REVIEW`, and every subject naming a crash, a leak, a wrong answer or a
refusal. The classes below come from reading those messages, and each names the
commits a reader can check it against.

The dividing line that matters: some of these classes are statements about the
*text* — a handler that cannot fire, a declaration missing its types, a flag
read from the wrong place — and a parser settles those for every platform at
once, in a second, on a machine with no GPU. The rest are statements about a
driver, a context or a window system, and no parser will ever answer them.
[The classes a parser cannot answer](#the-classes-a-parser-cannot-answer) says
which are which, so that the tooling proposed here is not asked to do work the
matrix has to do.

## The classes

### A. An error path that has never run

The largest single class, and the one that reads worst on a ticket: the program
is already in trouble, and the code written to report it does something else.

- `_WGLQuerier.pullExtensions` ends in `except AttributeError: return []`, and
  the lookup that raises it sat outside the `try`, so the clause could never
  run (990e73f5).
- `glutDestroyWindow`'s cleanup handler logged a variable the failing line had
  never assigned, so the report was a `NameError` raised inside the `except`,
  and that second error stopped the destroy call itself (9a8cad14).
- The check-script runner passed no timeout to `communicate()` beside its
  `except subprocess.TimeoutExpired` — the intent was there and the argument
  was missing, so a hung script was a cancelled job rather than a failed case
  (77d62ff8).
- `RawOpengl.render` restored a matrix mode read as a float, and the
  `glMatrixMode` in the `finally` refused it; the buffers are swapped after
  that block, so the drawn frame went with the exception (486ffe08, 5df56d7f).
- Six bare `except:` clauses around weakref creation were swallowing
  `KeyboardInterrupt` (pydispatcher 2e8af05, the same shape one repository
  over).

What these have in common is not a syntax: it is that no test has ever entered
the block. See [Gate 1](#gate-1-every-error-path-is-entered) and
[Gate 2](#gate-2-possibly-undefined).

### B. A declaration that does not describe the thing declared

ctypes is lenient in exactly the wrong direction. A function with no `argtypes`
accepts any arguments at all, and one with too few accepts the rest unchecked.

- `OpenGL.Tk`'s Windows implementation reached `GetDC`, `SetPixelFormat` and
  the rest through `ctypes.windll` with no prototypes, and ctypes gives an
  undeclared function a return type of C `int` — half the width of an `HDC`
  (bd64db34).
- `_GLXQuerier.getDisplay` passed `XOpenDisplay` a `str`; with no `argtypes`
  ctypes passes `wchar_t*`, the connection fails, and the querier answers GLX
  version `[0, 0]` with an empty extension list — which is the gate every GLX
  entry point is resolved through (b9f5fca6).
- Three OSMesa declarations disagreed with themselves and were invisible for
  the same reason (dc7b5403). `*GetCurrentContext` returned a pointer on one
  platform and an int on another (43bfebca).
- On the friendly-wrapper side, the customisation vocabulary names parameters
  as strings — `setInputArraySize('indices', None)` — and a name that is not
  there does not fail: the wrapper is built, the module imports, and the
  customisation silently does not happen. Khronos renamed the parameters of
  fourteen entry points in one commit (15c6a96c, #38).

See [Gate 6](#gate-6-the-customisation-vocabulary-names-real-parameters) and
[Gate 7](#gate-7-a-foreign-function-is-fully-declared).

### C. Two copies of one idea, drifted

Every one of these was invisible until somebody ran the half nobody runs.

- `PYOPENGL_ERROR_CHECKING=0` made `import OpenGL.GLES2` fail outright.
  `OpenGL/raw/GL/_errors.py` has always guarded the construction; GLES2's and
  GLSC2's `_types.py` did not (2247fbfc, #166).
- The compiled `_ErrorChecker` carries `checkContext`; the ctypes one carried
  no such name, and the case that would have said so asked only the build that
  had it (f81e8b06).
- The ctypes array handlers took only a sequence where numpy's took a length,
  so `glGenVertexArrays(1)` — the plainest call there is — failed on an
  installation without numpy (2c242faf).
- `ARRAY_TYPES` was a generated list and the extension read it at an index
  compiled into the element table; the two agreed only by convention
  (9b31283e).
- Fourteen modules could not be imported at all, `OpenGL/raw/GLSC2/_types.py`
  not existing being most of it (aab9690d).
- Three coverage scanners each grew their own idea of which files to read
  (6fe0e504); nine modules each `ast.parse`d a `.pyi` in a shape of its own
  (5079b48f); four modules each carried a copy of the backend list
  (b861a410).

See [Gate 4](#gate-4-sibling-families-do-not-diverge-unannounced) and
[Gate 5](#gate-5-parallel-implementations-have-one-surface).

### D. A flag that is read somewhere other than where it is set

- `OpenGL.ERROR_ON_COPY = True` after `import OpenGL.GL` changed nothing and
  said nothing: the flags are frozen into `OpenGL._configflags` when the first
  entry point is built. Two tickets are that, and both were spent looking at
  the array machinery (278764bd, #5, #159).
- `SIZE_1_ARRAY_UNPACK` was the one flag in the list that was not an
  `environ_key`, so `PYOPENGL_SIZE_1_ARRAY_UNPACK` did nothing, nothing could
  select the behaviour, nothing tested it, and it had stopped working
  (a242fd51).
- `USE_ACCELERATE` was read from the `_configflags` snapshot, which is taken
  when that module is first imported — possibly by a framework or a profiler,
  before the caller's assignment (ee05ec45); `install()` then never read it at
  all (dbfeea5e).

See [Gate 8](#gate-8-one-story-about-when-each-flag-is-read).

### E. A test, marker or gate that holds nothing

- mypy reported success because it was not looking: PyOpenGL declared no
  `[tool.mypy]` and ran no checker in CI, so 1,307 shipped stubs were held to
  nothing, and a wrong stub reached a release (9c6b0fc0). One repository over,
  `mypy` without `disallow_untyped_defs` skipped the bodies of 44 public entry
  points (opengl_extrusions 9ed47ae) and 326 function bodies (pyvrml97
  3efbc67).
- `select` unset left ruff's own default deciding, and that default has widened
  between releases: 5,099 findings came to 91 once it was pinned, and four of
  those were live defects — three `cnf={}` defaults shared by every widget, and
  two assertion messages ending `expected %`, so a *failing* case raised
  `ValueError` instead of reporting (9065e14d).
- `test_checks.py` named its 27 scripts in hand-written stubs, which is how two
  of them sat in the directory for years having never been launched (7541a7e3).
  The accelerate suites ran in no CI job at all (0f7fed74). The `typecheck`
  environment was not in the matrix (ab01fe4b). `tox.ini` declared `py39` cells
  and the matrix started at 3.10 (0871b04c).
- `exercise()` swallowed any `GLError` and drained the queue, at 98 sites, so a
  case could pass with every call in it failing (a0c8ab6c).
- `@pytest.fixture` over `@staticmethod` reads the function's `__name__`, which
  a `staticmethod` object does not carry before 3.10, so three modules failed
  to collect on the oldest supported interpreter (21b10182).
- A module-scope import of an optional library in a test is a *collection*
  error, and pytest abandons the run rather than the module — four modules
  reaching for EGL (a75d39f0), a `parametrize` argument importing numpy
  (ecc970b9), `from numpy import *` bringing numpy's own `test` object into the
  namespace (ec7d55d7), a name reached only under a non-default flag
  (0cee944c).

See [Gate 9](#gate-9-a-test-that-cannot-fail) and
[Gate 10](#gate-10-a-declared-gate-runs).

### F. The interpreter floor is a claim nothing checked

- `zip(strict=True)` is a 3.10 keyword and six cells of the matrix could not
  collect (b56d9cb3). The C used `Py_NewRef` twenty times against a 3.9 floor;
  on 3.9 the build emitted a warning, produced no extension, and — the
  extension being optional — `PYOPENGL_DISPATCH=c` silently ran ctypes, so the
  axis passed while testing the opposite of what it named (a37eef61).

See [Gate 3](#gate-3-the-interpreter-floor).

### G. Array and scalar semantics

- Reading a size-1 result decided the shape from how `int()` failed, and how it
  fails is not one thing: `ValueError` on a ctypes array, and on a numpy array
  that is not zero-dimensional it raises on some versions and warns on others
  (f849942a).
- Nineteen cases compared a one-element status query with a scalar —
  `glGetShaderiv(shader, GL_COMPILE_STATUS) == GL_TRUE`. Under numpy that
  comparison is truthy whatever the query answered (87c67ed6).
- Numpy scalars where an integer is wanted (6d5d0f14, and the same again in
  three sibling projects).

A parser reaches only the edge of this one; see
[the classes a parser cannot answer](#the-classes-a-parser-cannot-answer).

## The gates

Ordered by what they cost against what they reach. Each says what it reads and
what it reports against the tree as it stands.

Where they live: the project-specific ones belong in `tests/` as ordinary
pytest modules, which is the idiom the suite already uses for questions about
the syntax tree — `tests/stubs.py`, `tests/gl/enum_age_audit.py`,
`tests/bindings/generated/test_wrapper_parameter_names.py`. A gate in the suite
runs on every matrix row and carries its reason in its own docstring. The ones
that are somebody else's tool go in `tox.ini` beside `lint` and `typecheck`.

### Gate 1: every error path is entered

**Class A.** An AST pass enumerates every `ExceptHandler` and every `finally` in
`OpenGL/`; `coverage.py`, already configured here, says which ones the suite
entered; a recorded list carries the ones that are deliberately unreachable on
this platform, each with the reason. A handler that is new and unentered fails.

This is the only mechanism that reaches all of class A at once. A handler
written for the wrong exception, a handler whose body raises, a `finally` that
throws away the frame it was protecting — none of them has a syntax in common,
and all of them share never having run.

Cost: one pass over the tree, plus the coverage run the suite already does.
The recorded list is the work, and it is a one-off.

### Gate 2: possibly-undefined

**Class A.** mypy has an error code for the `NameError`-inside-the-handler
shape, and it needs none of the annotation work the main typecheck would.

```
mypy --follow-imports=skip --ignore-missing-imports \
     --disable-error-code=... --enable-error-code possibly-undefined OpenGL/
```

`[tool.mypy]` here deliberately covers the `.pyi` surface alone, and says why:
the package's own source reports around 240 findings, overwhelmingly mypy
failing to model the dynamic dispatch layer. This is a second run with one
error code, which sidesteps that entirely.

Measured against the tree today: **four findings**, and each wants a look.

| Site | Name |
|------|------|
| `OpenGL/GLUT/special.py:66` | `_exitfunctype` |
| `OpenGL/GLU/glunurbs.py:161` | `cb` |
| `OpenGL/arrays/numpymodule.py:243` | `USHORT_TYPE` |
| `OpenGL/arrays/numpybuffers.py:93` | `USHORT_TYPE` |

`GLUT/special.py` is the same file 9a8cad14 fixed.

### Gate 3: the interpreter floor

**Class F.** `vermin --target=3.9 --violations` over `OpenGL/`, `tests/` and
`src/`, as a tox environment; for the C, a name list checked against the
CPython version each API arrived in.

`requires-python` says 3.9 and the trove classifiers say 3.9, and CI runs a
`py39-num1-accel0-dispctypes` row, so the claim is made in three places. What
the row cannot catch is a file it does not reach.

Against the tree today: `tests/bindings/test_accelerate_generated_c.py:405`
imports `tomllib` inside `TestNumpyIsABuildRequirement.requires`, with no guard
and no skip on the class. `tomllib` arrived in 3.11. The py39 row collects that
module.

### Gate 4: sibling families do not diverge unannounced

**Class C.** For each file name occurring in more than one `OpenGL/raw/<API>/`,
parse it, reduce it to a skeleton — imports, guard conditions, assignment
targets, definitions — with the API's own name erased, and group the APIs by
skeleton. A shape class that is not in the recorded list, with a reason, is a
failure.

This is the gate that would have caught 2247fbfc before a user did. It is also
the one that says most about the tree right now:

| Family | APIs | Distinct shapes |
|--------|------|-----------------|
| `_errors.py` | 9 | 6 |
| `_glgets.py` | 8 | 2 |

Some of those six are real differences — EGL carries its own error class, GLX
and WGL have nothing to poll, GL alone offers the checker to the debug-output
path. Each of those is a sentence somebody can write once. What the gate buys
is that the seventh shape has to be explained before it ships.

### Gate 5: parallel implementations have one surface

**Class C.** `tests/test_attribute_surface.py` already compares the two dispatch
implementations across 1,266 entry points in separate processes, and bb20c441
turned three of its prose `BY_DESIGN` reasons into predicates that are checked.
Extend the same shape to the other paired implementations:

- the two `_ErrorChecker`s: every public name and every keyword parameter
  (f81e8b06),
- the ctypes and numpy array handlers: every method must accept the same call
  (2c242faf),
- the Python and Cython halves wherever both exist.

The rule the existing test states is worth keeping as the rule: a difference
that is not in the table is a failure, and a table entry with no predicate
licenses whatever happens to be true.

### Gate 6: the customisation vocabulary names real parameters

**Class B.** `tests/bindings/generated/test_wrapper_parameter_names.py` holds
`setInputArraySize` and `setOutput` names to the entry point's `argNames`
(15c6a96c). Widen it to the rest of the vocabulary — `setPyConverter`,
`setCConverter`, the `pnameArg` and `orPassIn` keywords, `OpenGL.lazywrapper`'s
69 wrappers and the seven hand-written forms in `OpenGL/GL/exceptional.py` —
and to the annotation table, which is now the other half of the same facts.

A rename upstream must be a red test rather than a checked call quietly
becoming an unchecked one.

### Gate 7: a foreign function is fully declared

**Class B.** An AST pass over `OpenGL/` finds every foreign function reached
through `windll`, `cdll`, `CDLL`, `WinDLL` or `createBaseFunction`, and requires
`argtypes` and `restype` to be set for each before any call site. A `str`
literal passed where the declaration says `c_char_p` is a failure in the same
pass.

The places to point it at first are `OpenGL/platform/win32.py:128`
(`GDI32 = ctypes.windll.gdi32`), `OpenGL/WGL/offscreen.py:157-159` and
`OpenGL/Tk/win32.py` — which is where bd64db34's `HDC` lost its top half, on
the platform none of us runs day to day.

### Gate 8: one story about when each flag is read

**Class D.** An AST pass reads three things — the flag assignments in
`OpenGL/__init__.py`, the import list in `OpenGL/_configflags.py`, and the
flag paragraphs in the package docstring — and requires them to agree:

- a flag the docstring says is settable from the environment is assigned
  through `environ_key`;
- a flag read live off the package, as `USE_ACCELERATE` deliberately is, says
  so where it is declared;
- a flag read from the snapshot is not also read off the package elsewhere.

Against the tree today: four of the eighteen flags — `WARN_ON_FORMAT_-`
`UNAVAILABLE`, `FORWARD_COMPATIBLE_ONLY`, `MODULE_ANNOTATIONS`,
`TYPE_ANNOTATIONS` — are plain assignments sitting in a list of fourteen
`environ_key` calls, so the environment variable a reader would expect does
nothing. That is the shape a242fd51 was. `OpenGL/GL/ARB/shader_objects.py:222`
reads `OpenGL.ERROR_CHECKING` off the package at import time while the wrappers
beside it read the snapshot.

### Gate 9: a test that cannot fail

**Class E.** One AST pass over `tests/`, several rules, each of which is a
defect this suite has actually had:

| Rule | From |
|------|------|
| `pytest.raises(Exception)` / `assertRaises(Exception)` names the exception instead | openglcontext 24122fa |
| `@pytest.fixture` is the outermost decorator | 21b10182, glisteel a73a254 |
| no module-scope import of an optional library in a module that declares a skip for it | a75d39f0, ecc970b9, 8ab756e2 |
| no `import *` from a third-party package in a test module | ec7d55d7 |
| a string literal naming a `.py` script or a fixture file resolves on disk | 7541a7e3, openglcontext 5333966 |
| `exercise(` carries an explicit list of the codes it tolerates | a0c8ab6c |
| a `skip` or `skipif` carries a reason | 5333966 |

Measured today: the first rule reports nothing, which is worth keeping. The
last three are the ones with work behind them.

`-ra` in `addopts` belongs with this, so that a run states its skips rather
than counting them: the first run with it on, one repository over, found two
tests that had been skipping for seven weeks while claiming to cover teapot
rendering (openglcontext 5333966).

### Gate 10: a declared gate runs

**Class E**, and the one that makes the other nine durable. A gate nothing runs
is a gate that stops being true, and this repository has had that four times in
three months.

`tools/preflight.py` in the workspace above already holds a project to its
declared configuration — its own header says that configuration nothing runs is
how a release goes out with a defect its own settings would have caught. The
extension is a cross-check of the run graph:

- every factor in `tox.ini`'s `envlist` is named by some CI row, and every CI
  row names an environment tox declares;
- every marker in `[tool.pytest.ini_options] markers` is selected or deselected
  by some row — a `serial` marker no row runs alone is decoration (6e23dd4,
  omi_physics d7916ad);
- every path in a `testpaths` or a posargs default is reached by some row
  (0f7fed74).

### Gate 11: the glGet table against the registry

**Class B**, and the one with the worst consequence: a recorded output size
shorter than what the driver writes is a heap overrun in every program making
the call, silent, because the bytes past the end usually belong to another live
allocation (95bf3b90, e46a5ae2, 4f39c015).

`plans/GLGET-SIZES.md` landed the live half: `tests/gl/test_glget_sizes.py`
walks the shipped table against the driver in front of it. The static half is
what reaches a pname no driver in CI implements — every recorded size compared
against what the registry's `COMPSIZE` and `len` attributes say, with a
disagreement a failure. 7529bff6 is the table and the generator disagreeing
with nothing to say so, and bc4e1326 is the driver being right and the table
wrong.

## The classes a parser cannot answer

Named so that nobody spends a week trying.

**Per-context state.** A GL object is a name in the context that issued it, and
the defects are a cache keyed by anything else: the extension list and version
cached against a handle the driver hands out again (1d25f1b7, cd4ebffa), a VBO
deleted in whichever context was current when the collector ran (a3338762),
`forget_context` freeing a table another thread was dispatching through
(ed014c03). What finds these is a fixture that makes and destroys many contexts
and reuses addresses — the suite does, twenty-two addresses over three hundred
contexts (0cc02c66, 5f9c0687) — not a parser.

**Driver behaviour and specification age.** An enum a context predates, a
uniform block with nothing bound, a validation a driver is entitled to fail:
these need a driver, and the matrix is the gate. `tests/gl/enum_age_audit.py`
is as far as reading the tree goes, and it goes there by reading the registry
rather than by reasoning about the code.

**Platform library search.** Which name a library has on which system,
`find_library` walking `PATH` on Windows, a conda `opengl32.dll` ahead of
System32 (be25e2ec, 31f1a5bd). A runner on that platform answers this; nothing
else does.

**Numeric shape.** A one-element array compared with a scalar, a numpy array
asked for its truth value, `int()` on a result whose failure mode depends on
the library version. mypy sees none of it without annotations the generated
modules cannot carry, and the axes in the matrix — `num0`, `accel0`,
`flag{errorcopy,nosizecheck}`, `dispctypes` — are what found every one of them
(f849942a, 87c67ed6, 2c242faf, 44af6c95). Extending the axes beats parsing.

## What landed

All eleven. Where each one lives:

| Gate | Where |
| --- | --- |
| 1 Every error path is entered | `tox -e errorpaths` → `src/check_error_paths.py`, `src/error-paths-unentered.txt` |
| 2 possibly-undefined | `tox -e possiblyundefined` → `src/check_possibly_undefined.py` |
| 3 The interpreter floor | `tox -e floor` → vermin |
| 4 Sibling families | `tests/gates/test_sibling_apis_agree.py` |
| 5 Parallel implementations | `tests/gates/test_parallel_implementations_agree.py` |
| 6 The customisation vocabulary | `tests/bindings/generated/test_wrapper_parameter_names.py` |
| 7 A foreign function is declared | `tests/gates/test_foreign_functions_are_declared.py` |
| 8 One story about each flag | `tests/gates/test_configuration_is_one_story.py` |
| 9 A test that cannot fail | `tests/gates/test_the_suite_can_fail.py` |
| 10 A declared gate runs | `tests/gates/test_declared_gates_run.py` |
| 11 The glGet tables agree | `tests/gates/test_glget_sizes_agree.py` |

The seven in `tests/gates/` are ordinary pytest modules, so they run on every
row of the matrix and need no driver. The three tox environments are in the
`envlist` and have a row of their own in `.github/workflows/test.yml`, which is
Gate 10's own rule applied to Gate 10.

`tests/sources.py` parses the package and the suite once for whichever gate
asks; `tests/gates/_families.py` reduces a per-API module to the shape the
grouping compares.

## What they found

Twelve defects, each fixed in the same pass, each with the gate that reports it
standing behind it.

**Wrong answers.**

- `FormatHandler.typeLookup` — a public classmethod, and how a third party asks
  which handler its own array format resolved to — raised `TypeError:
  'HandlerRegistry' object is not subscriptable` wherever PyOpenGL_accelerate
  is installed, which is most installations. The pure-Python registry is a
  dict subclass and answered; the compiled one held its mapping privately and
  offered only `__setitem__`, so the lookup's own `except KeyError` could not
  catch what it raised. The compiled registry answers `__getitem__`,
  `__contains__`, `__len__`, `__iter__`, `get`, `keys`, `values` and `items`
  now, and a type nothing handles raises the `KeyError` the method documents.
  (Gate 5)
- `tests/gles/es_coverage.py` reported `0 0 0.0%` for every ES level. It
  counted `def gl` in `OpenGL/raw/GLES*/VERSION/*.py`, and those files went
  with the declaration tables — so the scan found nothing and printed a table
  that looked as though it had run. The desktop report was corrected for this
  in e062d20f; the ES one was not. It reads the tables now: 142, 104, 68 and 44
  commands, at 99.3% and 100%. `extension_sources` also named `glob` without
  importing it, so it raised `NameError` on any call. (Gate 9)
- The harness case guarding exactly that asserted `'0 total' not in stdout`,
  which is a phrase only the GLU report writes. It reads the numbers now.
  (Gate 9)
- `numpymodule` and `numpybuffers` decided the 16-bit typecodes by asking numpy
  for a Numeric-era `'s'` array. On the branch where that *succeeds*,
  `USHORT_TYPE` is never bound and the table below raises `NameError` at
  import. The branch has not been reachable for as long as this package has
  required numpy; both say `'h'` and `'H'`. (Gate 2)
- `tests/bindings/test_accelerate_generated_c.py` imported `tomllib`, which is
  3.11, with no guard — and `py39-num1-accel0-dispctypes` is a row of the
  matrix. `tests/tomlread.py` is the one guarded reader, with `tomli` behind it
  and named in the `test` extra. (Gate 3)

**Things that said they worked and did not.**

- `PYOPENGL_WARN_ON_FORMAT_UNAVAILABLE`, `PYOPENGL_FORWARD_COMPATIBLE_ONLY`,
  `PYOPENGL_MODULE_ANNOTATIONS` and `PYOPENGL_TYPE_ANNOTATIONS` did nothing:
  four of the eighteen flags were plain assignments sitting in a list of
  fourteen `environ_key` calls, while the warning raised on a late assignment
  told the caller to set exactly those variables, "which works whatever the
  import order". All four read the environment now. (Gate 8)
- `ARRAY_SIZE_CHECKING` is what `flagnosizecheck` sets in the matrix and the
  package docstring introduced every other flag but that one. (Gate 8)
- `FormatHandler.dimensions` declared a `typeCode` parameter that no
  implementation accepts and no caller passes — so the interface a third party
  writing a handler reads described an argument every handler would have
  refused. (Gate 5)
- `OpenGL/raw/GLES3/_types.py` carried an `_error_function` nothing read, left
  from before `_errors.py` existed, and it reads as the module doing error
  checking. (Gate 4)
- `glcontext_desktop.draw_framebuffer` tolerated every GL error there is where
  its own docstring names the one it expects. (Gate 9)
- `tests/gles/es_coverage.py` and the two tox environments added here had no
  CI row, which is the same defect as the `py39` cell the matrix never
  started. (Gate 10)

**Names that may be unbound where they are read** (Gate 2): four, of which
`OpenGL/GLUT/special.py` is the file 9a8cad14 fixed for the same class, and
`OpenGL/GLU/glunurbs.py` cleaned up its loop variables under a
`try: del … except NameError`, a guard for the loop running no times — which it
cannot.

## What is left

- **`src/error-paths-unentered.txt` has 285 entries in it**, out of 333 error
  paths in the package. That is the ratchet's starting point rather than a
  result: it stops a new one arriving, and every line in it is a case somebody
  could write. `OpenGL/wrapper.py` is 88 of them.
- **The record is written from one configuration** — ctypes entry points, numpy
  present, the EGL device backend on Linux. A handler that runs on a machine
  with more of the world in front of it is reported and does not fail, because
  a red build on somebody's laptop for having a better driver is not a gate.
  What that costs is that the list shrinks only when somebody runs `--write`
  in the configuration it was written from.
- **Gate 4 records `_types.py` as outside the shape comparison.** Nine APIs,
  nine genuinely different files: it is each API's own ctypes vocabulary, and a
  shape record over it would go red on every ordinary edit. The one policy
  question it carries — the error-checker construction — is read wherever it
  is, by a rule of its own.
- **Gate 11 compares the two shipped tables against each other, not against a
  specification.** `gl.xml` carries `COMPSIZE(pname)` and not what any
  particular pname's size is: that lives in the spec text. So a size that is
  wrong in `src/glgetsizes.csv` is wrong in all three copies consistently, and
  what catches it is still `tests/gl/test_glget_sizes.py` against a driver that
  implements the pname.
