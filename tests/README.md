# PyOpenGL test suite

## Why these tests exist

This suite exists to find defects in PyOpenGL: a broken wrapper, a wrong array
size, a mis-generated entry point, a bad type signature. When a test turns up a
bug in the library, fix the library and leave the test as it is. For example,
calling `glProgramNamedParameter4fNV` with a multi-character name showed that
`setInputArraySize('name', 1)` in `OpenGL/GL/NV/fragment_program.py` cut names
to one byte. The fix went into the wrapper.

Three principles follow from that:

1. Make real calls. A test that only checks an entry point is non-null, or wraps
   everything in a context that swallows errors, proves very little. Build the
   objects the call needs, pass valid arguments, and assert a clean GL error
   state. Where practical, assert the result as well. The call has to reach the
   driver and do its work.

2. Write `glGet*` tests for the parameters each extension or version introduces,
   when the platform supports them. Each version level and each supported
   extension adds queryable state. Query it with correctly-sized buffers and
   check the values are sane. Wrong output sizes are a recurring bug that
   corrupts memory (see `get_checked`, below), and getters are where they occur.

3. Run everywhere PyOpenGL runs. The suite must work on Linux (Wayland or GLX),
   Windows and macOS. Prefer the toolkit-agnostic base classes and the windowing
   backends below over anything platform-specific. Where a test cannot run on a
   platform, driver or headless setup, call `skipTest` with a clear reason
   instead of failing. Do not special-case one OS silently.

Some calls cannot succeed in a given environment: external Vulkan or fd
interop, multi-GPU SLI, or a window-system framebuffer that a headless context
lacks. Skip those with a reason, and do not count them as covered.

## Directory map

```
tests/
├── glcontext.py            shared, API/toolkit-agnostic base: ContextTestCase,
│                             pick_backend(), get_checked()/require_entrypoint(),
│                             check_error/read_pixel/assert_pixel/exercise/...
├── glcontext_glfw.py       windowing backend: on-screen glfw window
├── glcontext_pygame.py     windowing backend: on-screen pygame/SDL window
├── glcontext_egl.py        windowing backend: headless EGL device (real GPU,
│                             no window), for CI and containers
├── glcontext_osmesa.py     windowing backend: OSMesa, rasterising into an
│                             array of our own, with no display server
├── glcontext_desktop.py    DesktopGLTestCaseBase (OpenGL.GL) + GLUTestCaseBase
├── glcontext_es.py         ESTestCaseBase (OpenGL.GLES2 / GLES3)
├── conftest.py             what must be settled before any test module is
│                             imported: PYOPENGL_PLATFORM for the backends that
│                             need one (egl, osmesa), and that the dispatch
│                             implementation is the one the run asked for
├── platforms.py            which platform plugin this run selected, for a case
│                             only one of them can serve: `platforms.needs(...)`
├── arraycompat.py          `from arraycompat import np`: numpy, or a ctypes
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
├── bindings/               the library itself, with no GL context (or one
│   │                         taken in a child process)
│   ├── dispatch/             which implementation is installed, what an entry
│   │                           point exposes, alternate(), demotion
│   ├── generated/            OpenGL.raw: the virtual modules, the declaration
│   │                           tables, the stubs, the plug-in registry
│   ├── arrays/               ArrayDatatype and the format handlers
│   ├── platform/             which library each platform dispatches to
│   ├── egl/ wgl/ glx/        the window-system bindings
│   ├── osmesa/               OSMesa's own entry points, in child processes
│   │                           because the platform is chosen at import
│   ├── tk/ glut/             the toolkits PyOpenGL ships an integration for
│   └── errors/               error checking and the debug-output policy
├── gates/                  questions a parser settles about the tree itself,
│                             on any machine and with no GL: an error path
│                             nothing enters, a foreign function with no
│                             prototypes, two sibling APIs that drifted, a
│                             flag read somewhere other than where it is set,
│                             a test that cannot fail, a declared gate nothing
│                             runs.  See plans/STATIC-GATES.md
├── harness/                tests OF the fixtures above, rather than of the
│                             library: the backends, the context requirements,
│                             what collects where
├── checks/                 stand-alone check scripts and the runner that
│                             discovers them; `suitepath.py` there is what
│                             lets one import the helpers below when it is
│                             run as a file rather than by the runner
├── directdocs/             the documentation build tool
├── data/                   fixtures the suites read rather than build
│
├── paths.py                ROOT / TESTS / SRC / PACKAGE, worked out once
├── sources.py              the tree's own Python, parsed once: `from sources
│                             import package, suite` for a question a parser
│                             settles
├── stubs.py                the shipped `.pyi` surface, parsed once
├── tomlread.py             `from tomlread import load`: tomllib, or tomli
│                             on the two interpreters below 3.11
├── testdecorator.py        `@gltest`: the same fixture around a plain function,
│                             for the stand-alone check scripts
└── report_*.py             programs CI runs to say what the machine has;
                              nothing collects these
```

> Do not compute the checkout's location from `__file__`. Use `from paths import
> ROOT`. Counting `os.path.dirname` calls encodes how deep the file sits, so
> moving the module changes what the name points at without raising an error.
> Moving modules into these directories did this to a dozen of them. The
> symptoms were a registry that parsed as empty, a parametrised case that
> collapsed to one `NOTSET`, and a test that skipped because it found no raw
> tree to read.

`pyproject.toml` holds the settings that shape a run: `pythonpath`, which puts
this directory and the suite directories on the path so the helpers import by
bare name; `--import-mode=importlib`; `xfail_strict`; `filterwarnings = error`;
a per-test `timeout`; and the markers below. Nothing under `tests/` edits
`sys.path`.

> Warnings are errors. A `ResourceWarning` for a file the test left open, or a
> deprecation with a deadline, fails the run. A warning that comes from outside
> PyOpenGL goes in the `filterwarnings` list in `pyproject.toml`, with the
> reason. Two details matter when writing one of those entries. The message
> pattern is matched against the start of the message. The `.` in the pattern
> does not match a newline, so a message that starts with a newline needs
> `(?s)`, or the entry matches nothing and gives no sign of it.

### Where a test belongs

Find the row that describes the subject of the test. No test here is filed by
the date it was written or by the bug it came from. A module named after its
origin is hard to find once that origin is forgotten. That is how thirty
context-backed GL tests ended up beside the fixture that serves them.

| What the test is about | Where it goes |
|---|---|
| A desktop GL entry point introduced at a version | `gl/test_gl<major><minor>.py`, or `gl/test_gl1_<area>.py` for the fixed-function ones |
| A desktop GL extension | `gl/test_ext_*.py`, grouped by vendor and era |
| The size a `glGet*` writes | `gl/test_glget_*.py`, and the pname in `gl/glget_groups.json` |
| Pixel data crossing the boundary (readback shape, target-array sizing) | `gl/test_images.py` |
| GLE tubing and extrusion | `gl/test_gle.py` |
| An OpenGL-ES entry point or extension | `gles/` |
| GLU (quadrics, NURBS, tessellation, projection, mipmaps) | `glu/test_glu_<area>.py` |
| The code generator: the registry, the annotations, the C and stubs it emits | `cdispatch/` |
| Which implementation is installed, what an entry point exposes, `alternate()`, demotion | `bindings/dispatch/` |
| `OpenGL.raw`: virtual modules, declaration tables, stubs, constants, the plug-in registry | `bindings/generated/` |
| `ArrayDatatype`, the format handlers, the buffer protocol | `bindings/arrays/` |
| Which library a platform dispatches to, and what it costs to import | `bindings/platform/` |
| EGL, WGL or GLX as a binding rather than as a backend | `bindings/egl/`, `bindings/wgl/`, `bindings/glx/` |
| The Tk widget or the GLUT integration | `bindings/tk/`, `bindings/glut/` |
| Error checking, `CONTEXT_CHECKING`, the debug-output policy | `bindings/errors/` |
| The suite's own fixtures, backends and collection | `harness/` |
| A case that only one platform plugin can serve (GLX, EGL, WGL, OSMesa) | wherever its subject belongs, marked with `platforms.needs(...)` |
| A program needing a toolkit main loop, a window of its own, or a fresh process | a `checks/check_*.py` script; see [Check scripts](#check-scripts) |
| A report about what the machine has, for CI to print | a `report_*.py` script; nothing collects these |

Three questions decide most cases:

1. Does it need a GL context? If so, it goes in `gl/`, `gles/` or `glu/`
   behind one of the base cases, and not in `bindings/`. A test that creates a
   context it does not use adds that cost to every run. It also hides the fact
   that its subject needs no GL.
2. Is the answer fixed once per process? Examples are which dispatch
   implementation is installed, what an import costs, and what a call with no
   context does. These tests run in a child process, through
   `glcontext.CHILD_PREAMBLE` and `childenv.child_environment()`.
3. Does it need a window or a main loop? Then it is a check script, and not a
   test case.

### Configuration flags

`OpenGL/__init__.py` documents flags a caller sets before importing the
library. Most of them can also be set as `PYOPENGL_<NAME>` in the environment.
The suite runs under these flags, because they change what the entry points do:

| Flag | What a run under it asserts |
|---|---|
| `PYOPENGL_ERROR_ON_COPY=1` | The implicit copy PyOpenGL makes for a Python sequence or a mismatched array raises an error. This applies to array data only; a `str` name or label is still accepted and encoded. Cases whose subject is that conversion skip and give the reason. The other cases still run. Where a list was only a convenient way to write the data, build it with `arraycompat.copy_safe`; use `arraycompat.object_names` for GL object names. |
| `PYOPENGL_ARRAY_SIZE_CHECKING=0` | The output-size check is off. The cases that assert the size error skip. |
| `PYOPENGL_SIZE_1_ARRAY_UNPACK=0` | A query that produces one value returns a one-element array in place of the value. Read such a result with `OpenGL._scalar.as_int`, as the library does. |
| `PYOPENGL_USE_ACCELERATE=0` | The compiled accelerators are off, whether or not they are installed. Call `OpenGL.dispatch.settle()` in place of reading `_dispatch.AVAILABLE`, and read `acceleratesupport.ACCELERATE_AVAILABLE` in place of `import OpenGL_accelerate`. An importable extension does not mean its entry points are the ones installed. |

`tox.ini` carries these flags as a `flag{...}` factor on the newest
interpreter. The factor is crossed with numpy and accelerate, since the array
flags change how those handle arrays, and is not run across the whole
interpreter sweep. `USE_ACCELERATE` is the separate `useaccel0` factor. It
needs accelerate built: with the extension absent, a run cannot distinguish a
guard that checks whether the extension is in use from one that checks whether
it can be imported.

Passing a list is correct usage and does not need fixing. It exercises the list
handler, and copying a list is PyOpenGL's documented default. Use `copy_safe`
where a list was only the readable way to write the data. A case that tests
what a list does keeps the list and skips under the flag.

### Markers

| Marker | What it means | Deselect with |
|---|---|---|
| `performance` | asserts a speed that only a real driver can give (how fast something draws, or the cost of a round trip to the driver), so it needs a GPU with no other load | `-m "not performance"` |
| `resources` | asserts a budget in memory or import time, so its result depends on the machine as well as the library | `-m "not resources"` |
| `slow` | takes seconds because it builds something, such as a frozen application or an archive | `-m "not slow"` |

`tox` deselects `performance` and `resources` in every environment, so a
developer's tox run and a CI run leave out the same tests. A bare `pytest` still
runs both. That is the place to measure speed or memory: one machine, with
nothing else running. `tox -e ... -- -m performance` brings them back, because a
later `-m` overrides the one tox supplies.

## The base test cases

A test declares the context it needs through class attributes and gets a
current, cleared context to render into. The toolkit-agnostic base
(`glcontext.ContextTestCase`) reaches GL through `self.gl` / `self.gl3` (set by
the API mixin), so the same helpers work for desktop GL and ES.

| Suite | Import | Base | GL module |
|-------|--------|------|-----------|
| `gl/`   | `from gltestcase import GLTestCase`   | `DesktopGLTestCaseBase` | `OpenGL.GL` |
| `glu/`  | `from glutestcase import GLUTestCase` | `GLUTestCaseBase`       | `OpenGL.GL` + `OpenGL.GLU` |
| `gles/` | `from egltestcase import ESTestCase`  | `ESTestCaseBase`        | `OpenGL.GLES2` / `GLES3` |

Each concrete case is `class Case(pick_backend(), <API base>)`. The windowing
backend supplies `_create_context` / `_swap` / `_destroy_context`. The API base
supplies `self.gl` and API-specific helpers.

Useful class attributes (override per test): `profile` (`'core'` /
`'compatibility'`), `gl_version`, `api` (`'gl'` / `'gles'`), `red_size` …
`stencil_size`, `accum_size`, `width` / `height`, `visible`, `dwell`.

Helpers on the base classes:

- `require_extension(name)` / `require_version(major, minor)` - skip if absent.
- `require_feature(name, core, extension)` - skip unless the context has the
  feature, either because its version is new enough or because it lists the
  extension. Use this in place of `bool(some_entry_point)`, which only says
  whether the library resolved the symbol. See "A resolved entry point is not
  an implemented feature" below. `require_vertex_arrays()` is the desktop
  shorthand for the common case.
- `check_error(context='')` - assert no pending GL error.
- `read_pixel` / `read_image` / `assert_pixel` - framebuffer readback.
- `getString` / `getStringi` / `getInteger` / `version` / `extensions`.
- `compile_program(vs, fs, extra_stages=())` - compile and link a program.
- `framebuffer(fbo)` - a `with` block that binds `fbo`, then rebinds whatever
  was bound before it on exit. It does not bind zero. `colour_buffer_name()`
  and `draw_framebuffer()` return what this context draws into.
- `get_checked(fn, args, count, dtype)` - call a `glGet*v` getter with an
  oversized buffer filled with canary values, and assert it wrote no more than
  `count` elements. Use this when the output size is uncertain. A buffer that is
  too small overruns the heap without an error, and the crash comes much later
  in unrelated code.
- `require_entrypoint(fn, name)` - skip if an ES-only EXT command has the same
  name as a desktop-GL command and PyOpenGL cached a null for it under the
  shared egl process.
- `exercise(reason)` / `tolerate_glerror(*codes)` - tolerate a documented,
  expected GLError (a known driver gap) for a narrow block. They are not a
  general workaround; the surrounding calls must still succeed. `exercise`
  takes a required reason naming the error it forgives and why. Usually the
  reason is that a driver advertises an extension without serving every entry
  point in it. It tolerates only `GL_INVALID_ENUM`, `GL_INVALID_VALUE` and
  `GL_INVALID_OPERATION`, the errors a driver raises for an unsupported call.
  `GL_OUT_OF_MEMORY`, `GL_INVALID_FRAMEBUFFER_OPERATION` and `GL_CONTEXT_LOST`
  mean the call failed or the case set up its context wrongly. They are never
  a known gap, so they propagate. Every forgiven error is counted, and the run
  prints the tally. That number shows how much of a run proved only that entry
  points are reachable, as opposed to proving their behaviour. Prefer
  `tolerate_glerror` where the error code is known exactly. Use a plain call
  with `check_error` where the driver should succeed.

## Windowing backends - `TEST_WINDOWING`

`pick_backend()` selects the backend from the `TEST_WINDOWING` environment
variable (default: glfw, then pygame, then tk). `backends.headless_for()`
returns which of the windowless backends a platform has. Use it for a case that
needs to run without a window but does not need a specific backend.

| `TEST_WINDOWING` | Backend | Notes |
|------------------|---------|-------|
| `glfw` (default) | on-screen glfw window | desktop GPU, or llvmpipe under a software compositor |
| `pygame`         | on-screen pygame/SDL window | same |
| `tk`             | on-screen Tk window (`glcontext_tk.py`) | Uses `OpenGL.Tk.GLFrame`, which creates its own core-profile context on the window Tk provides. It needs no extra package. On Linux it needs an X display, because Tk has no Wayland backend. On macOS it needs a window server (`tests/report_tk_aqua.py` reports whether a machine has one). |
| `egl`            | headless EGL device (`glcontext_egl.py`) | Renders directly on a GPU with no window system. Use it for CI and containers where the compositor renders in software. It forces `PYOPENGL_PLATFORM=egl`. ES and GL both work through an offscreen pbuffer. |
| `cgl`            | headless macOS context (`glcontext_cgl.py`) | CGL is the lowest-level OpenGL interface on macOS. NSGL (the `NSOpenGLContext` Cocoa API) and AGL (the older Carbon API) are built on it. CGL can create a context without a window server, which is the situation on a macOS CI runner. An offscreen CGL context has no default framebuffer, so the backend binds a framebuffer object of the requested size. No OpenGL-ES, and no compatibility profile above 2.1. `TEST_CGL_RENDERER` pins the renderer kind. |
| `osmesa`         | software, into an array the suite owns (`glcontext_osmesa.py`) | OSMesa is Mesa's off-screen interface. It is a PyOpenGL platform in its own right, not a driver behind GLX or EGL, so it forces `PYOPENGL_PLATFORM=osmesa`. It needs no display server and no `/dev/dri`, only `libOSMesa`, so it runs where no other backend can. It always renders in software. The array it renders into is the default framebuffer, so no framebuffer object is needed. Desktop GL only; an OpenGL-ES case skips. `OpenGL.osmesa.offscreen` implements it, and a program can use it to get a headless context of its own. |
| `wgl`            | headless Windows pbuffer (`glcontext_wgl.py`) | A pbuffer is a drawable that the display driver allocates in its own memory, with no window. It is the default framebuffer, so no framebuffer object is needed. The backend requests it double-buffered, because the suite is written for a window and the GL 1.x and 2.0 state cases call `glDrawBuffer(GL_BACK)`. No OpenGL-ES, because WGL provides none. `python tests/check_wgl_offscreen.py` reports whether a machine can serve it, and names the missing WGL extensions if not. Windows' own GDI Generic fallback has none of them. |

On a Wayland session with the NVIDIA driver, `glReadPixels` from an on-screen
window returns black regardless of what was drawn. The cases that read back what
a widget rendered fail there and pass under `xvfb-run`. The Linux CI already
runs the whole suite under `xvfb-run -a`. A developer on such a session should
do the same for the windowed suites. Thirteen check scripts run only under X,
so without `xvfb-run` only CI runs them.

The GLUT and Xlib scripts decide whether they can run from `DISPLAY`, not from
the login session type, because `xvfb-run` changes `DISPLAY` and not the
session. XWayland is refused. It is an X server, so the display opens, but GLUT
support for it is poor: a window either does not appear or does not respond.
XWayland identifies itself by advertising the `XWAYLAND` extension.

On an NVIDIA driver, about one run in ten dies with SIGSEGV while a context is
torn down. The faulting frame is inside `libnvidia-eglcore`, reached through
`eglDestroyContext`. Under `glfw` the path is `glfwDestroyWindow` →
`destroyContextEGL`, which calls `eglDestroyContext`. No frame between the
fault and the call belongs to PyOpenGL. `gdb -q -batch -ex run -ex 'bt 40'
--args python -m pytest …` catches it within a few attempts. Mesa and the macOS
backends do not show it, so CI does not either.

On macOS, a headless CGL context has no drawable, and framebuffer zero belongs
to the drawable. So `glBindFramebuffer(GL_FRAMEBUFFER, 0)`, the usual way to
finish with a framebuffer object, leaves the context with no complete
framebuffer to draw into. The next call that needs a framebuffer then raises
`GL_INVALID_FRAMEBUFFER_OPERATION`, and the error does not point back to the
unbind that caused it. Use `with self.framebuffer(fbo):`, which restores
whatever was bound before. Where a case must bind by hand, read
`self.draw_framebuffer()` before the bind and restore that value, not zero.

A resolved entry point is not an implemented feature. macOS exports every entry
point from its framework, whatever the current context implements. So
`bool(glGenVertexArrays)` is true on the 2.1 legacy profile, which uses the
fixed-function pipeline, and the call then raises `GL_INVALID_OPERATION`. By
then the guard has already decided the feature exists. Check the context with
`require_feature(...)`, `require_extension(...)` or `require_version(...)`.
Drivers that resolve only what they implement hide this problem entirely.

Several fixtures and child scripts open their own window, either for a hint
`pick_backend` does not accept or for a question that is fixed once per process.
These have one trap. When `glfw.create_window` cannot make a window, it returns
a NULL `LP__GLFWwindow`, which is falsy but is not `None`. So
`if window is None` treats a failure as a window, and every call through the
missing context returns zero. Write `if not window`, or use
`glcontext.window_was_made(window)`, which also reports why it failed.

Other settings: `TEST_VISIBLE=0` runs with hidden windows and no dwell;
`TEST_DWELL=<seconds>` sets the per-test on-screen pause; `TEST_EGL_DEVICE=<n>`
pins a specific EGL device; `TEST_CHECK_TIMEOUT=<seconds>` limits one check
script (120 by default), and the per-test `timeout` in `pyproject.toml` limits
everything else. Under the `egl` backend, the legacy root-level windowed tests
skip, because a window cannot be combined with the egl-device platform.

## Adding a test

1. Pick the suite (`gl/`, `gles/`, `glu/`) and a unique `test_*.py` basename.
2. Subclass the suite's base case; set `profile` / `gl_version` / `api` etc. for
   the context you need.
3. Call `require_extension(...)` / `require_version(...)` first, so unsupported
   platforms skip cleanly.
4. Make real calls. Create the objects (buffers, textures, programs,
   framebuffers), pass valid arguments, and end with `self.check_error(...)`.
   Assert real results (pixels, returned values) where you can.
5. For every getter the feature adds, query it with a correctly-sized buffer (or
   `get_checked`) and check the result is sane.
6. Build array data with `from arraycompat import np` so the test also runs in
   the no-numpy environments.
7. If a specific entry point cannot succeed here (external interop, multi-GPU, a
   window-system-only path), call `skipTest('<why>')`. Do not mention its name
   anywhere the coverage scanner would count it.
8. Import `OpenGL.EGL` only behind
   `pytest.importorskip('OpenGL.EGL', exc_type=ImportError)`. EGL ships with the
   graphics driver, and macOS has none. The binding raises `ImportError` naming
   the missing library on purpose, because `try: from OpenGL import EGL` is how
   a program tests whether the machine has EGL. Since pytest 8.2,
   `importorskip` catches only `ModuleNotFoundError`. Without `exc_type`, the
   import becomes a collection error, and pytest abandons the whole run instead
   of skipping one module. Importing `glcontext_egl` has the same effect,
   because it is the EGL backend. No other PyOpenGL subpackage behaves this way.
   `OpenGL.GLUT` and the others import without their library and raise
   `NullFunctionError` when called. `tests/harness/test_collects_without_egl.py`
   collects the suite with EGL hidden, and that test catches this mistake.
9. Back every interface block that a draw or dispatch will execute. An active
   uniform block, shader storage block or atomic counter buffer needs a buffer
   object bound to its binding point. Without one, the results of shader
   execution are undefined, and the specification lets a driver interrupt or
   terminate (GL 4.6 core, 7.6.3 and 7.8). Drivers that use that permission
   segfault; `glGetError` reports nothing. Tolerant drivers report nothing
   either, so a case with an unbacked block passes everywhere until it reaches
   a strict driver. Either bind a buffer for the block or use a program without
   one.

Run the test on a real GPU (`TEST_WINDOWING=egl` in a container, or windowed on
the host) and on the software path, and confirm it skips where it should.

## Measuring what a run executed

`coverage.py` is configured in `pyproject.toml` with `parallel` and
`patch = subprocess`, because several suites run their checks in a fresh
interpreter. The platform plugins are covered almost entirely by child
processes, so measuring only the parent would report them as unexecuted.

```
python -m coverage run -m pytest tests/
python -m coverage combine
python -m coverage report -m OpenGL/raw/osmesa/mesa.py
```

The report excludes generated `def name(...): pass` declarations. The decorator
replaces the body with a ctypes function, so that line never runs however often
the entry point is called. Counting it as a miss would hide the lines that are
actually unreached.

Line coverage is stricter than the entry-point counters below. The counters
report which entry points a suite names. Line coverage reports which lines a run
executed. A case can name a call in a skip reason, or after an assertion it
never gets past.

## Coverage tooling

`gl/gl_coverage.py`, `gles/es_coverage.py`, and `glu/glu_coverage.py` count the
`gl*` entry points defined per version and per supported extension, and report
which ones the tests call. `supported_extensions.json` (an `extensions` list
and a `with_funcs` map) defines the set being measured. When you add real
coverage for an extension, add it to `with_funcs` with its function list so the
report includes it. List only the functions you actually exercise, so partial
coverage shows as partial.

```
python gl/gl_coverage.py           # summary
python gl/gl_coverage.py --ext     # per-extension
python gl/gl_coverage.py --ext-uncovered
```

`gl/enum_age_audit.py` reports enums a case uses that are newer than the
context it requests. A 4.3 enum in a 3.3 context is `GL_INVALID_ENUM`. Mesa
accepts it and macOS does not, so the case passes on Mesa and fails on macOS.
The audit exits non-zero only for a use outside a block that tolerates the
error or checks the context version first.

```
python gl/enum_age_audit.py
```

## The static gates

`gates/` holds the checks a parser can answer about the source tree. They need
no GL, no driver and no platform. They run in a couple of seconds and cover
every file at once. They are the only checks that read the Windows and macOS
parts of this package on a Linux machine. Each gate covers a class of defect
this repository has had. [plans/STATIC-GATES.md](../plans/STATIC-GATES.md)
records where each came from, and lists the classes a parser cannot detect.

| Gate | What it refuses |
| --- | --- |
| `test_the_suite_can_fail.py` | `pytest.raises(Exception)`, a fixture under `@staticmethod`, an optional import at module scope, a named script that is not there, a blanket `tolerate_glerror()`, a skip with no reason |
| `test_sibling_apis_agree.py` | a per-API module that has drifted from its siblings, and an `_ErrorChecker` built without checking whether error checking is on |
| `test_foreign_functions_are_declared.py` | a ctypes call with no `argtypes`/`restype` |
| `test_configuration_is_one_story.py` | a flag the environment cannot set, or one the docstring does not introduce |
| `test_declared_gates_run.py` | a tox factor, a marker or a test path nothing runs |
| `test_parallel_implementations_agree.py` | a format handler that implements less than the interface, or a registry that supports one implementation's lookups and not the other's |
| `test_glget_sizes_agree.py` | the two shipped glGet size tables disagreeing |
| `test_requirements_files_resolve.py` | a `-r` or `-c` naming a file that is not there, or a pair of requirements files including each other |

Three more gates use external tools, so they run from tox:

```
tox -e floor              # vermin: nothing above the requires-python floor
tox -e possiblyundefined  # mypy: a name that may be unbound where it is read
tox -e errorpaths         # the suite under coverage, then the error paths
                          # nothing entered -- see src/error-paths-unentered.txt
```

`errorpaths` keeps a record file. An `except` clause or a `finally` block that
no case enters is code no test runs. Handlers that raise a new error instead
of reporting the original have all been found in such code. The record lists
what this configuration does not reach today. Any new entry fails the gate, and
the list should shrink over time. The gate reads the coverage data, not a
coverage report, so `# pragma: no cover` on a clause has no effect here. The
pragma controls what a report omits, and the gate reads the tracer's data.

## Running

```
# whole matrix (CPython 3.9 to 3.15 and PyPy 3.10 and 3.11, × numpy × accelerate), windowed:
uv run --with tox,tox-uv tox

# one configuration, headless on the real GPU:
TEST_WINDOWING=egl python -m pytest -q tests/gl tests/gles tests/glu

# software / windowed:
TEST_VISIBLE=0 python -m pytest -q tests/
```

### Running in parallel

`pytest-xdist` roughly halves the run time: 67s to 35s on four workers, with
every case giving the same outcome as a serial run. Two options are required:

```
python -m pytest -q -n 4 --dist loadfile --max-worker-restart=0
```

Use four workers, not `-n logical`. The workers share one renderer, and twenty
of them on a large machine fail cases that pass with four.

`--dist loadfile` keeps each module in one process. A test class creates its
context in `setUp`, so the cases of one class must run in one process to share
it. The default `--dist load` sends single cases to whichever worker is free.

`--max-worker-restart=0` fails the run when a worker dies, instead of replacing
the worker. With a replaced worker, the controller waits on a queue that will
never drain. The run stops progressing and reports nothing, so a crash looks
like a hang.

Do not run in parallel on the NVIDIA driver. With several processes rendering
on the device at once, one worker's rendering stops partway through a run and
does not recover. From then on, every case in that process that reads a pixel
gets `(0, 0, 0, 0)` with `GL_NO_ERROR`, from draws the driver accepts. This
includes contexts created afterwards. The failing cases are whatever that worker
had left to run, so the set differs every time. It happens in roughly one run in
eight. Calling `glFinish` before the read does not change it. Neither a serial
run nor a run limited to `tests/gles` reproduces it. A reset context behaves the
same way, so when a frame reads back empty, `assert_pixel` calls
`glGetGraphicsResetStatus` and includes the result in the failure. When caught,
it reported no reset, so the cause is still unknown. The teardown SIGSEGV
described above is the other symptom of the same configuration. Mesa shows
neither. Ten consecutive four-worker runs on the software device matched each
other and a serial run. For that reason CI runs in parallel, and this warning
applies to a developer's NVIDIA GPU.

## Check scripts

A check script is a program, not a test case. It opens a window, runs a
toolkit's main loop, or answers a question that can only be asked once per
process. `test_checks.py` runs each script in a separate process. The scripts
run in the default windowed mode even when the outer run uses the headless
`egl` backend.

The runner runs every `check_*.py` beside `test_checks.py`. It finds them by
glob and keeps no list, so adding a script means adding a file, and every
script is run. A program that reports facts instead of checking them is named
`report_*` and is not collected. `report_cgl_context.py` and
`report_egl_device_enumeration.py` are examples; CI runs both to print what the
machine has.

A script states its requirements in a `# requires:` line within its first forty
lines:

```python
#! /usr/bin/env python
# requires: glut numpy
```

The runner reads this line from the file without importing it, since whether
the script imports at all is part of what running it tests. The allowed words
are `numpy`, `window-server`, `xlib`, `glx` and `glut`. Any other word fails
the run, so a typo cannot silently turn into a check that never runs.

A script that uses `checkutils`, `arraycompat`, `testdecorator` or any other of
the suite's own modules imports `suitepath` first:

```python
import suitepath  # noqa: F401  -- the suite's modules, by bare name
import checkutils
```

`test_checks.py` puts `tests/` in each child's `PYTHONPATH`, so those bare names
resolve under the runner either way. When a script is run as a file, for
example `python tests/checks/check_osmesa.py`, `sys.path` starts at
`tests/checks` instead, one directory below those modules. That is how a
platform is tested by hand, and how CI reports the renderer before the OSMesa
row.

A script that cannot run on the current machine (a driver that refuses the
context, an SDL that cannot open a display) reports this at run time by exiting
with code 77. Use `checkutils.skip(reason)`, or
`checkutils.require('some.module')` for a dependency. The harness reports either as a skip. On success a script
prints `OK`. A script that dies on an import or a null entry point prints
nothing. The harness treats no output as a failure, because that is how it
distinguishes a working check from a broken one.

A script still running after `TEST_CHECK_TIMEOUT` seconds (120 by default) is
killed and the case fails. Before the kill, `nativestacks.of(pid)` attaches the
platform's debugger (`cdb` on Windows, `lldb` on macOS, `gdb` elsewhere). The
failure then includes every thread's native stack, or the debugger's reason for
not providing one. Linux with `ptrace_scope` 1 refuses the attach.

A GLUT check script has to handle two points where classic GLUT (the macOS
version) differs from freeglut:

- Context creation - `glutInitContextVersion`, `glutInitContextFlags`,
  `glutInitContextProfile` and `glutSetOption` exist only in freeglut. A script
  that needs them checks `if not glutInitContextVersion` and skips.
- Leaving the main loop - classic GLUT has no way to exit `glutMainLoop`, which
  is why freeglut added `glutLeaveMainLoop`. A script whose callback ends the
  run must fall back to `os._exit(0)` where that entry point is absent.
  Otherwise it spins until the harness times it out. It has already printed
  `OK` by then, so the log shows success and the run records a failure.
