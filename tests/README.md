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
├── conftest.py             puts tests/ on sys.path; forces PYOPENGL_PLATFORM=egl
│                             for the egl backend
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
├── basetestcase*.py        legacy root-level windowing dispatch + glfw/pygame
├── testdecorator*.py       legacy `@gltest` decorator dispatch
├── test_*.py               legacy root-level tests (use basetestcase/testdecorator)
└── check_*.py / *.py       stand-alone check scripts run out-of-process by
                              test_checks.py
```

> **Note on file names:** the suites are collected without `__init__.py`
> (pytest *prepend* import mode), so **every `test_*.py` basename must be unique
> across the whole tree** — e.g. the ES copies are `test_es_nv_state.py`, not a
> second `test_ext_nv_state.py`.

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
- `check_error(context='')` — assert no pending GL error.
- `read_pixel` / `read_image` / `assert_pixel` — framebuffer readback.
- `getString` / `getStringi` / `getInteger` / `version` / `extensions`.
- `compile_program(vs, fs, extra_stages=())` — compile + link a program.
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

A fixture or a child script that opens its own window — several must, for a
hint `pick_backend` does not take or a question that is settled once per
process — has one trap to avoid: **`glfw.create_window` answers a NULL
`LP__GLFWwindow` where it could not make one, which is falsy but not `None`.**
`if window is None` therefore reads a refusal as a window, and every call
through the context that is not there answers zero. Write `if not window`, or
`glcontext.window_was_made(window)`, which says why.

Other knobs: `TEST_VISIBLE=0` runs headless-ish (hidden windows, no dwell);
`TEST_DWELL=<seconds>` controls the per-test on-screen pause; `TEST_EGL_DEVICE=<n>`
pins a specific EGL device. Under the `egl` backend the legacy root-level
*windowed* tests skip (a window plus the egl-device platform is incompatible).

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
8. **Back every interface block a draw or dispatch will execute.** An active
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

## Running

```
# whole matrix (6 Pythons × numpy × accelerate), windowed:
uv run --with tox,tox-uv tox

# one configuration, headless on the real GPU:
TEST_WINDOWING=egl python -m pytest -q tests/gl tests/gles tests/glu

# software / windowed:
TEST_VISIBLE=0 python -m pytest -q tests/
```

The legacy `test_checks.py` runs `check_*.py` scripts out-of-process; those are
windowed and are run in the default windowed mode even when the outer run uses
the headless `egl` backend.
