# PyOpenGL 4.0 release notes

What changed since the 3.x series. The current development version is
`4.0.0a5`.

## C dispatch layer in PyOpenGL_accelerate

- A C dispatch layer, generated from the Khronos registry, ships in
  `PyOpenGL_accelerate`. It covers 4,859 of PyOpenGL's 4,880 bindings across
  GL, GLES 1/2/3, GLSC2, GLX, WGL and EGL.
- Measured on an RTX 3060 Ti with CPython 3.12: `glBindTexture` 407 ns → 58 ns,
  `glUniform1f` 382 ns → 51 ns, `glUniformMatrix4fv` with a numpy 4×4
  1184 ns → 106 ns. Roughly seven times faster per call, eleven times for a
  call that passes an array.
- What a program gains depends on how much of its frame goes on dispatch.
  Measured uplift on optimised PyOpenGL applications is about 5%; a call-heavy
  or immediate-mode program approaches the ratios above.
- Both implementations are the same bindings with the same semantics, and the
  test suite runs under both. `pip install PyOpenGL` on its own still gives the
  pure-Python ctypes implementation on every platform and every interpreter.
  `PYOPENGL_DISPATCH=ctypes` selects it where the extension is installed, and
  `OpenGL.dispatch.status()` reports which one you got and, if it is not the
  one you asked for, why.

## Per-context entry-point tables

- Under ctypes, whichever context resolves an entry point first determines the
  binding for the whole process. Where two contexts differ — a discrete-GPU
  context beside a software one, core beside compatibility, GLES beside desktop
  GL — that is wrong for one of them.
- Under the C implementation each context has its own table, so `bool(glFoo)`
  and `glInitXxx()` answer for the context that is current, and a binding held
  across a context switch still dispatches correctly.
- `OpenGL.dispatch.make_current()` and `forget_context()` are there for a
  program that wants to be exact about switches; `PYOPENGL_CONTEXT_TRACKING=verify`
  asks the driver on every call instead, with nothing to change in the program.

## Error checking: `GL_KHR_debug`, and one query per API

- Where the context offers `GL_KHR_debug`, PyOpenGL uses it: checking costs
  0.8 ns rather than an 11 ns `glGetError` round trip, and the `GLError` carries
  the driver's own `description` of what was wrong. It is on by default and can
  be turned off per process or per context.
- GL, GLES, EGL and the window-system APIs are each asked for errors their own
  way. A single `glGetError` answering for all of them reported none of EGL's
  errors and could attribute a stale GL error to an EGL call.
- `OpenGL.dispatch.set_error_checking()` changes checking at run time, for one
  entry point or for all of them, which the import-time flag could not do.

## Memory safety and crash fixes

- Several `glGet` output sizes were recorded short, so the driver wrote past the
  end of the array PyOpenGL had allocated. Nothing raised; the damage surfaced
  later as an unrelated crash. `GL_PATCH_DEFAULT_INNER_LEVEL`,
  `GL_PATCH_DEFAULT_OUTER_LEVEL`, the NV coverage modes and a bounding-box
  query are corrected, and the whole shipped size table is now checked against
  the live driver on every test run.
- Fixed: segfaults on exit under GLFW; VBO deletion attempted with no current
  context; and `OpenGL.GL.ARB.vertex_array_object` wrapping the output of
  `glGenVertexArrays` twice, once from the generator and once by hand.
- A `VBO` garbage-collected while a different context was current deleted that
  context's buffer of the same number -- every context numbers its buffers from
  1 -- and the other context's next draw came up empty. A `VBO` now deletes its
  buffer only in the context that made it, recognised through
  `OpenGL.dispatch.context_identity()` even where the driver has since given
  that context's handle to a new one, and otherwise leaves the buffer to its
  context. A program that holds GL names of its own can do the same.
- Output arrays that are too short for what the call was told to write are
  refused rather than handed to the driver.

## Binding fixes

- `gluUnproject4` had the wrong signature; GLU quadrics, NURBS and the
  tessellator had defects the new suites exposed.
- `glGetTexImageCompressed` ignored the level it was given.
- `glDrawBuffersEXT` was being wrapped to `glDrawBuffers`.
- Constants larger than `sys.maxint` converted incorrectly.
- GLES image functions had wrong sizing, and now have size checks.
- `int64` and `uint64` array element types are supported.
- Extension availability is cached per context rather than re-queried.
- A command adopted into core is exported as core rather than as its extension.
- Modules that could not be imported at all now import, and the type names their
  declarations reach for are declared: `OpenGL.GLSC2` in its entirety, which had
  neither `raw/GLSC2/_types.py` nor `raw/GLSC2/_errors.py`;
  `OpenGL.GLU.EXT.nurbs_tessellator`, which read its constants from a module
  that does not hold them; `OpenGL.GLES3.vboimplementation`, which named an
  `OpenGL.GLES3.OES` package that does not exist; `OpenGL.GLX.NV.video_capture`
  and the `OpenGL.GLX.SGIX` modules, whose `Colormap`, `Status`,
  `GLXVideoDeviceNV`, `DMparams`, `DMbuffer`, `VLServer`, `VLPath` and `VLNode`
  were undeclared; and the GL extensions declared with `GLeglClientBufferEXT` or
  `GLVULKANPROCNV`. The suite imports every shipped module and evaluates every
  declaration in the shipped tables.
- `glGenVertexArrays(1)` and the other entry points that allocate their own
  output ask the array handler for a length rather than a shape. The ctypes
  handlers took only a sequence, so without numpy installed those calls raised
  `TypeError` before reaching the driver. Both take a length or a shape now, as
  the numpy handler does.
- `FormatHandler.typeLookup` answers which handler a data type resolved to, and
  raised `TypeError: 'HandlerRegistry' object is not subscriptable` wherever
  PyOpenGL_accelerate was installed. The pure-Python registry is a dict
  subclass; the compiled one offered only `__setitem__`. It answers a lookup by
  type now, and a type nothing handles raises the documented `KeyError`.
- `FormatHandler.dimensions` declared a `typeCode` parameter no handler accepts
  and no caller passes, so the interface a third party writing a handler reads
  described an argument every implementation would have refused.

## Type stubs and `py.typed`

- 1,310 `.pyi` stubs and a `py.typed` marker, carrying the constants, the entry
  points and their signatures. The generated modules fill their namespaces from
  declaration tables at import, so the stubs are what an editor's completion and
  a type checker read.
- GLU, GLUT and GLE have stubs as well. None of the three is a Khronos API, so
  each is written by hand and the registry-driven generator has nothing to say
  about them; their stubs are emitted from the declarations themselves, 354 GLUT
  names, 219 GLU and 52 GLE.
- Docstrings state GL types in the registry's own names, so
  `glBindTexture(target: GLenum, texture: GLuint) -> None` rather than
  `glBindTexture(target, texture) -> None`.
- The entry points `OpenGL.GL` exports through a wrapper of its own are
  described as the wrapper takes them, not as the C function does.
  `glDeleteTextures(textures)` reads the count from the array it is given, and
  the stub offers that call alongside the `(n, textures)` pair; `glMap1d`,
  `glMap1f`, `glMap2d` and `glMap2f` take the points array without the strides,
  and the stub offers that call alone, since it is the only one they accept.
  `glCallLists` and `glAreTexturesResident` gain their Pythonic forms the same
  way. GLU and GLE have many of these:
  `gleExtrusion(contour, cont_normal, up, point_array, color_array)` takes five
  arguments where the C entry point takes seven, because both counts are read
  off the arrays passed with them, and `gluProject(objX, objY, objZ)` fills in
  the three matrices from the current GL state. The stub says what each wrapper
  takes.
- The stubs are checked, and a defect in them fails the build. `mypy` runs over
  all 1,310 of them in CI, and the suite holds each one against the object it
  describes — including holding every GLU, GLUT and GLE entry point to the
  number of arguments its Python form actually takes. What the gate covers, and
  why the package's own source is not in it, is in `[tool.mypy]` in
  `pyproject.toml`.
- A `mypy` run over a program that imports PyOpenGL reads the stubs, and reports
  nothing from inside the package's own modules.

## Configuration flags

The flags `OpenGL/__init__.py` documents are read from the environment as
`PYOPENGL_<NAME>`. CI runs the whole suite with `PYOPENGL_ERROR_ON_COPY=1`, with
`PYOPENGL_ARRAY_SIZE_CHECKING=0` and with `PYOPENGL_SIZE_1_ARRAY_UNPACK=0`, as
well as with the defaults.

- `SIZE_1_ARRAY_UNPACK` reads `PYOPENGL_SIZE_1_ARRAY_UNPACK`. It was the one
  flag of the set that read no environment variable, so setting the variable did
  nothing and only assigning the name before the first import had any effect.
- With `PYOPENGL_SIZE_1_ARRAY_UNPACK=0`, `vbo.VBO` could not create a buffer: it
  read what `glGenBuffers(1)` returned with `long()`, which cannot read a
  one-element array. It reads through `OpenGL._scalar.as_int`, which takes
  either shape.
- With `PYOPENGL_ERROR_ON_COPY=1`, a parameter declared as a bare pointer —
  `GLintptr` and `GLsizeiptr`, `GL_NV_vdpau_interop`'s surface arrays among them
  — got no converter on the ctypes path, so ctypes refused every array passed to
  it, the one whose memory the call wanted included. Such a parameter resolves
  to the array class for its element type, and that class refuses a copy the
  same way, so the flag still means what it did.
- With `PYOPENGL_ERROR_ON_COPY=1`, `VBO.delete()` could not delete a buffer: it
  passed the buffer name as an int, which the wrapper copies into an array. It
  builds a `GLuint`, as the deleter that runs at collection already did.
- `ALLOW_NUMPY_SCALARS` has no effect from 4.0, and reading or setting it is
  still allowed. A numpy integer scalar is accepted wherever an integer is
  wanted with the flag or without it, because ctypes converts through
  `__index__`. What the flag added beyond that was a retry through `int()`,
  which also accepted a numpy float and truncated it silently.

## Context creation

- **Headless EGL.** `OpenGL.EGL.devices` reports the EGL devices a system
  offers, what each driver calls itself, and which of them rasterise on the CPU,
  along with the handle `eglGetPlatformDisplayEXT` wants. Getting there
  otherwise takes three extensions and a pair of string queries.
- **macOS without a window server.** `OpenGL.CGL` creates a context with no
  window and no window server, with `headless_context()` and `OffscreenTarget`
  for drawing into.
- **Tkinter.** `OpenGL.Tk.GLFrame` is an ordinary `tkinter.Frame` that owns an
  OpenGL context on its own native window. It is an OpenGL 3.3 core profile by
  default, so shaders and vertex array objects are available, and it needs
  nothing installed beyond Python — the Togl-based widgets keep their names and
  no longer need Togl.
- **Wayland.** On Linux the GLX/EGL choice is a context-level probe, so GLUT
  runs under Wayland and XWayland.
- **Windows.** ES and EGL are not part of Windows, and ANGLE is how a machine
  has either. `PYOPENGL_PLATFORM=angle` binds them to an installed ANGLE, and
  `PYOPENGL_ANGLE_PATH` says which copy to use, since ANGLE travels inside
  applications rather than being installed system-wide and a machine may hold
  several. That platform supplies ES and no desktop GL, because that is what
  ANGLE has.
- **Windows, without selecting a platform.** The default one looks for
  `libEGL`, `libGLESv1_CM` and `libGLESv2` — the names an ANGLE or Mesa build
  installs beside the application that ships it — as well as the bare `EGL`,
  `GLESv1_CM` and `GLESv2` an SDK or driver vendor uses. `OpenGL.GLES1`,
  `OpenGL.GLES2` and `OpenGL.GLES3` import whether or not a machine has one, and
  a call with no entry point under it raises `NullFunctionError` naming the
  function. The WGL calls that live in `gdi32` resolve there rather than being
  looked for in `opengl32` alone.
- **Windows loads its own OpenGL.** `opengl32` and `glu32` go to the loader by
  name, so Windows' search order answers and the system directory is reached
  before `PATH`. `System32\opengl32.dll` is a trampoline to whatever the
  graphics driver installed; looking on `PATH` first meant a conda environment,
  which puts a Mesa `opengl32.dll` ahead of it, rendered in software with
  nothing saying so.
- **`NullFunctionError` says which of three things happened.** The message was
  the same whether the library was not installed, no context had been created
  yet, or the driver genuinely lacked the entry point — three different
  problems with three different answers, described as one. Where the library
  is absent it now names the library and where to get it, and says that every
  entry point in it is undefined rather than sending the reader to check the
  one name they happened to call. Where no context is current it says so —
  above GL 1.1 an address comes from the context, so on Windows, where
  `wglGetProcAddress` needs a current one, that is the usual reason a call
  like `glGenVertexArrays` is undefined on a machine whose driver has it.
- **A GLUT you installed is found by its own name.** The Windows platform asks
  for `freeglut` and `glut32` — what the official freeglut binaries, MSYS2,
  vcpkg and the original GLUT install — before the builds we ship, and a
  library of the wrong architecture no longer stops the search at the first
  name.

## Packaging and freezing

- **The Windows GLUT and GLE builds are an optional download.** They shipped
  inside every wheel, on every platform, so a Linux server rendering through
  EGL fetched twelve Windows libraries it could never load — and a scanner
  objecting to a decade-old vendored binary quarantined PyOpenGL itself for
  users who never wanted GLUT (#164). They are `PyOpenGL-glut-binaries` now:

  ```
  pip install PyOpenGL[glut]
  ```

  **A Windows program that calls `glutInit()` needs that extra**, where a
  plain `pip install PyOpenGL` used to be enough. Nothing else changes: a
  freeglut the system provides still wins over the shipped build, and where
  neither is present the error names the command to run rather than reporting
  an undefined function. One download carries GLE as well.
- A PyInstaller hook ships in the box and PyInstaller finds it by itself. It
  reports the modules PyOpenGL's plug-in registries would import — including
  plug-ins added by other packages — and the Windows GLUT and GLE libraries,
  from wherever the running loader would find them. An application frozen on a
  host without the extra is frozen without GLUT. For any other freezer,
  `OpenGL.plugins.registered_modules()` is the same answer.
- Building `PyOpenGL_accelerate` from a source tree drops the generated C where
  the Cython or the numpy that wrote it has changed. Those modules
  `cimport numpy`, and `cythonize` decides by timestamp whether to write the C
  again, so C left over from an earlier build can otherwise be compiled against
  numpy headers it no longer matches.

## Testing and CI

- Around 1,500 test cases across GL, GLU, GLES and EGL, run against whatever
  driver is present rather than a fixed list, with GLFW, pygame, Tk, EGL and CGL
  backends. `TEST_VISIBLE=false` runs much of it without opening windows.
- Coverage is measured against what the machine in front of the suite actually
  exports, not against the registry: 1,052 of 1,052 commands for the GL
  versions, and of the 1,910 entry points a reference driver provides, the five
  not called by anything are `GL_EXT_semaphore` calls that need a semaphore
  imported from Vulkan or Direct3D.
- CI runs on every push, on three platforms and their software renderers: Linux
  on llvmpipe through an EGL device and through OSMesa, Windows on Mesa through
  a WGL pbuffer, and macOS through CGL on macOS 13, 14 and 15 — the first
  Intel, the other two Apple Silicon. A Linux cell runs on arm64, and the
  `PyOpenGL_accelerate` wheels are built for aarch64 on an arm64 machine rather
  than under emulation.
- The interpreter sweep runs 3.9, 3.10, 3.12, 3.13 and 3.14. 3.9 is the
  `requires-python` floor, and the suite is what evaluates it: mypy refuses
  `--python-version=3.9`, and numpy's own stubs need 3.12 to parse.
- Further cells cover numpy absent, `accelerate` built with the C entry points
  selected, `accelerate` built with the ctypes entry points selected,
  `accelerate` built and then declined with `PYOPENGL_USE_ACCELERATE=0`, and the
  configuration flags above. A run that asks for the C entry points where the
  extension is not installed is refused rather than falling back to ctypes.
- The stub typecheck is a cell of the matrix, so `tox` runs it.
- A weekly job pulls the Khronos registry, regenerates the bindings and opens a
  pull request when anything changed, so a new entry point is not discovered by
  somebody trying to call it.

## Compatibility

- **Python 3.9 or newer, and numpy 2.x.** numpy remains optional; the suite runs
  and is tested without it.
- **`PyOpenGL_accelerate` must match the PyOpenGL it was generated from.** The
  two are released together and its dispatch tables are generated from that
  PyOpenGL, so install the pair in one command.
- **PyPy runs the ctypes bindings.** `PyOpenGL_accelerate` is built for CPython,
  so neither the C dispatch layer nor the Cython accelerators are available
  there, and `OpenGL.dispatch.status()` says which implementation is running and
  why. The buffer-protocol array handler reads CPython's C API through
  `ctypes.pythonapi`, which PyPy does not have, so a `memoryview` has no array
  handler there, reported as a missing handler rather than as an error from
  inside the call that passed one.
- The platform module is now named `linux` rather than `unix`.
- Licence metadata is in SPDX form; the licence itself is unchanged BSD-3-Clause.

## Documentation

- [The C dispatch layer](https://mcfletch.github.io/pyopengl/documentation/c-dispatch.html)
  — what it covers, what differs, contexts, arrays, strings and error checking.
- [EGL devices](https://mcfletch.github.io/pyopengl/documentation/egl-devices.html)
- [Offscreen OpenGL on macOS](https://mcfletch.github.io/pyopengl/documentation/cgl-offscreen.html)
- [OpenGL in a Tkinter widget](https://mcfletch.github.io/pyopengl/documentation/tk-widget.html)
- [Offscreen OpenGL on Windows](https://mcfletch.github.io/pyopengl/documentation/wgl-offscreen.html)
- [OpenGL ES through ANGLE](https://mcfletch.github.io/pyopengl/documentation/angle-gles.html)
