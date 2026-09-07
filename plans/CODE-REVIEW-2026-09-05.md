# Code review: `307c9f7b..HEAD` — 4.0.0a2 to 4.0.0a4

2026-09-05. 116 commits (`git log 307c9f7b..HEAD`), two of them merges, all
since the 4.0.0a2 version bump and none previously reviewed. This covers both
windows around the 2026-09-03 review (`474c1a8..805f0917`): the 24 pre-review
commits (`307c9f7b..474c1a8`) and the 92 since (`474c1a8..HEAD`,
`4.0.0a1-120-g777ca6b7`, 2 commits ahead of `origin/develop`). The 2026-09-03
review's 17 findings are not restated; they were verified fixed in
`474c1a8..HEAD`.

Reviewed on commit state `777ca6b7` with an otherwise clean tree, in the
`.venv` at `/workspaces/OpenGL-dev/.venv` (PyOpenGL 4.0.0a4 + accelerate
4.0.0a4, editable; glfw 2.10.2, pygame-ce, numpy 2.5.2). Rendering on Mesa
llvmpipe through the headless EGL-device backend, matching the CI
configuration next to a GLFW windowed run.

## What this window is

The change of the release is the **C dispatch layer**: entry points generated
from the Khronos registries become `GLProc` heap objects in
`accelerate/src/c/pygl_runtime.c`, one per calculation, executing directly in
the process instead of a ctypes call per argument. Around it sits the machinery
that makes that safe: generated C tables for signatures, array classes and glGet
sizes; a version pin that refuses to run a PyOpenGL/accelerate pair built
against different registries; a finder serving table-backed virtual modules in
place of the 1,298 generated files; and the annotation table in
`OpenGL/_declarations.py` that the Python side and the compiled layer read from
the same source.

The window pays real test debt at the same time. The four per-backend test
fixtures became one (`777ca6b7`, 2596 pass under the EGL device platform where
2514 did), macOS gained a headless CGL backend and binding, the suite runs on
CPython 3.10-3.14, and the `_configflags`/`USE_ACCELERATE` and
`PYOPENGL_DISPATCH` machinery that decides which layer runs is now read late
and documented. None of the draft findings from the investigation phase
survived as defects; all three were refuted or reduced to the minor notes
below, and each is recorded as checked and cleared in its finding's place.

## Findings

### Medium

**1. macOS never builds or selects the C dispatch layer.** The macOS CI job
(`.github/workflows/test.yml:99-139`) builds only `py312-num1-accel0-dispctypes`
— acceleration absent, ctypes entry points. The single `accel1-dispc` job
(`test.yml:46`) runs on ubuntu/llvmpipe only. Two consequences: the
`accelerate` extension's *build* is unproven on macOS (setup.py, the generated
table includes, the compiler flags), and no macOS behaviour of the compiled
layer is ever exercised — this after `bafd44a5` went to the trouble of giving
macOS a headless CGL backend precisely so a GPU-less runner can run the suite.
Why it matters: the release's flagship labour — the C tables, the pointer and
array conversions, the debug-output callback — is validated on exactly one
platform/compiler pair, and a macOS-only compile or load-time failure would
ship to every macOS user as an import error. Fix: add the
`py312-num1-accel1-dispc` env to the macos matrix. CGL needs no window server
for the fixture (that is `777ca6b7`'s point), and the entry points resolve
against the same GL library the ctypes config already loads.

**2. The `gltest` decorator no longer presents the final frame.** The old
decorator ended every run with `glfw.swap_buffers(SCREEN);
glfw.destroy_window(SCREEN)` (`tests/testdecorator_glfw.py` before
`777ca6b7`). The new one does `case.setUp()`, runs the function, then
`case.doCleanups()` in a `finally` (`tests/testdecorator.py:55-63`); the swap
lives in the backend's teardown hook that the decorator deliberately never
calls. For headless runs this is invisible and harmless. For an interactive
run of the `tests/check_*.py` scripts under `TEST_VISIBLE=1` the rendered
buffer is destroyed before it is presented, so a bug visible only on the final
frame cannot be seen. Why it matters: `TEST_VISIBLE` exists so a developer can
look at what the suite drew. Fix: present (call the backend's swap hook) in
the `finally` before `doCleanups()` when the context is windowed.

**3. The "read the flags late" mechanism freezes on the first
`_configflags` import.** `OpenGL/__init__.py:400-404` deliberately delays
importing `_configflags` so that the flags a program sets in the lines after
`import OpenGL` are what the layers read. `_configflags.py:3-20` snapshots
`USE_ACCELERATE` and friends at its own first import — which happens at the
first entry-point build, so the mechanism works in the common single-process
order (verified empirically: `OpenGL.USE_ACCELERATE = False` before `import
OpenGL.GL` disables the C layer). The fragility: the *first* thing to import
`OpenGL._configflags` — a framework, a profiler, a different binding stacked
on PyOpenGL — fixes the snapshot, and every later assignment to
`OpenGL.USE_ACCELERATE` becomes inert. The documented escape hatch then
silently stops working for that program, with no error. Fix: have `_wanted()`
read `getattr(OpenGL, 'USE_ACCELERATE')` live at call time instead of the
snapshot, or expose the flags through a module `__getattr__` that reads the
live module attributes.

### Low

**4. `use_debug_output(False)` mixes a process-global error mode with
per-context callbacks.** Disabling pops the callback for *this* context and
calls `_c.set_error_mode(0)` (`.dispatch/__init__.py:387-394`); the error-mode
switch is process-global. With two contexts in one process, both with debug
output installed, disabling in one flips the checking mechanism back to
per-call `glGetError` for the *other* context too, while its driver-side debug
output and callback stay live. Correctness is unaffected (the check mechanism
and the callback agree on which errors exist), but the switch is not
reversible per context, which the docstring's "undoes what switching it on
did" (`__init__.py:370-372`) implies it is. Fix: track enabled callbacks per
context and only reset the global mode when the last one disables.

**5. `GLsizeiptr` remains unsigned end-to-end against a signed Khronos
definition.** `OpenGL/raw/GL/_types.py:97` defines `GLsizeiptr` as
`ctypes.c_size_t` and the new numpy mapping sends `GL_SIZEIPTR` to `'P'`
(`arrays/numpymodule.py:271`) — both unsigned `size_t`. Khronos declares it
`khronos_ssize_t` (ptrdiff\_t). Pre-existing, not introduced in this window,
but the new pointer-array work and the generated C table entrench the choice.
Practical impact is limited (sizes and offsets arrive non-negative), and the
types are internally consistent, so this is a documentation note more than a
defect: record the deviation next to the definition so a future reader does
not "fix" one side and break the other.

**6. `pygl_boolean_slow` contracts with the caller through a pending
exception.** `pygl_runtime.c:594-601` returns 0 when `PyObject_IsTrue` fails,
leaving the exception pending for `PYGL_CONV_OK` to divert to
`pygl_argument_error`. The behaviour is correct and matches ctypes (verified:
a numpy array with ambiguous truth value raises `ctypes.ArgumentError` from
the call, and the next call is clean). The function's correctness depends on
two conventions none of its own code states — the pending exception survives
the return, and every caller checks `PyErr_Occurred()` before proceeding. A
comment stating the contract on the function would keep a future reordering of
those checks from silently swallowing conversion errors.

**7. `uv.lock` removal trades CI reproducibility for library policy.**
`33a25e30` deletes the 773-line lockfile with "a library does not pin its
dependencies". Reasonable as policy for a distributable, but the five CI tox
envs now resolve at run time and can drift from each other and from a
developer's machine between releases. If a release-time full-suite run ever
needs to be repeatable, pinning a CI-only resolution (e.g. a lock committed
under `ci/`) is the tool, and nothing here forces that choice yet.

**8. `_lookup_dirtied_block` is a process-global crossing contexts and
threads.** `OpenGL/error.py:190-207` tracks, in one global, whether an error
was noted inside a `glBegin` block. It matches the pre-existing begin-block
global pattern, but two threads each making their own context current can
misattribute a block note to the wrong end. Consistency here is encouraging —
no crash, no incorrect state — and the pattern predates the window, so this
is recorded as known shape rather than a defect to fix now.

### Checked and cleared

The following were investigated as candidate defects and refuted, each with an
empirical demonstration; they are recorded so the next reviewer does not
re-derive them.

- **`pygl_boolean_slow` swallowing exceptions** — not a defect; see finding 6
  for the contract that makes it correct.
- **`customise=True` bailing when `_output_parameters` is None** — cannot
  happen: `absorb_chains.py`'s `_statable` refuses to migrate any module whose
  `setOutput` uses sizes `_output_parameters` cannot state, and the table test
  guards it.
- **`use_debug_output(False)` not disabling** — fixed by `743fa8ef` (per-context
  callback registry); only the residual in finding 4 remains.
- **The `gltest` spurious `SkipTest` on headless backends** — removed by
  `777ca6b7`; the decorator now runs the context under `pick_backend()`.
- **`OpenGL.CONTEXT_CHECKING` set too late at import** — addressed by
  `777ca6b7` as its commit message describes, settling it in a subprocess where
  the suite needs to know what a no-context call does.

## What is good and should stay

- **Generated-table provenance.** Every shipping enum and signature names the
  registry commit it came from, and a PyOpenGL/accelerate pair built against
  different inputs refuses to run (`a6ffed98`, the `_versions_match` gate in
  `.dispatch/__init__.py:226-237`). This closes the class of bug where two
  builds of one tag disagree silently.
- **The demotion and begin-block machinery.** `note_lookup_inside_block` /
  `take_lookup_inside_block` (`error.py`) consumed once by `glEnd`
  (`GL/exceptional.py`) is a clean-room-ready, testable design; the C layer's
  own `make_current`/`forget_context` clearing of the same switch is symmetric
  with it.
- **Array binding by name, not position** (`9b31283e`). The C layer resolves
  array classes through a generated name table, removing the shared-position
  invariant that made the two-sided tables fragile.
- **Pointer-array handling** (`808dce51`): `GLintptrArray`/`GLsizeiptrArray`,
  pointer-element resolution through `_type_`, and a `TypeError` instead of
  silent pass-through when no array class fits.
- **The test-suite consolidation** (`777ca6b7`): one backend vocabulary
  (`tests/backends.py`), `pick_backend()`, `DesktopGLTestCaseBase` with the
  profile/version the legacy suites were written against, and the four
  per-backend modules gone. The suite gains instead of losing; the EGL-device
  run of `tests/gl` + `tests/glu` in this review passed 330, skipped 307, with
  798 subtests.

## Test evidence

Runs by this reviewer (all green, C dispatch unless noted, Mesa llvmpipe):

| Suite | Configuration | Result |
|---|---|---|
| `tests/cdispatch/` | default (C) | 345 passed |
| `tests/gl/` `tests/glu/` | `TEST_WINDOWING=egl` headless | 330 passed, 307 skipped, 798 subtests |
| `tests/test_backend_names.py` `tests/test_shared_context_setup.py` | default | 26 passed (EGL subprocess included) |
| `tests/test_checks.py` | default (wayland) | 8 passed, 18 skipped, 1 xfail (environmental skips) |
| `tests/test_intptr_arrays.py` `test_declaration_types.py` `test_dispatch_selection.py` `test_attribute_surface_api.py` | default | 58 passed |
| `tests/test_core.py` | default (GLFW) | 28 passed, no skips |

The `test_checks.py` skips are the machine's session (wayland: the
`glx_only`/`xlib_only`/`glut_only` decorators skip, one `egl_pygame` xfails),
not configuration drift.

## Documentation

Documentation landed with the features it describes (EGL device page with
`deadadaa`, C-dispatch pages, the backend/CGL notes, `_configflags` docstring
rewrite). Finding 6 asks only for a code comment, finding 5 for a line of
documentation next to the definition. No documentation file in this window was
left describing an older world.

## Suggested follow-ups, in order

1. macOS `accel1-dispc` CI job (finding 1).
2. Present the last frame in `gltest` (finding 2).
3. Make `USE_ACCELERATE` a live read (finding 3).
4. Per-context error-mode accounting in `use_debug_output` (finding 4).
5. Comment/docstrings for findings 5 and 6.