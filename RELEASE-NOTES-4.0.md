# PyOpenGL 4.0 release notes

What changed since the 3.x series. The current development version is
`4.0.0a4`.

## Calls are much faster, and your code does not change

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

## Each context holds its own function pointers

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

## Error checking costs less and tells you more

- Where the context offers `GL_KHR_debug`, PyOpenGL uses it: checking costs
  0.8 ns rather than an 11 ns `glGetError` round trip, and the `GLError` carries
  the driver's own `description` of what was wrong. It is on by default and can
  be turned off per process or per context.
- GL, GLES, EGL and the window-system APIs are each asked for errors their own
  way. A single `glGetError` answering for all of them reported none of EGL's
  errors and could attribute a stale GL error to an EGL call.
- `OpenGL.dispatch.set_error_checking()` changes checking at run time, for one
  entry point or for all of them, which the import-time flag could not do.

## Memory-safety and crash fixes

- Several `glGet` output sizes were recorded short, so the driver wrote past the
  end of the array PyOpenGL had allocated. Nothing raised; the damage surfaced
  later as an unrelated crash. `GL_PATCH_DEFAULT_INNER_LEVEL`,
  `GL_PATCH_DEFAULT_OUTER_LEVEL`, the NV coverage modes and a bounding-box
  query are corrected, and the whole shipped size table is now checked against
  the live driver on every test run.
- Fixed: segfaults on exit under GLFW; VBO deletion attempted with no current
  context; a crash when EGL device enumeration met a device that would not
  initialise; a doubly-wrapped entry point that crashed `vertex_array_object`
  on import; and a software/hardware renderer contradiction that dumped core.
- Output arrays that are too short for what the call was told to write are
  refused rather than handed to the driver.

## Binding bugs found by a much larger test suite

- `gluUnproject4` had the wrong signature; GLU quadrics, NURBS and the
  tessellator had defects the new suites exposed.
- `glGetTexImageCompressed` ignored the level it was given.
- `glDrawBuffersEXT` was being wrapped to `glDrawBuffers`.
- Constants larger than `sys.maxint` converted incorrectly.
- GLES image functions had wrong sizing, and now have size checks.
- `int64` and `uint64` array element types are supported.
- Extension availability is cached per context rather than re-queried.
- A command adopted into core is exported as core rather than as its extension.

## Editors and type checkers can see the API

- 1,307 `.pyi` stubs and a `py.typed` marker. The generated modules fill their
  namespaces from declaration tables at import, so nothing reading the source
  could see them: completion offered nothing and a checker typed every name as
  `Any`. The stubs carry the constants, the entry points and their signatures.
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
  way.
- The stubs are checked, and a defect in them fails the build. `mypy` runs over
  all 1,307 of them in CI, and the suite holds each one against the object it
  describes. What the gate covers, and why the package's own source is not in
  it, is in `[tool.mypy]` in `pyproject.toml`.
- Fourteen modules that could not be imported at all now import:
  `OpenGL.GLSC2` in its entirety, which had no `raw/GLSC2/_types.py`;
  `OpenGL.GLU.EXT.nurbs_tessellator`, which read its constants from a module
  that does not hold them; `OpenGL.GLX.NV.video_capture` and the two
  `OpenGL.GLX.SGIX` modules, whose GLX types were undeclared; and
  `OpenGL.GLES3.vboimplementation`, which named an `OpenGL.GLES3.OES` package
  that does not exist. Every shipped module is now imported by the suite.
- PyOpenGL no longer reports errors from its own interior in a user's `mypy`
  run: 3,041 errors in 252 files became 318 in 54, and a six-line user program
  that came back with errors from `OpenGL/plugins.py` now comes back clean.

## More ways to get a context

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
- **Windows.** ES and EGL reach through ANGLE, and the WGL calls that live in
  GDI resolve properly.

## Packaging and freezing

- A PyInstaller hook ships in the box and PyInstaller finds it by itself. It
  reports the modules PyOpenGL's plug-in registries would import — including
  plug-ins added by other packages — and the Windows GLUT and GLE DLLs. For any
  other freezer, `OpenGL.plugins.registered_modules()` is the same answer.

## Testing and CI

- Around 1,500 test cases across GL, GLU, GLES and EGL, run against whatever
  driver is present rather than a fixed list, with GLFW, pygame, Tk, EGL and CGL
  backends. `TEST_VISIBLE=false` runs much of it without opening windows.
- Coverage is measured against what the machine in front of the suite actually
  exports, not against the registry: 1,052 of 1,052 commands for the GL
  versions, and of the 1,910 entry points a reference driver provides, the five
  not called by anything are `GL_EXT_semaphore` calls that need a semaphore
  imported from Vulkan or Direct3D.
- CI runs on llvmpipe and on the macOS runners on every push, across six Python
  versions, with and without numpy, and with and without `accelerate`.
- A weekly job pulls the Khronos registry, regenerates the bindings and opens a
  pull request when anything changed, so a new entry point is not discovered by
  somebody trying to call it.

## Compatibility notes

- **Python 3.9 or newer, and numpy 2.x.** numpy remains optional; the suite runs
  and is tested without it.
- **`PyOpenGL_accelerate` must match the PyOpenGL it was generated from.** The
  two are released together and its dispatch tables are generated from that
  PyOpenGL, so install the pair in one command.
- The platform module is now named `linux` rather than `unix`.
- Licence metadata is in SPDX form; the licence itself is unchanged BSD-3-Clause.

## Documentation

- [The C dispatch layer](https://mcfletch.github.io/pyopengl/documentation/c-dispatch.html)
  — what it covers, what differs, contexts, arrays, strings and error checking.
- [EGL devices](https://mcfletch.github.io/pyopengl/documentation/egl-devices.html)
- [Offscreen OpenGL on macOS](https://mcfletch.github.io/pyopengl/documentation/cgl-offscreen.html)
- [OpenGL in a Tkinter widget](https://mcfletch.github.io/pyopengl/documentation/tk-widget.html)
