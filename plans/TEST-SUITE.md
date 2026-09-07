# The test suite: consolidation and clean-up

A review of `tests/` and `accelerate/tests/` as a piece of software in its own
right, and a plan for the work it needs. Written 2026-09-07 against
`542bbea`.

## Where the suite stands

| | |
|---|---|
| Test modules | 196 `test_*.py` — 63 at `tests/` root, 70 `gl/`, 38 `gles/`, 19 `cdispatch/`, 6 `glu/` |
| Support modules and check scripts | 66 further `.py`, 58 of them at `tests/` root |
| Lines | 30,017 in `test_*.py`; 36,628 across `tests/` |
| A full run | 47.6s on the EGL device backend — 3,082 items collected; 3,007 passed, 482 skipped, 1 xfailed, plus 1,387 subtests |
| Configuration | one `markers` entry in `pyproject.toml`; three `conftest.py` files, each editing `sys.path` |

The shared framework — `glcontext.py`, the backend mixins, the API bases, the
`gl/` `gles/` `glu/` `cdispatch/` suites — is coherent and documented, and
`tests/README.md` states the principles it is built on. The work below is
almost entirely about what sits *around* that framework: a layer of material
that predates it and was never brought in, a `tests/` root that mixes six
unrelated kinds of file, and a handful of conventions that are stated but not
enforced.

Performance is not the problem: 47.6s for the whole suite, and the largest
single cost is one PyInstaller build. The plan therefore spends its effort on
structure, and treats speed as a small section at the end.

**Two supported configurations are red**, which the tox matrix does not cover
and so has never reported: `PYOPENGL_ERROR_ON_COPY=1` aborts collection and then
fails 59 tests, and `PYOPENGL_ARRAY_SIZE_CHECKING=0` fails three. Section I has
the numbers and what to do; the first two fixes are small and go ahead of
everything else here.

---

## A. Material that nothing runs

Fourteen modules under `tests/` are reachable from nothing — no import, no
runner entry, no CI step, no documentation reference.

| File | What it is |
|---|---|
| `tests.py` | A matrix runner for python2.6–3.10 that clones pygame from Bitbucket over `hg` and installs `../OpenGL_accelerate`. Every path in it is gone. |
| `testing_context.py` | `createPyGameContext` / `createGLUTContext`, superseded by `glcontext.pick_backend()`. |
| `performance.py` | A drawing-strategy profiler. |
| `osdemo.py`, `linewidth.py`, `geomshader.py`, `glsl_version.py` | Demonstration programs. |
| `gh_bug32.py`, `gh_bug6_check.py`, `gh_bug33_osmesa_attribute_pointer.py`, `timerleak.py` | Bug reproductions from closed issues. |
| `importtests.py` | Two import statements. |
| `check_autocomplete.py`, `check_querier_version_parse.py` | Named for the check-script convention, wired into nothing, and neither prints the `OK` the harness reads. |

**Do:** delete all fourteen. Where one records a fact still worth having —
`osdemo.py` is the only OSMesa offscreen sample in the tree, and
`gh_bug33_osmesa_attribute_pointer.py` the only OSMesa attribute-pointer
case — turn it into a real check script under the convention in section C
before deleting, or move it to `examples/` where samples live.

`check_autocomplete.py` and `check_querier_version_parse.py` are the interesting
pair: they carry the `check_` prefix that means "run by `test_checks.py`", and
they are not run, because `test_checks.py` enumerates its scripts by hand. That
is section C.

---

## B. `test_core.py` and the legacy root-level GL tests

Nine modules at `tests/` root open a GL context — through `basetestcase.BaseTest`,
or `testdecorator.gltest` — and test the desktop GL API, which is what
`tests/gl/` is for. They are the oldest material in the suite and carry the
habits of the era:

`test_core.py` (728 lines, 28 tests), `test_textures.py` (13),
`test_arraydatatype.py` (16), `test_evaluators.py` (7), `test_tess.py` (4),
`test_glgetactiveuniform.py` (1), `test_glgetfloat_leak.py` (1),
plus `test_sf2946226.py` (1) and `test_vbo_memusage.py` (1).

Four properties make them worth reworking rather than moving:

**1. A guard that returns instead of skipping.** `test_core.py` holds twelve
bare `return` statements guarding on `if not glDrawBuffers:`, `if not
glGenFramebuffers:`, `if not glCreateShader:`. A test that returns early passes.
Two of them print instead — `print('No Frame Buffer Support!')`, `print('No
multi_draw_arrays support')` — into a captured stream nobody reads. The rest of
the suite skips with a reason, which is `tests/README.md` item 3 and the only
form that leaves a record.

**2. A guard that deletes the test.** Eleven class-body conditionals across
these modules (`if array:`, `if not OpenGL.ERROR_ON_COPY:`) define the test
method only when the condition holds. Under `num0` or `ERROR_ON_COPY=1` those
tests do not skip — they do not exist, and the run reports a smaller number with
nothing to say about the difference. `pytest.mark.skipif` says the same thing
and leaves the record.

One of them is broken outright — and it is the loose end of the larger problem
in section I. `tests/test_evaluators.py:19` reads

```python
if (not OpenGL.ERROR_ON_COPY) or array:
```

and `array` is not defined in that module — it imports numpy as `np`. With the
flag at its default the left side is true, `or` short-circuits, and the name is
never looked up. Set `PYOPENGL_ERROR_ON_COPY=1` and it is a `NameError` while
the class body is executing, which is a collection error, which **ends the whole
run**:

```
E   NameError: name 'array' is not defined
!!!!! Interrupted: 1 error during collection !!!!!
```

Every one of these branches should be a `skipif` naming the flag, so that the
configuration it is about is visible in the run rather than in the source.

**3. `bool(entry_point)` as an availability test.** These modules ask the
library whether a symbol resolved; `tests/README.md` explains why that is a
different question from whether the context implements the feature, and
`ContextTestCase.require_feature` is the answer. On macOS the difference is a
segfault rather than a skip.

**4. Most of it is now covered better elsewhere.** Cross-checking each entry
point against `tests/gl/`:

| `test_core.py` test | Disposition |
|---|---|
| `test_glget` | **Delete.** Superseded by `gl/test_glget_extensions.py`, which is data-driven from `gl/glget_groups.json` and per-feature. `glget_check.py` already carries this test's crash-guard ranges, with a comment saying where they came from. |
| `test_errors` | **Delete.** `gl/test_review_fixes.py::TestGLErrorAttributes` asserts the same `err`/`baseOperation`/`pyArgs`/`cArgs` contract, against a stated rule. |
| `test_simple`, `test_nonFloatColor` | Fold into `gl/test_gl1_immediate.py`. |
| `test_arbwindowpos` | Fold into `gl/test_ext_aliases.py`, which covers window-pos already. |
| `test_gl_1_2_support`, `test_compressed_data` | Fold into `gl/test_gl12_13.py`. |
| `test_glmultidraw` | Fold into `gl/test_gl14.py`. |
| `test_glCallLists_twice2` | Move to `gl/test_gl1_lists.py`. Its comment ("other tests share this context") is untrue — `ContextTestCase` gives every test its own — and should go with it. |
| `test_fbo`, `test_gen_framebuffers_twice`, `test_glDrawBuffers_list*` | Fold into `gl/test_gl30.py` / `gl/test_ext_fbo_mem_ati.py`. |
| `test_glgetbufferparameter`, `test_glbufferparameter_create`, `test_glgetbuffersubdata_output_array`, `test_scalars_mapped_to_arrays` | Move to `gl/test_gl15.py` (buffer objects) or a new `gl/test_buffer_getters.py`. The `SIZE_1_ARRAY_UNPACK` branches in them are the only coverage of that flag; keep them and name them. |
| `test_shader_compile_string` | Fold into `gl/test_gl20.py`. |
| `test_max_compute_work_group_invocations` | **Delete.** `gl/test_glget_compute.py` covers it. |
| `test_get_version`, `test_lookupint`, `test_get_read_fb_binding` | Move to `gl/`; these are about the querier and the lookup, and want a named home — `gl/test_version_queries.py`. |
| `test_constantPickle` | Not a GL test at all. Move to the bindings group (section D) — it needs no context. |
| `test_arrayTranspose`, `test_mmap_data`, `test_vbo` | Array-handling, not GL feature coverage. Move to the arrays group (section D). `test_mmap_data` writes `mmap-test-data.dat` into the **current working directory** — hence the entry for it in `.gitignore` — and must take `tmp_path`. |

`test_arraydatatype.py` splits along a line already in it: `test_pointers`,
`test_texture`, `test_numpyConversion`, `test_glbuffersubdata_numeric` and
`test_copyNonContiguous` drive fixed-function GL and belong in `gl/`; the other
eleven — bytes, bytearray, the buffer protocol, memoryview, `void_dp`, string
parameters, subclassing, byte counts — need no context and belong in the arrays
group (section D). It takes a 300×300 compatibility context for all sixteen
today.

The other modules move whole: `test_textures.py` → `gl/`,
`test_evaluators.py` and `test_tess.py` → `glu/` (they test NURBS, quadrics,
tessellation and GLE), `test_glgetactiveuniform.py` → `gl/`,
`test_glgetfloat_leak.py` and `test_vbo_memusage.py` → `gl/` (both need a
context), carrying the resource-budget marker of section F, and
`test_sf2946226.py` → `gl/test_ext_fbo_mem_ati.py`.

When they are all out, `basetestcase.py` has no callers and goes with them; the
suite is left with one fixture spelling, `glcontext.pick_backend()` plus an API
base, which is what `tests/README.md` already describes.

**A note on what not to lose.** Several of these tests are the *only* coverage
of a configuration flag — `ERROR_ON_COPY`, `ARRAY_SIZE_CHECKING`,
`SIZE_1_ARRAY_UNPACK`, `UNSIGNED_BYTE_IMAGES_AS_STRING`. Moving them is the
chance to make that explicit: name the case for the flag it is about, and
`skipif` on the flag rather than branching inside the body.

---

## C. Files named `test_*` that hold no tests, and files that run twice

`tests/test_checks.py` runs stand-alone scripts as subprocesses and derives each
script's filename from the test function's name minus `test_`. Five of its
entries therefore name files that also start with `test_`:

```
test_test_sf2946226      -> test_sf2946226.py
test_test_glgetactiveuniform -> test_glgetactiveuniform.py
test_test_glgetfloat_leak    -> test_glgetfloat_leak.py
test_test_gldouble_ctypes    -> test_gldouble_ctypes.py
test_test_instanced_draw_detect -> test_instanced_draw_detect.py
```

Two consequences:

- **Three modules run twice.** `test_sf2946226.py`, `test_glgetactiveuniform.py`
  and `test_glgetfloat_leak.py` are collected in-process *and* launched as
  children, testing the same thing in the same configuration.
- **Four `test_*.py` files hold no tests at all.** `test_fbdel.py`,
  `test_gldouble_ctypes.py`, `test_glx_raw_x.py` and
  `test_instanced_draw_detect.py` are interactive GLUT programs with a
  `__main__` block. pytest imports all four during collection — which loads
  GLUT and, for `test_glx_raw_x.py`, `libX11` and a module-level `pytest.skip` —
  and reports a skip that reads as a covered case.

**Do:**

1. Rename the four programs `check_*.py` and let `test_checks.py` run them, or
   delete them: `test_fbdel.py` is a 2009 FBO delete-loop against a driver bug,
   and `test_instanced_draw_detect.py` prints `bool()` of four entry points.
   Before deleting the latter, note what goes with it:
   **`OpenGL.extensions.alternate` has no test.** It is a public API, and the
   only two places in the suite that touch it are
   `test_instanced_draw_detect.py` and the module-level
   `glMultiDrawElements = alternate(...)` in `test_core.py` /
   `basetestcase.py` — both of which this plan removes. Write a real case for
   it in `bindings/dispatch/` first: which of several candidates it picks, what
   it does when none resolve, and that the result reports the name a caller
   would expect.
2. Drop the `__main__`/`checkutils.run()` tails from the three that are real
   tests, and delete their `test_test_*` entries from `test_checks.py`.
3. **Discover check scripts rather than listing them.** Replace the 27
   hand-written stub functions with a `glob('check_*.py')` and a
   `pytest.mark.parametrize`, with the platform requirement declared *in the
   script* (a `# requires: glut, window-server` header, or a `checkutils`
   call the runner reads) rather than as a decorator in the runner. This is
   what makes `check_autocomplete.py` and `check_querier_version_parse.py`
   impossible: a script in the directory is either run or explicitly excluded.
4. While there: `numpy_only` in `test_checks.py` skips with the reason
   `'No GLUT installed'`, and both `xlib_only` and `numpy_only` name their
   inner function `glut_only_test`.
5. `test_check_egl_pygame` is `@pytest.mark.xfail` with no reason and no
   `strict`. A known failure carried forward is the thing the project's own
   guidance rules out. Fix it, or record why it cannot pass here and make it a
   skip with that reason.

---

## D. The shape of `tests/`

`tests/` root holds 121 `.py` files of six unrelated kinds: the fixture
framework, tests *of* the fixture framework, tests of library internals that
need no GL, context-backed GL tests (section B), stand-alone check scripts, and
the dead material of section A. Which kind a file is can only be learned by
opening it.

Proposed layout — the sub-suites are unchanged; the root is sorted:

```
tests/
├── conftest.py, README.md
├── <the framework>          glcontext*.py, backends.py, arraycompat.py,
│                            checkutils.py, childenv.py, testdecorator.py,
│                            glget_check.py, coverage.py
├── harness/                 tests OF the framework
├── bindings/                library internals, no GL context
├── checks/                  check_*.py and the runner that discovers them
├── gl/  gles/  glu/         context-backed API suites
├── cdispatch/               the generator
└── data/
```

**`harness/`** — nine modules that test the test framework rather than
PyOpenGL: `test_backend_names.py`, `test_glcontext_helpers.py`,
`test_glcontext_egl.py`, `test_glcontext_cgl.py`, `test_shared_context_setup.py`,
`test_context_version.py`, `test_check_script_skips.py`, `test_suite_imports.py`,
`test_collects_without_egl.py`, and from the sub-suites
`gl/test_context_fixture.py`, `gl/test_standalone_context.py`,
`gl/test_colour_buffer_name.py`. Grouping them says what they are and makes
"the harness is sound" a thing a developer can run in one command.

**`bindings/`** — the ~35 remaining root modules, which are about the library's
own structure rather than about what a context can draw. Most need no GL at all;
the handful that do (`test_attribute_surface.py`, `test_cgl.py`) reach it in a
child process. They already cluster; the clusters should be directories:

| Cluster | Modules |
|---|---|
| `bindings/dispatch/` | `test_dispatch_api.py`, `test_dispatch_selection.py`, `test_attribute_surface.py`, `test_attribute_surface_api.py`, `test_getextensionprocedure_routing.py`, `test_undefined_function_guard.py`, `test_friendly_wrappers.py`, `test_extension_aliases.py` |
| `bindings/generated/` | `test_virtual_modules.py`, `test_raw_module_protocol.py`, `test_core_declarations.py`, `test_declaration_types.py`, `test_module_stubs.py`, `test_packaged_loaders.py`, `test_plugins.py`, `test_glget_consistency.py` |
| `bindings/arrays/` | `test_intptr_arrays.py`, `test_numpy_scalar_handlers.py`, `test_vbo_deleter.py`, the context-free half of `test_arraydatatype.py`, and the array-handling tests lifted out of `test_core.py` |
| `bindings/platform/` | `test_platform_libraries.py`, `test_darwin_platform.py`, `test_cgl.py`, `test_lazy_property.py`, `test_optional_module_imports.py`, `test_import_cost.py` |
| `bindings/egl/` | `test_egl_bindings.py`, `test_egl_devices.py`, `test_egl_error_checking.py`, `test_egl_missing_library.py` |
| `bindings/wgl/` | `test_wgl.py`, `test_wgl_bindings.py` |
| `bindings/glx/` | `test_glx_extension_query.py` |
| `bindings/tk/` | `test_tk_widget.py`, `test_tk_attributes.py` |
| `bindings/glut/` | `test_glut_destroy_window.py`, `test_glut_window_title.py` |
| `bindings/errors/` | `test_context_checking.py`, `test_debug_output_scope.py`, `test_debug_output_unnamed_context.py` |
| not `bindings/` at all | `test_dumbmarkup.py` tests `directdocs.dumbmarkup`, the documentation-build tool, not the library. Give it `tests/directdocs/`. |

This also lets CI's macOS job name what it runs (`tests/bindings tests/harness`)
rather than four `--ignore=` flags.

**Two pairs to unify while moving:**

- `test_dispatch_api.py` and `test_dispatch_selection.py` both spawn children
  that report which implementation is installed, and both carry a stub class
  standing in for a build with no extension — the second one's comment says
  "Mirrors tests/test_dispatch_selection". One module with one stub.
- `test_attribute_surface.py` and `test_attribute_surface_api.py` are the two
  halves of one question (does an entry point know which API it belongs to, and
  do both implementations expose the same attributes).

**One split to consider keeping split:** the debug-output work sits in five
places — two at root, three in `gl/`. The `gl/` three need a context and the
root two do not, so the boundary is real; they should be cross-referenced in
their docstrings rather than merged.

**Import mode.** With the directories above, `test_ext_state.py` would exist in
both `gl/` and `gles/` — which pytest's default *prepend* import mode forbids,
and which is why the ES copies carry the `test_es_` prefix today. `pytest 9`
with `importmode = "importlib"` lifts the restriction. Combined with
`pythonpath = ["tests", "src"]` in `pyproject.toml`, all three `conftest.py`
`sys.path` blocks disappear too. Do this first, as its own change, and confirm
the run is identical before anything moves.

---

## E. Duplicated machinery

**Two files are near-copies.**
`gl/test_ext_nv_path_rendering.py` and `gles/test_es_nv_path_rendering.py` are
99.2% identical: the same test methods in the same order, differing in the
imported module, the base class, and formatting the copy lost (three
semicolon-joined statement pairs). `gl/test_glget_extensions.py` and
`gles/test_es_glget_extensions.py` are 89.5% identical. Both pairs should be an
API-agnostic mixin plus two thin subclasses, which is the pattern
`glget_check.GLGetCheckMixin` already establishes.

Two individual test bodies are byte-identical across suites:
`test_nonsquare_matrices` (`gl/test_gl21.py`, `gles/test_es3_ubo.py`) and
`test_nv_memory_object_sparse` (`gl/test_ext_nv_advanced.py`,
`gles/test_es_nv_shader.py`). The same treatment, or a note in each saying it is
deliberately run under both APIs.

**Three coverage scripts, one job.** `gl/gl_coverage.py` (187 lines),
`gles/es_coverage.py` (129), `glu/glu_coverage.py` (61) count entry points
against the tests that call them. They have diverged: `gl` has `--ext`,
`--ext-uncovered` and `--driver`; `gles` has `--md`; `glu` has no options. Their
file scans differ too — `test_*.py`, `test_es*.py` + `test_ext*.py`, and
`test_glu_*.py` respectively, so `gles/test_array_int64.py` is invisible to the
ES report and a new file with an unexpected name is silently uncounted anywhere.
Make one `coverage.py` parameterised by API, keep the union of the options, scan
`test_*.py` everywhere, and give it a test — nothing currently runs these, so
they can rot without anyone finding out. `es_coverage.py` has: its docstring
says it scans `check_es*.py` and writes `ES_COVERAGE.md`, and neither exists.

**Child-process plumbing.** Twenty-five modules spawn subprocesses across 35
call sites; most carry a triple-quoted source blob and hand-rolled
`subprocess.run` + JSON parsing. `childenv.child_environment()` is the only
shared part. A
`run_in_child(source, **environment) -> parsed JSON` helper beside it, asserting
the return code and surfacing the child's stderr on failure, removes the
repetition and gives one place to add a timeout and a `NOTHING_TO_TEST_WITH`
skip.

**Shader source stays where it is.** 146 `#version` directives across 61
modules. The declaration is the first thing a reader of a shader needs and the
first thing they change, so it belongs in the shader text and not behind a
helper that composes it. What is worth fixing is the inconsistency: `#version
150` and `#version 150 core`, `#version 420` and `#version 420 core`, `#version
450` and `#version 450 core` all appear for the same profile. Write the profile
every time, so a reader never has to remember which versions default to which.

**`accelerate/tests/` is a parallel contract.** `test_arraydatatypeaccel.py`'s
`_BaseTest` mixin — `from_param`, `dataPointer`, `arraySize`, `arrayByteCount`,
`asArray`, `unitSize`, `dimensions`, `arrayToGLType` — is the `ArrayDatatype`
contract, and it is only ever run when the compiled extension is installed. The
pure-Python handler implements the same contract and is never checked against
it. Move the mixin into `tests/bindings/arrays/` and parametrise it over the
handlers present, so `accel0` runs it too; leave in `accelerate/tests/` only
what is genuinely about the extension.

---

## F. Configuration

`[tool.pytest.ini_options]` holds one key. Everything else that shapes a run is
spelled out on command lines in `tox.ini` and `.github/workflows/test.yml`, or
not at all.

**Do:**

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "accelerate/tests"]
pythonpath = ["tests", "src"]
importmode = "importlib"
xfail_strict = true
filterwarnings = ["error", ...]     # with the known ones listed
markers = [
    "performance: ...",
    "slow: ...",
]
```

- `xfail_strict` — with one `xfail` in the tree and no reason on it, an xpass
  currently passes silently.
- `filterwarnings = ["error"]` — the run emits five warnings today, including a
  `PytestRemovedIn10Warning` for a class-scoped fixture defined as an instance
  method in `cdispatch/`, which is a deprecation with a deadline. There is also
  a `PytestCollectionWarning` for numpy's `_pytesttester.test`, reached through
  `from numpy import *` in `basetestcase.py` and `test_core.py`; that star
  import goes with section B.
- **The `performance` marker is declared, documented in `tests/README.md`, and
  deselected in four CI steps — and no test carries it.** Either mark the
  resource-budget tests (`test_glgetfloat_leak.py`, `test_vbo_memusage.py`,
  `test_import_cost.py`) — noting they measure memory, not speed, so a second
  marker may be the honest answer — or remove the machinery. A deselection that
  deselects nothing is a claim the configuration makes and does not keep.

**Axes for the configuration flags**, once section I has established which
configurations pass. Crossing five flags with six interpreters would multiply
the matrix by 32; the flags are not interpreter-sensitive, so pin them to the
newest Python and vary only what they interact with:

```
py<newest>-num{0,1}-accel{0,1}-disp{ctypes,c}-flag{errorcopy,sizecheck,...}
```

— one interpreter, crossed with numpy/no-numpy and accelerate/no-accelerate,
because an array flag is exactly a claim about those two. The interpreter sweep
stays on the ordinary configuration, where it is a claim about the interpreter.

**Two definitions of the test environment.** `test-requirements.txt` and
`[project.optional-dependencies] test` list the same packages, and already
disagree: pyproject pins `pygame < 2.1.3` for Python < 3.11, `test-requirements`
has that line commented out and adds `--only-binary`. `tox.ini` reads the file;
everything else reads pyproject. Make `test-requirements.txt` a one-line
`-e .[test]`, or delete it and point `tox.ini` at the extra.

**A basename-uniqueness guard.** `tests/README.md` states the rule that every
`test_*.py` basename is unique tree-wide, and nothing enforces it — a collision
is a confusing collection error at some future point. Under `importmode =
"importlib"` the rule can be dropped; until then it should be a test.

**A timeout.** `pytest-timeout` is installed in the development environment,
absent from `test-requirements.txt`, and configured nowhere. `test_checks.py`
bounds its own children at 120s; nothing bounds an in-process hang, and CI's
only backstop is the 30-minute job limit, which reports a cancelled job rather
than a test name. Add `pytest-timeout` to the requirements and a generous
per-test `timeout` to the ini.

---

## G. Passing without proving anything

`ContextTestCase.exercise()` skips on an unresolved entry point and swallows
**any** `GLError`. It is used at 98 sites, against 19 uses of the narrower
`tolerate_glerror(*codes)`. `tests/README.md` describes both as narrowly
tolerating "a *documented*, expected GLError (a known driver gap)" — which
`tolerate_glerror` enforces, by taking the codes, and `exercise()` cannot. A
case wrapped in `exercise()` passes even if every call in it errors, and the
report says nothing.

**Do:** give `exercise()` a required reason argument and, where the error is
predictable, the codes — making it `tolerate_glerror` with a note. Where a case
genuinely only wants to prove an entry point is reachable, name that: a
`smoke()` context manager that records what it tolerated, so the coverage report
can distinguish "called and did the thing" from "called and was forgiven". The
suite's stated bar is the former (`tests/README.md`, principle 1); 98 sites are
currently below it and the count is not visible anywhere.

This is the largest single quality item in the plan and the one most likely to
turn up real defects — a swallowed `GL_INVALID_OPERATION` on a driver that
supports the extension is exactly the wrapper bug the suite exists to find. It
should be done extension by extension, not in one sweep.

---

## H. Speed

47.6s for the whole suite locally; nothing here is urgent. Ranked by what a
change would actually buy:

1. **CI wall-clock, not local.** Six Linux tox axes and four macOS jobs each run
   the suite serially. `pytest-xdist` with `-n auto` has four cores to use on a
   GitHub runner. The caveats need testing before adopting: workers contend for
   the EGL device, and the intermittent NVIDIA teardown SIGSEGV documented in
   `tests/README.md` would take a worker's whole batch with it. Try it on one
   Linux axis first, with `--dist loadfile` so a module's contexts stay in one
   process, and compare the pass/skip counts against a serial run before
   trusting it.
2. `tests/test_packaged_loaders.py` spends 7.5s (16% of the run) in a
   PyInstaller build for `TestFreezingAnApplication`'s two cases. The fixture is
   already module-scoped, so there is nothing to reuse; mark the class `slow` so
   a developer can deselect it, and leave CI running it.
3. `gl/test_glget_sizes.py` (1.13s) and `test_collects_without_egl.py` (2.7s
   across two tests, each collecting the suite in a child) are the next two.
   Both are doing real work for their time.

What is *not* worth doing: sharing contexts between tests. A context per test is
deliberate — the dispatch table is keyed by a context handle the driver reuses,
which `glcontext.forget_context` exists to handle — and context creation is not
where the time goes.

---

## I. The configuration flags nothing runs

`OpenGL/__init__.py` documents a set of flags a caller may set before importing
the library, each settable from the environment. The tox matrix varies
interpreter, numpy, accelerate and dispatch, and none of these. Running the
suite under each of them, on the EGL device backend, says what that has cost:

| Configuration | Result |
|---|---|
| default | 3,007 passed, 482 skipped |
| `PYOPENGL_SIZE_1_ARRAY_UNPACK=0` | 3,007 passed, 482 skipped |
| `PYOPENGL_ALLOW_NUMPY_SCALARS`, `PYOPENGL_STORE_POINTERS` | collect clean; not run further |
| `PYOPENGL_ARRAY_SIZE_CHECKING=0` | **3 failed** |
| `PYOPENGL_ERROR_ON_COPY=1` | **collection aborts**; ignoring `test_evaluators.py`, **59 failed** across 38 modules |

The two failing configurations fail for different reasons, and the difference
decides what to do about each.

**`ARRAY_SIZE_CHECKING=0` — three tests, and they are the tests' fault.**
`gl/test_array_acceptance.py::test_too_long_is_refused`,
`::test_too_short_is_refused_rather_than_read_past` and
`gl/test_buffer_lifetime.py::test_a_failing_size_check_releases_its_buffer`
assert the refusal that the flag switches off. They are the right tests; they
need `skipif` on the flag, or better, they should set it for themselves. Cheap
to fix, and worth doing at once.

**`ERROR_ON_COPY=1` — 59 tests, and the question is open.** Forty-five raise
`OpenGL.error.CopyError: list passed, cannot copy with ERROR_ON_COPY set` from
`OpenGL/arrays/lists.py:32`; the rest are three `AssertionError`, two
`AttributeError` and a `RuntimeError`, which need reading individually. They are
spread right across the tree — five in `test_intptr_arrays.py`, four in
`gl/test_review_fixes.py`, and singles through `gl/`, `gles/` and `glu/`. The
flag exists so that a program can refuse the silent copy PyOpenGL otherwise
makes for a Python list, so a test that passes a list is asking for exactly what
the flag forbids.

**The lists are not the mistake.** Passing a list is how the list handler gets
exercised, and PyOpenGL copying it is the documented default behaviour — a
suite that converted all 59 to arrays would stop testing the path most callers
take. What the flag says is that *this run* refuses the copy, so a test that
uses a list incidentally should ask the flag and build an array where it is set,
and a test that is *about* the flag should pass a list on purpose and assert the
raise.

**Do:** a helper in `arraycompat.py` —

```python
def copy_safe(data, dtype):
    """``data`` as a list, or as an array where the run refuses copies."""
    return np.array(data, dtype) if ERROR_ON_COPY else data
```

— applied at the 45 `CopyError` sites where the list is incidental, which leaves
the default configuration passing lists exactly as it does now. The other six
failures (three `AssertionError`, two `AttributeError`, a `RuntimeError`) are
not the same thing and want reading one at a time.

Then the coverage that is missing either way: **`ERROR_ON_COPY` has no test of
its own.** The flag is read at import of `OpenGL/arrays/lists.py`, where the
`err_on_copy` decorator is applied once per process, so a case for it runs in a
child — which section E's `run_in_child` provides. It should assert that a list
raises `CopyError` under the flag, that the same call succeeds without it, and
that an array is accepted under both.

Add whichever configurations end up green as a tox axis, so they stay that way.

`tests/tests.py` — the dead runner of section A — swept eight of these flags in
a loop. It is the wrong mechanism now, but its `FLAGS` list is the right list;
copy it out before deleting the file.

---

## J. Documentation

`tests/README.md` is good and mostly current. What it needs with this work:

- **`cdispatch/` and `data/` are missing from the directory map** — 19 modules
  and 355 tests, the second-largest sub-suite, undescribed.
- The map's `basetestcase*.py` / `testdecorator*.py` globs are left over from
  when there were `_glfw` and `_pygame` variants; there is one of each.
- The `conftest.py` line does not mention the `PYOPENGL_DISPATCH=c` strictness
  check, which is the thing most likely to stop somebody's run.
- `TEST_CHECK_TIMEOUT` is not documented with the other `TEST_*` variables.
- The legacy-suite entries go when section B lands; the new directories arrive.
- `childenv.py`'s docstring cites `tests/test_glx_raw_x.py` as the example of a
  test that refuses to run off Linux — that file contains no tests.

Outside the suite, four pages cite test paths and will need the new ones:
`documentation/c-dispatch.html` (`test_attribute_surface.py`,
`test_virtual_modules.py`), `documentation/wrapping.html` (`tests/cdispatch/`),
`documentation/cgl-offscreen.html` (`check_cgl_context.py`),
`documentation/egl-devices.html` (`glcontext_egl.py`). `plans/` references stay
as they are: they record what was decided when it was decided.

---

## Sequence

Each step leaves the suite green and is worth landing on its own.

0. **The unambiguous red first** (I): the `test_evaluators.py:19` `NameError`
   that ends the run under `ERROR_ON_COPY=1`, and the three
   `ARRAY_SIZE_CHECKING=0` cases that assert the check the flag switches off.
   Neither waits for the reorganisation.

1. **Configuration next** (F): `pythonpath`, `importmode`, `testpaths`,
   `xfail_strict`, `filterwarnings`, the requirements de-duplication. Confirm
   the collected count and the pass/skip split are unchanged.
2. **Delete the dead** (A). Nothing imports any of it; the run should not move.
3. **The check-script runner** (C): discovery instead of enumeration, the four
   no-test programs renamed or deleted, the double-run entries dropped, the
   `xfail` resolved.
4. **`test_core.py` and the legacy GL modules** (B), one module at a time,
   deleting what is superseded and moving the rest into `gl/` and `glu/` with
   real skips. Ends with `basetestcase.py` deleted.
5. **The directory move** (D), mechanical once 1–4 are done, plus the two module
   unifications.
6. **Shared machinery** (E): the two near-duplicate files, one coverage script,
   `run_in_child`, `glsl.py`, the array-contract mixin.
7. **The `ERROR_ON_COPY` 59** (I), in one pass, with the calls that cannot be
   converted written down — that list is the reason to do it.
8. **`exercise()`** (G), extension by extension, over as long as it takes.
9. **`pytest-xdist` on one Linux CI axis** (H), if it proves stable, and the
   configuration axes from step 7.

Documentation (J) is not a step: each of 0–9 updates `tests/README.md` as part
of itself.

## Verification

Every step is checked the same way, since the suite is its own oracle:

- `TEST_WINDOWING=egl python -m pytest tests/ -q` — the counts of passed,
  skipped and xfailed compared against the run before the change. A step that
  moves files should not move any count; a step that turns a silent return into
  a skip should move exactly the skips it claims.
- `python -m pytest tests/ --collect-only -q | tail -1` before and after, for
  the steps that change import mode or move files.
- `PYOPENGL_ERROR_ON_COPY=1` and `PYOPENGL_ARRAY_SIZE_CHECKING=0` against the
  baselines in section I, for step 0 and step 7.
- The macOS and no-numpy axes are where the conditional-definition changes in
  section B will show: `tox -e py312-num0-accel0-dispctypes` locally, and the
  `macos` job in CI.
- `python gl/gl_coverage.py --ext` before and after section E's coverage merge,
  to show the numbers are the same ones.


---

## What landed

Steps 0–7 and 9, in eleven commits on `develop`. Step 8 is not started; the
notes below say what else is left.

| | before | after |
|---|---|---|
| Test modules at `tests/` root | 63 | 0 — the root holds the framework |
| Modules nothing runs | 14 | 0 |
| Files named `test_*` holding no tests | 4 | 0 |
| Modules run twice | 3 | 0 |
| `conftest.py` editing `sys.path` | 3 | 0 |
| Warnings in a run | 5 | 0 |
| Default run | 3,007 passed / 482 skipped | 3,113 / 485 |
| `PYOPENGL_ERROR_ON_COPY=1` | collection aborts, then 59 failed | 3,096 passed / 502 skipped |
| `PYOPENGL_ARRAY_SIZE_CHECKING=0` | 3 failed | green |
| `PYOPENGL_STORE_POINTERS=0` | 1 failed | green |
| `PYOPENGL_USE_ACCELERATE=0` | **segfault**, 69 failed | 6 failed, no crash |

### Defects found, in the library

- **An output array was never measured against the count the call would write.**
  `glGenTextures(64, numpy.zeros(4, 'I'))` wrote 256 bytes into 16 — a heap
  overrun with no exception, on the pure-ctypes path, which is what a
  `pip install PyOpenGL` without a compiler runs. The C layer had the check;
  nothing else did. Fixed in `converters.Output.checkOutputSize`.
- **Six entry points were being handed the wrong element type** and getting a
  silent conversion: `GL_TYPE` as signed where the call takes `GLenum`, the
  multi-draw counts as unsigned where `GLsizei` is signed, the GLU sampling
  matrices as doubles where the call takes floats, and the GLE geometry as one
  type where GLE asks for `gleDouble` paths and `float` colours.
- **`ALLOW_NUMPY_SCALARS` bought nothing but a silent float→int truncation**;
  integer scalars are converted by ctypes itself. Dropped for 4.0.
- **`check_egl_pygame.py` asked `eglChooseConfig` for `EGL_CONFORMANT=
  EGL_OPENGL_API`**, an `eglBindAPI` enum and no combination of the
  conformance bits, so the call was `EGL_BAD_ATTRIBUTE`. An `xfail` had been
  covering it.
- **`check_glx_raw_x.py` passed `DISPLAY` to `XOpenDisplay` with no argtypes**,
  so ctypes handed a `char *` parameter a `wchar_t *` and every display looked
  closed.
- Eight leaked file handles, in `src/xmlreg.py`, `accelerate/setup.py` and six
  test modules.

### Defects found, in the suite

- A test cleared `support._swallowed` — the process's record of customisations
  the C layer performed — and its `finally` cleared it again rather than
  restoring it, so anything collected afterwards got the raw binding. It
  surfaced in a different suite, about a different call.
- Six modules asked `dispatch.AVAILABLE` (is the extension importable) where
  they meant `dispatch.settle()` (is it what is running), so under
  `USE_ACCELERATE=0` they ran against the implementation they were the control
  for.
- `accelerate/tests/test_numpyaccel.py` had two methods named
  `test_asArrayConvert`; the first had never run.
- `test_arraydatatype.py::test_texture`'s body was inside an `else:` after
  importing `OpenGLContext` and PIL, so it had never executed.
- `TEST_NO_ACCELERATE` only works if it beats the first import of
  `acceleratesupport`, so the one case that used it had never run.
- `test_passBackResults` claimed to test `ALLOW_NUMPY_SCALARS` and bound a
  texture.

### Decided against

**`pytest-xdist`.** Measured: 66.8s to 36.2s with four workers and
`--dist loadfile` — 1.85x rather than 4x, because the GL device serialises most
of it. But fourteen ES cases *skip* under it that run serially, all of them
`entry point ... did not resolve in this process`: an ES-only EXT command whose
name collides with a desktop-GL one takes a cached null when the desktop module
is imported first, and which files a worker gets decides the order. So the
faster run quietly tests less, which is the trade this suite exists to refuse.

Worth revisiting only after that collision is fixed in the library rather than
worked around by `require_entrypoint` — which is its own piece of work, and a
better one.

### Left to do

- **Step 8, `exercise()`.** Untouched. Still 98 sites swallowing any `GLError`
  against 19 uses of the narrower `tolerate_glerror(*codes)`.
- **The two near-duplicate files**, `gl/test_ext_nv_path_rendering.py` and its
  ES copy (99.2% identical), and the `glget_extensions` pair (89.5%).
- **The `accelerate/tests` array contract**, still run only where the extension
  is installed.
- **Six failures under `PYOPENGL_USE_ACCELERATE=0`** with accelerate installed:
  differences between the compiled and ctypes paths in NV path rendering, the
  legacy ARB shader and program extensions, and one check script. Not a
  configuration the matrix defines — `accel0` means accelerate is *not
  installed* — so it is a separate investigation rather than a red axis.
- **`SIZE_1_ARRAY_UNPACK` cannot be set from the environment**, alone among the
  flags documented beside it in `OpenGL/__init__.py`. Setting
  `OpenGL.SIZE_1_ARRAY_UNPACK` in code before the first import works; the
  `PYOPENGL_` variable does nothing. Either it should be an `environ_key` like
  its neighbours or the documentation should say it is not one.


---

## A second pass

Seven follow-ups, all landed.

| | before | after |
|---|---|---|
| `PYOPENGL_SIZE_1_ARRAY_UNPACK=0` | not settable at all; 312 failed once it was | 3,139 passed / 485 skipped |
| `PYOPENGL_DISPATCH=c` | — | 3,140 / 484 |
| `exercise()` sites with a stated reason | 0 of 98 | 98 of 98 |
| Errors `exercise()` may swallow | any | three, and counted |
| `nv_path_rendering` | two files, 99.2% identical | 243 shared, two of 25 |

### The name collision, and what it really was

Not a name collision at all. A context's extension list is cached against its
handle; a handle is an address the driver hands out again; and `forget_context`
retired the dispatch table without dropping that cache. So the next context on
the address read the dead one's extension list, and every entry point gated on
an extension only the new context has was refused —
`bool(glTexParameterIivEXT)` answering False under an ES context that exports
it. That is why fourteen ES cases ran or skipped depending on collection order,
and why `pytest-xdist` looked faster while testing less.

`forget_context` now drops what *describes* a context and nothing else. Not
`contextdata.cleanupContext`, which also releases the client array pointers the
driver may still be reading — its own docstring warns that doing so is a
protection fault, and doing it here segfaulted the run.

`require_entrypoint` in `glcontext.py` exists to paper over this and can
probably go; it is left in place because nothing now needs it and removing it
is a separate change.

### Also found

- **The output-array guard was missing from a third path.** It is in the C
  dispatch layer, and (from the first pass) in the pure-Python converters — but
  `OpenGL_accelerate`'s Cython `SizedOutputOrInput` had neither, and that is
  what runs with accelerate installed and `PYOPENGL_DISPATCH=ctypes`. The new
  overrun test aborted there.
- **`SIZE_1_ARRAY_UNPACK`'s off-mode was broken library-wide.** Twenty-three
  places read a size-1 query for themselves with `int()`, which numpy refuses
  for an array that is not zero-dimensional. `OpenGL/_scalar.py` holds the one
  answer now. One of those was a defect in the *default* configuration too:
  `_as_address` could not read a pointer that arrived in a one-element array,
  so `use_debug_output` reported no application callback installed and PyOpenGL
  would have taken over one that was not its to take.
- **`run_in_child` defaults to asserting exit zero**, which is wrong for the
  four modules that read exit 77 as "nothing here to test with" — they reported
  a skip as a failure. Introduced by the first pass's conversion; fixed.

### Still open

- **`PYOPENGL_DISPATCH=ctypes` with accelerate installed: 6 failures**, in the
  legacy ARB shader and program extensions and NV path rendering. They fail at
  the commit this work started from, so they are a difference between the
  compiled and ctypes paths rather than anything here. CI runs `dispctypes`
  only with `accel0`, which is why nothing had reported them. Worth a session
  of its own.
- **`pytest-xdist`** — now that the caches follow their context, the reason it
  tested less is gone. It is still not adopted: that would want measuring
  again, against these counts.
- The `accelerate/tests` array contract, still run only where the extension is
  installed.
