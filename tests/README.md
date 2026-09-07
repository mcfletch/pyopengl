# PyOpenGL test suite

## Why these tests exist

The point of this suite is **to improve PyOpenGL**, not to accumulate green
checkmarks. A test earns its place when it can surface a real defect — a broken
wrapper, a wrong array size, a mis-generated entry point, a bad type signature.
When a test turns up a bug in the library, **fix the library**; do not work
around it in the test. (For example, exercising `glProgramNamedParameter4fNV`
with a multi-character name revealed `setInputArraySize('name', 1)` in
`OpenGL/GL/NV/fragment_program.py` hard-capping names to one byte — the fix was
to the wrapper, not the test.)

Three principles follow from that:

1. **Make real calls, not "not falsey" probes.** Calling an entry point and
   checking only that it is non-null (or wrapping everything in a blanket
   error-swallowing context) proves almost nothing. Build the real objects the
   call needs, pass valid arguments, and assert a clean GL error state (and,
   where practical, the actual result). A call that *reaches the driver and does
   the thing* is the bar.

2. **Write `glGet*` tests for the parameters an extension / version introduces,
   when the platform supports them.** Each version level and each supported
   extension adds queryable state; exercise those getters with correctly-sized
   buffers and sane expectations. Wrong output sizes are a recurring,
   memory-corrupting class of bug (see `get_checked`, below) — getters are
   exactly where they hide.

3. **Run everywhere PyOpenGL runs.** The suite must work on **Linux (Wayland or
   GLX), Windows, and Apple**. Prefer the toolkit-agnostic base classes and the
   windowing backends below over anything platform-specific. Where a test
   genuinely cannot run on a platform/driver/headless setup, `skipTest` with a
   clear reason rather than failing — and never silently special-case one OS.

If a call genuinely cannot succeed in a given environment (external Vulkan/fd
interop, multi-GPU SLI, a window-system framebuffer that a headless context
lacks), skip it **with a reason** and do not count it as covered. That is
honesty, not a workaround.

## Directory map

```
tests/
├── glcontext.py            shared, API/toolkit-agnostic base: ContextTestCase,
│                             pick_backend(), get_checked()/require_entrypoint(),
│                             check_error/read_pixel/assert_pixel/exercise/...
├── glcontext_glfw.py       windowing backend: on-screen glfw window
├── glcontext_pygame.py     windowing backend: on-screen pygame/SDL window
├── glcontext_egl.py        windowing backend: headless EGL device (real GPU,
│                             no window) — for CI / containers
├── glcontext_desktop.py    DesktopGLTestCaseBase (OpenGL.GL) + GLUTestCaseBase
├── glcontext_es.py         ESTestCaseBase (OpenGL.GLES2 / GLES3)
├── conftest.py             what must be settled before any test module is
│                             imported: PYOPENGL_PLATFORM=egl for the egl
│                             backend, and that the dispatch implementation is
│                             the one the run asked for
├── arraycompat.py          `from arraycompat import np` — numpy, or a ctypes
│                             fallback for the no-numpy (num0) tox environments
│
├── gl/                     desktop OpenGL suite
│   ├── gltestcase.py         -> `from gltestcase import GLTestCase`
│   ├── gl_coverage.py        entry-point coverage report
│   ├── supported_extensions.json   coverage manifest (extensions + with_funcs)
│   └── test_*.py             the tests
├── gles/                   OpenGL-ES suite
│   ├── egltestcase.py        -> `from egltestcase import ESTestCase`
│   ├── es_coverage.py        coverage report
│   ├── supported_extensions.json
│   └── test_*.py
├── glu/                    GLU suite
│   ├── glutestcase.py        -> `from glutestcase import GLUTestCase`
│   ├── glu_coverage.py
│   └── test_*.py
│
├── cdispatch/              the build-time code generator, which reads the
│                             Khronos registry out of `src/` and emits the
│                             C, the stubs and the tables `OpenGL/raw` is
│                             built from
│
├── bindings/               the library itself, with no GL context -- or one
│   │                         taken in a child process
│   ├── dispatch/             which implementation is installed, what an entry
│   │                           point exposes, alternate(), demotion
│   ├── generated/            OpenGL.raw: the virtual modules, the declaration
│   │                           tables, the stubs, the plug-in registry
│   ├── arrays/               ArrayDatatype and the format handlers
│   ├── platform/             which library each platform dispatches to
│   ├── egl/ wgl/ glx/        the window-system bindings
│   ├── tk/ glut/             the toolkits PyOpenGL ships an integration for
│   └── errors/               error checking and the debug-output policy
├── harness/                tests OF the fixtures above, rather than of the
│                             library: the backends, the context requirements,
│                             what collects where
├── checks/                 stand-alone check scripts and the runner that
│                             discovers them
├── directdocs/             the documentation build tool
├── data/                   fixtures the suites read rather than build
│
├── paths.py                ROOT / TESTS / SRC / PACKAGE, worked out once
├── testdecorator.py        `@gltest`: the same fixture around a plain function,
│                             for the stand-alone check scripts
└── report_*.py             programs CI runs to say what the machine has;
                              nothing collects these
```

> **Do not compute the checkout's location from `__file__`.** `from paths import
> ROOT` — counting `os.path.dirname` calls encodes how deep the file happens to
> sit, so moving a module changes what the name means without breaking it. That
> is not hypothetical: it is what the move into these directories did to a dozen
> modules, and the symptoms were a registry that parsed as empty, a parametrised
> case that collapsed to one `NOTSET`, and a test that skipped saying there was
> no raw tree to read.

`pyproject.toml` holds the settings that shape a run: `pythonpath` (which is
what puts this directory and the suite directories on the path, so the helpers
import by bare name), `--import-mode=importlib`, `xfail_strict`,
`filterwarnings = error`, a per-test `timeout`, and the markers below. Nothing
under `tests/` edits `sys.path`.

> **Warnings are errors.** A `ResourceWarning` for a file the test left open, a
> deprecation with a deadline: the run fails on it rather than printing it into
> a summary nobody reads. A warning that is genuinely not ours goes in the
> `filterwarnings` list in `pyproject.toml`, with the reason. Two things to know
> about writing one of those: the message pattern is matched against the *start*
> of the message, and `.` does not match a newline — a message that opens with
> one needs `(?s)`, or the entry silently matches nothing.

### Where a test belongs

Find the row that describes what the test is *about*. Nothing in this suite is
filed by when it was written or by which bug it came from — a module named for
its provenance stops being findable the moment the provenance stops mattering,
and that is how thirty context-backed GL tests came to live beside the fixture
that serves them.

| What the test is about | Where it goes |
|---|---|
| A desktop GL entry point introduced at a version | `gl/test_gl<major><minor>.py`, or `gl/test_gl1_<area>.py` for the fixed-function ones |
| A desktop GL extension | `gl/test_ext_*.py`, grouped by vendor and era |
| The size a `glGet*` writes | `gl/test_glget_*.py`, and the pname in `gl/glget_groups.json` |
| Pixel data crossing the boundary — readback shape, target-array sizing | `gl/test_images.py` |
| GLE tubing and extrusion | `gl/test_gle.py` |
| An OpenGL-ES entry point or extension | `gles/` |
| GLU — quadrics, NURBS, tessellation, projection, mipmaps | `glu/test_glu_<area>.py` |
| The code generator: the registry, the annotations, the C and stubs it emits | `cdispatch/` |
| Which implementation is installed, what an entry point exposes, `alternate()`, demotion | `bindings/dispatch/` |
| `OpenGL.raw`: virtual modules, declaration tables, stubs, constants, the plug-in registry | `bindings/generated/` |
| `ArrayDatatype`, the format handlers, the buffer protocol | `bindings/arrays/` |
| Which library a platform dispatches to, and what it costs to import | `bindings/platform/` |
| EGL, WGL or GLX as a binding rather than as a backend | `bindings/egl/`, `bindings/wgl/`, `bindings/glx/` |
| The Tk widget or the GLUT integration | `bindings/tk/`, `bindings/glut/` |
| Error checking, `CONTEXT_CHECKING`, the debug-output policy | `bindings/errors/` |
| The suite's own fixtures, backends and collection | `harness/` |
| A program needing a toolkit main loop, a window of its own, or a fresh process | a `checks/check_*.py` script — see [Check scripts](#check-scripts) |
| A report about what the machine has, for CI to print | a `report_*.py` script; nothing collects these |

Three questions decide most of it:

1. **Does it need a GL context?** If so it belongs in `gl/`, `gles/` or `glu/`
   behind one of the base cases, and not in `bindings/`. A test that takes a
   context it does not use costs every run the context and hides the fact that
   the subject needs no GL at all.
2. **Is the answer settled once per process?** Which dispatch implementation is
   installed, what an import costs, what a call with no context does: those run
   in a child, through `glcontext.CHILD_PREAMBLE` and
   `childenv.child_environment()`.
3. **Does it need a window, or a main loop?** Then it is a check script, not a
   test case.

### Configuration flags

`OpenGL/__init__.py` documents flags a caller sets before importing the
library, most of them settable as `PYOPENGL_<NAME>` in the environment. The
suite is run under them, because they change what the entry points do:

| Flag | What a run under it asserts |
|---|---|
| `PYOPENGL_ERROR_ON_COPY=1` | The caller refuses the implicit copy PyOpenGL makes for a Python sequence or a mismatched array. Cases whose subject *is* that conversion skip, saying so; the rest keep working. Build data with `arraycompat.copy_safe` where the list was incidental, and `arraycompat.object_names` for GL object names. |
| `PYOPENGL_ARRAY_SIZE_CHECKING=0` | The output-size check is off. The cases that assert the refusal skip. |
| `PYOPENGL_USE_ACCELERATE=0` | The compiled accelerators are off, whether or not they are installed. Ask `OpenGL.dispatch.settle()`, not `_dispatch.AVAILABLE`: the extension being *importable* is not the same as its entry points being the ones installed. |

`tox.ini` carries these as a `flag{...}` factor on the newest interpreter,
crossed with numpy and accelerate — which is what an array flag is a claim
about — rather than across the whole interpreter sweep.

**Passing a list is not a bug to fix.** It is how the list handler gets
exercised, and PyOpenGL copying it is the documented default. `copy_safe` is
for a case where the list was merely the readable way to write the data; a case
that is *about* what a list does keeps the list and skips under the flag.

### Markers

| Marker | What it means | Deselect with |
|---|---|---|
| `performance` | asserts how fast something draws, so it needs a GPU | `-m "not performance"` |
| `resources` | asserts a budget in memory or import time, so it measures the machine as much as the library | `-m "not resources"` |
| `slow` | takes seconds because it builds something — a frozen application, an archive | `-m "not slow"` |

## The base test cases

A test declares the context it needs via class attributes and gets a current,
cleared context to render into. The toolkit-agnostic base
(`glcontext.ContextTestCase`) reaches GL through `self.gl` / `self.gl3` (set by
the API mixin), so the same helpers work for desktop GL and ES.

| Suite | Import | Base | GL module |
|-------|--------|------|-----------|
| `gl/`   | `from gltestcase import GLTestCase`   | `DesktopGLTestCaseBase` | `OpenGL.GL` |
| `glu/`  | `from glutestcase import GLUTestCase` | `GLUTestCaseBase`       | `OpenGL.GL` + `OpenGL.GLU` |
| `gles/` | `from egltestcase import ESTestCase`  | `ESTestCaseBase`        | `OpenGL.GLES2` / `GLES3` |

Each concrete case is `class Case(pick_backend(), <API base>)`: the windowing
backend supplies `_create_context` / `_swap` / `_destroy_context`; the API base
supplies `self.gl` and API-specific helpers.

Useful class attributes (override per test): `profile` (`'core'` /
`'compatibility'`), `gl_version`, `api` (`'gl'` / `'gles'`), `red_size` …
`stencil_size`, `accum_size`, `width` / `height`, `visible`, `dwell`.

Helpers on the base classes:

- `require_extension(name)` / `require_version(major, minor)` — skip if absent.
- `require_feature(name, core, extension)` — skip unless the *context* has the
  feature, either by being new enough or by listing the extension. Ask this
  rather than `bool(some_entry_point)`, which is a question about the library:
  see “A resolved entry point is not an implemented feature” below.
  `require_vertex_arrays()` is the desktop shorthand for the common one.
- `check_error(context='')` — assert no pending GL error.
- `read_pixel` / `read_image` / `assert_pixel` — framebuffer readback.
- `getString` / `getStringi` / `getInteger` / `version` / `extensions`.
- `compile_program(vs, fs, extra_stages=())` — compile + link a program.
- `framebuffer(fbo)` — a `with` block that binds `fbo` and then rebinds
  whatever was bound before it, rather than binding zero. `colour_buffer_name()`
  / `draw_framebuffer()` answer what this context draws into.
- **`get_checked(fn, args, count, dtype)`** — call a `glGet*v` getter with an
  oversized, canary-filled buffer and assert it wrote no further than `count`
  elements. Use this when the output size is uncertain: a too-small buffer
  silently overruns the heap and crashes much later somewhere unrelated.
- `require_entrypoint(fn, name)` — skip if an ES-only EXT command collides with a
  desktop-GL name and PyOpenGL cached a null for it under the shared egl process.
- `exercise()` / `tolerate_glerror(*codes)` — narrowly tolerate a *documented*,
  expected GLError (a known driver gap). Not a general crutch; the surrounding
  calls must still succeed.

## Windowing backends — `TEST_WINDOWING`

Selected by `pick_backend()` from the `TEST_WINDOWING` environment variable
(default: glfw, then pygame). All three serve both desktop GL and ES.

| `TEST_WINDOWING` | Backend | Notes |
|------------------|---------|-------|
| `glfw` (default) | on-screen glfw window | desktop GPU, or llvmpipe under a software compositor |
| `pygame`         | on-screen pygame/SDL window | same |
| `egl`            | **headless EGL device** (`glcontext_egl.py`) | renders directly on a GPU with no window system — the right choice for CI / containers where the compositor is software-rendered. Forces `PYOPENGL_PLATFORM=egl`; ES vs GL both work via an offscreen pbuffer. |
| `cgl`            | **headless macOS context** (`glcontext_cgl.py`) | CGL is the layer NSGL and AGL are built on and the only one that hands out a context with no window server, which is what a macOS CI runner has. Framebuffer zero belongs to a drawable and there is none, so the backend binds a framebuffer object of the requested size. No OpenGL-ES, and no compatibility profile above 2.1; `TEST_CGL_RENDERER` pins the renderer kind. |

On a Wayland session with the NVIDIA driver, `glReadPixels` from an on-screen
window answers black however the frame was drawn, so the cases that read back
what a widget rendered fail there and pass under `xvfb-run`. The Linux CI runs
the whole suite under `xvfb-run -a` already; a developer on such a session wants
the same for the windowed suites.

On an NVIDIA driver, roughly one run in ten dies with SIGSEGV while a context is
torn down. The faulting frame is inside `libnvidia-eglcore`, reached through
`eglDestroyContext` (or, under `glfw`, through `glfwDestroyWindow` →
`destroyContextEGL`, which calls it); no frame between the fault and the call
belongs to PyOpenGL. `gdb -q -batch -ex run -ex 'bt 40' --args python -m pytest
…` catches it in a few attempts. Mesa and the macOS backends do not show it, so
neither does CI.

**Framebuffer zero is the drawable's, and a headless CGL context has no
drawable.** So `glBindFramebuffer(GL_FRAMEBUFFER, 0)` — the usual shorthand for
finishing with a framebuffer object — leaves a macOS context with nothing
complete to draw into, and the next call that needs a framebuffer answers
`GL_INVALID_FRAMEBUFFER_OPERATION` against itself, saying nothing about the
unbind that caused it. Use `with self.framebuffer(fbo):`, which puts back
whatever was bound before; where a case must bind by hand, restore
`self.draw_framebuffer()` read *before* the bind, not zero.

**A resolved entry point is not an implemented feature.** macOS exports every
entry point from its framework whatever the current context implements, so
`bool(glGenVertexArrays)` is true on the 2.1 legacy profile that carries its
fixed-function pipeline — and the call then answers `GL_INVALID_OPERATION`,
after the guard has already decided the feature was there. Ask the context:
`require_feature(...)`, `require_extension(...)` or `require_version(...)`. On a
driver that resolves only what it implements, the symbol guard hides this
completely.

A fixture or a child script that opens its own window — several must, for a
hint `pick_backend` does not take or a question that is settled once per
process — has one trap to avoid: **`glfw.create_window` answers a NULL
`LP__GLFWwindow` where it could not make one, which is falsy but not `None`.**
`if window is None` therefore reads a refusal as a window, and every call
through the context that is not there answers zero. Write `if not window`, or
`glcontext.window_was_made(window)`, which says why.

Other knobs: `TEST_VISIBLE=0` runs headless-ish (hidden windows, no dwell);
`TEST_DWELL=<seconds>` controls the per-test on-screen pause; `TEST_EGL_DEVICE=<n>`
pins a specific EGL device; `TEST_CHECK_TIMEOUT=<seconds>` bounds one check
script (120 by default) where the per-test `timeout` in `pyproject.toml` bounds
everything else. Under the `egl` backend the legacy root-level *windowed* tests
skip (a window plus the egl-device platform is incompatible).

## Adding a test

1. Pick the suite (`gl/`, `gles/`, `glu/`) and a **unique** `test_*.py` basename.
2. Subclass the suite's base case; set `profile` / `gl_version` / `api` etc. for
   the context you need.
3. `require_extension(...)` / `require_version(...)` first, so unsupported
   platforms skip cleanly.
4. **Make real calls.** Create the objects (buffers, textures, programs,
   framebuffers), pass valid arguments, and end with `self.check_error(...)`.
   Assert real results (pixels, returned values) where you can.
5. For every getter the feature adds, query it with a correctly-sized buffer (or
   `get_checked`) and check the result is sane.
6. Build array data with `from arraycompat import np` so the test also runs in
   the no-numpy environments.
7. If a specific entry point cannot succeed here (external interop, multi-GPU, a
   window-system-only path), `skipTest('<why>')` and do **not** reference its
   name where the coverage scanner would count it.
8. **Reach for `OpenGL.EGL` only behind
   `pytest.importorskip('OpenGL.EGL', exc_type=ImportError)`.** EGL ships with
   the graphics driver and macOS has none, so the binding raises `ImportError`
   naming the missing library — deliberately, because `try: from OpenGL import
   EGL` is how a program asks whether the machine has it. Since pytest 8.2
   `importorskip` catches only `ModuleNotFoundError`, so without `exc_type` that
   is a *collection* error, and pytest abandons the whole run rather than the
   one module. Importing `glcontext_egl` counts: it is the EGL backend. No other
   PyOpenGL subpackage does this — `OpenGL.GLUT` and friends import fine with no
   library and answer `NullFunctionError` when called.
   `tests/test_collects_without_egl.py` collects the suite on a machine
   pretending to have no EGL, which is where this is caught.
9. **Back every interface block a draw or dispatch will execute.** An active
   uniform block, shader storage block or atomic counter buffer with no buffer
   object bound to its binding point leaves the results of shader execution
   undefined, and the specification allows a driver to interrupt or terminate on
   it (GL 4.6 core, 7.6.3 and 7.8) — a segfault rather than a `glGetError`
   result, on the drivers that take the licence. `glGetError` reports nothing,
   and the tolerant drivers say nothing either, so a case that draws with an
   unbacked block passes everywhere until it reaches the one that does not.
   Either bind a buffer for the block or give the case a program without one.

Run it on a real GPU (`TEST_WINDOWING=egl` in a container, or windowed on the
host) **and** on the software path, and confirm it skips where it should.

## Coverage tooling

`gl/gl_coverage.py`, `gles/es_coverage.py`, and `glu/glu_coverage.py` count the
`gl*` entry points defined per version / per supported extension and report which
ones the tests call. `supported_extensions.json` (`extensions` list +
`with_funcs` map) is the coverage universe. When you add real coverage for an
extension, add it (with its full function list) to `with_funcs` so the report
reflects it; only list functions you actually exercise, so partial coverage reads
honestly.

```
python gl/gl_coverage.py           # summary
python gl/gl_coverage.py --ext     # per-extension
python gl/gl_coverage.py --ext-uncovered
```

`gl/enum_age_audit.py` reports enums a case names that the context it asks for
predates — a 4.3 enum in a 3.3 context is `GL_INVALID_ENUM`, and Mesa accepts it
where macOS does not, so the case passes here and fails on someone else's
machine. It exits non-zero only for a use outside a block that tolerates the
error or asks the context its version first.

```
python gl/enum_age_audit.py
```

## Running

```
# whole matrix (6 Pythons × numpy × accelerate), windowed:
uv run --with tox,tox-uv tox

# one configuration, headless on the real GPU:
TEST_WINDOWING=egl python -m pytest -q tests/gl tests/gles tests/glu

# software / windowed:
TEST_VISIBLE=0 python -m pytest -q tests/
```

## Check scripts

A check script is a program rather than a test case: it opens a window, drives
a toolkit's main loop, or settles a question that can only be asked once per
process. `test_checks.py` runs each of them out-of-process, and they are run in
the default windowed mode even when the outer run uses the headless `egl`
backend.

**Every `check_*.py` beside `test_checks.py` is run — the runner globs, it does
not keep a list.** So adding a script is adding a file, and a script that
nothing runs cannot happen. (It used to: `check_autocomplete.py` and
`check_querier_version_parse.py` sat in this directory for years under a runner
that named its scripts by hand, and neither was ever launched.) A program that
*reports* rather than checks — `report_cgl_context.py`,
`report_egl_device_enumeration.py`, both of which CI runs to say what the
machine has — is named `report_*` and is not collected.

A script says what it needs in a `# requires:` line among its first forty:

```python
#! /usr/bin/env python
# requires: glut numpy
```

read out of the file rather than imported, since whether it imports at all is
part of what running it answers. The vocabulary is `numpy`, `window-server`,
`xlib`, `glx` and `glut`; a word outside it fails the run rather than quietly
skipping, so a typo cannot become a check that never runs.

A script that cannot run on *this particular* machine — a driver that refuses
the context, an SDL that will not open a display — says so at run time by
exiting 77: `checkutils.skip(reason)`, or `checkutils.require('some.module')`
for a dependency, which the harness reports as a skip. A script that instead
dies on an import or a null entry point prints nothing, and no output is a
*failure*, since that is how the harness tells a working check from a broken
one. On success it prints `OK`.

Two things a GLUT check script has to ask about, both of which classic GLUT
(macOS's) answers differently from freeglut:

- **Context creation.** `glutInitContextVersion`, `glutInitContextFlags`,
  `glutInitContextProfile` and `glutSetOption` are freeglut's. A script that
  needs them checks `if not glutInitContextVersion` and skips.
- **Leaving the main loop.** Classic GLUT has no way out of `glutMainLoop`;
  that gap is why freeglut added `glutLeaveMainLoop`. A script whose callback
  ends the run must fall back to `os._exit(0)` where that entry point is
  absent, or it spins until the harness times it out — having printed its `OK`,
  so the log says the check succeeded and the run says it failed.
