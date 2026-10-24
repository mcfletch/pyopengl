# PyOpenGL 4.0 release notes

Changes since the 3.x series. The current development version is `4.0.0a5`.

## Python 3.9+ Only

- Support for Python 2.7 and 3.6 through 3.8 is removed entirely
- Type declarations are included throughout

## C dispatch layer in PyOpenGL_accelerate

- `PyOpenGL_accelerate` ships a C dispatch layer generated from the Khronos
  registry. It covers 4,859 of PyOpenGL's 4,880 bindings across GL, GLES 1/2/3,
  GLSC2, GLX, WGL and EGL.
- Measured on an RTX 3060 Ti with CPython 3.12: `glBindTexture` 407 ns → 58 ns,
  `glUniform1f` 382 ns → 51 ns, `glUniformMatrix4fv` with a numpy 4×4
  1184 ns → 106 ns. That is roughly seven times faster per call, and eleven
  times for a call that passes an array.
- The gain for a program depends on how much of its frame time goes on
  dispatch. Optimised PyOpenGL applications measured about 5% faster. A
  call-heavy or immediate-mode program comes closer to the ratios above.
- Both implementations provide the same bindings with the same semantics, and
  the test suite runs under both. `pip install PyOpenGL` on its own still
  installs the pure-Python ctypes implementation on every platform and
  interpreter. `PYOPENGL_DISPATCH=ctypes` selects ctypes where the extension is
  installed. `OpenGL.dispatch.status()` reports which implementation is active
  and, if it is not the one requested, the reason.

## Per-context entry-point tables

- Under ctypes, the first context to resolve an entry point fixes the binding
  for the whole process. When two contexts differ (a discrete-GPU context
  beside a software one, core beside compatibility, GLES beside desktop GL),
  the binding is wrong for one of them. The ctypes implementation has always
  worked this way and still does. This may be fixed in a later release.
- Under the C implementation each context has its own table. `bool(glFoo)` and
  `glInitXxx()` report on the current context, and a binding held across a
  context switch still dispatches correctly.
- `OpenGL.dispatch.make_current()` and `forget_context()` let a program report
  each context switch explicitly. `PYOPENGL_CONTEXT_TRACKING=verify` queries the
  driver for the current context on every call instead, with no program changes.

## Error checking: `GL_KHR_debug`, and one query per API

- Where the context offers `GL_KHR_debug`, PyOpenGL uses it for error checking.
  A check costs 0.8 ns, compared with 11 ns for a `glGetError` round trip, and
  the `GLError` carries the driver's own `description` of the error. It is on
  by default and can be turned off per process or per context.
- GL, GLES, EGL and the window-system APIs each report errors through their own
  query. In 3.x a single `glGetError` checked all of them. It missed every EGL
  error, and could attribute a stale GL error to an EGL call.
- `OpenGL.dispatch.set_error_checking()` changes error checking at run time, for
  one entry point or for all of them. The import-time flag cannot do this.

## Memory safety and crash fixes

- Several `glGet` output sizes were recorded too short, so the driver wrote past
  the end of the array PyOpenGL had allocated. No error was raised, and the
  damage appeared later as an unrelated crash. The sizes for
  `GL_PATCH_DEFAULT_INNER_LEVEL`, `GL_PATCH_DEFAULT_OUTER_LEVEL`, the NV
  coverage modes and a bounding-box query are corrected. Every test run now
  checks the whole shipped size table against the live driver.
- Fixed: segfaults on exit under GLFW; VBO deletion attempted with no current
  context; and `OpenGL.GL.ARB.vertex_array_object` wrapping the output of
  `glGenVertexArrays` twice, once from the generator and once by hand.
- A `VBO` garbage-collected while a different context was current deleted the
  buffer with the same number in that context. Every context numbers its buffers
  from 1, so the other context's next draw came up empty. A `VBO` now deletes
  its buffer only in the context that created it. It identifies that context
  through `OpenGL.dispatch.context_identity()`, even when the driver has reused
  the context's handle for a new one. Otherwise it leaves the buffer to its own
  context. A program that holds GL names of its own can use the same function.
- Output arrays shorter than what the call was told to write are rejected
  before the call reaches the driver.
- The accelerator's buffer-protocol handler read a `Py_buffer` belonging to a
  memoryview it had already released. `MemoryviewHandler` builds a memoryview
  for any object that is not already one. `arraySize`, `dimensions` and
  `arrayToGLType` each kept a pointer into that memoryview after the statement
  that created it. They then read whatever the allocator had since put in that
  memory: `arraySize` returned 1 for a six-element array, `dimensions` returned
  `()`, and `arrayToGLType` read a freed `format` string and crashed the
  process. Each now holds the memoryview for as long as it reads through it, as
  `unitSize` already did. `dimensions` returns a tuple, like every other shape
  in the handlers.
- An `OpenGL.osmesa.offscreen.OffscreenContext` dropped without being released
  left Mesa holding a live context whose framebuffer Python had freed. OSMesa
  rasterises into an array the caller owns, and keeps the pointer for the life
  of the context. The next `OSMesaMakeCurrent` on that thread flushed the
  dropped context's front buffer through that pointer. The result was a
  512-byte write into freed memory, and a crash later in an unrelated call. The
  context now releases itself when it is garbage-collected. `release()` also
  takes `forget=False`, as `OpenGL.WGL.offscreen` does, for a caller that tears
  a context down without informing the dispatch layer.
- `OffscreenContext.make_current` now informs the dispatch layer of the switch,
  which it cannot detect on its own. The compiled layer keeps a table of
  resolved entry points per context. It re-reads the current context only when
  it resolves a new entry point. So a second OSMesa context kept dispatching
  through the first context's table, using its resolved addresses and its
  record of which commands that context supports. `OpenGL.WGL.offscreen` and
  `OpenGL.Tk` already informed the dispatch layer.

## Binding fixes

- With the C dispatch layer, `glColorPointerf(array)` and every other typed
  client-array setter in `OpenGL.GL.pointers` converted its array with the
  converter of the first setter built from the same entry point. That was
  usually `glColorPointerd`'s converter, to doubles. Each setter still told the
  driver the type its own name gives, so a draw read float64 memory as float32
  and produced garbage colours and positions. Each derived function now carries
  the customisations its own chain declared, in whatever order the chains are
  built. The chain keeps the record, in its own `GLProc` that dispatches
  through the entry point's slot. `glColorPointer` demoted by `errcheck`
  carries only its own customisations, and the entry point `OpenGL.raw` exports
  carries none.
- `glIndexPointerb` and `glTexCoordPointerb` passed `GL_BYTE`, which neither
  entry point accepts, so every call raised `GL_INVALID_ENUM`. They now pass
  their bytes widened to `GL_INT`, as `glVertexPointerb` does.
- `gluUnproject4` had the wrong signature. The new suites found defects in GLU
  quadrics, NURBS and the tessellator, which are fixed.
- `glGetTexImageCompressed` ignored the level it was given.
- `glGetTexImage`, `glReadPixels` and the other calls that size their result
  from a format raised `Unrecognised image format` for `GL_RG`,
  `GL_RG_INTEGER`, `GL_BGR_INTEGER` and `GL_BGRA_INTEGER` unless
  `OpenGL.GL.ARB.texture_rg` had been imported. These formats are core from
  GL 3.0, and `OpenGL.GL` now sizes them itself.
- `glDrawBuffersEXT` was being wrapped to `glDrawBuffers`.
- Constants larger than `sys.maxint` converted incorrectly.
- GLES image functions had wrong sizing, and now have size checks.
- `int64` and `uint64` array element types are supported.
- Extension availability is cached per context instead of being re-queried.
- A command adopted into core is exported as core, not as its extension.
- Several modules that failed to import now import, and the type names their
  declarations use are now declared. The modules are:
  - `OpenGL.GLSC2` in its entirety, which had neither `raw/GLSC2/_types.py`
    nor `raw/GLSC2/_errors.py`;
  - `OpenGL.GLU.EXT.nurbs_tessellator`, which read its constants from a module
    that does not define them;
  - `OpenGL.GLES3.vboimplementation`, which named an `OpenGL.GLES3.OES` package
    that does not exist;
  - `OpenGL.GLX.NV.video_capture` and the `OpenGL.GLX.SGIX` modules, whose
    `Colormap`, `Status`, `GLXVideoDeviceNV`, `DMparams`, `DMbuffer`,
    `VLServer`, `VLPath` and `VLNode` were undeclared;
  - the GL extensions declared with `GLeglClientBufferEXT` or `GLVULKANPROCNV`.

  The suite imports every shipped module and evaluates every declaration in the
  shipped tables.
- `glGenVertexArrays(1)` and the other entry points that allocate their own
  output ask the array handler for an array of a given length, not a given
  shape. The ctypes handlers accepted only a shape sequence, so without numpy
  installed those calls raised `TypeError` before reaching the driver. Both
  handlers now accept a length or a shape, as the numpy handler does.
- `FormatHandler.typeLookup` returns the handler a data type resolves to. It
  raised `TypeError: 'HandlerRegistry' object is not subscriptable` wherever
  PyOpenGL_accelerate was installed. The pure-Python registry is a dict
  subclass, but the compiled one offered only `__setitem__`. The compiled
  registry now supports lookup by type, and a type with no handler raises the
  documented `KeyError`.
- `OSMesaGetColorBuffer` and `OSMesaGetDepthBuffer` return a one-byte
  `GLboolean`, but were called with no declared result type. So ctypes read a C
  `int`, and three bytes the call never wrote decided the result. "There is no
  buffer" could arrive as "here is one", with a width, height and pointer that
  were never written either. Both functions now declare their result and
  argument types. A query with no buffer returns `(0, 0, 0, None)` on every
  ABI.
- `FormatHandler.dimensions` declared a `typeCode` parameter that no handler
  accepts and no caller passes. A third party writing a handler from that
  interface would have written an argument every implementation refuses.
- `glGetUniformIndices(program, ['name', ...])` returns a `GLuint` array with
  one index per name. `OpenGL.GL`, `OpenGL.GL.ARB.uniform_buffer_object` and
  `OpenGL.GLES3` share one implementation. It also accepts the C argument order,
  `(program, uniformCount, uniformNames[, uniformIndices])`, recognised by the
  second argument being a count. `uniformNames=` works as a keyword. The names
  are required in either form, so `glGetUniformIndices(program, 3)` raises
  `TypeError` instead of passing the driver a null array to read three names
  from. GLES3 did not accept the C order before.
- An input array from which the driver reads a caller-given count of items is
  now checked against that count, on both dispatch paths, when
  `ARRAY_SIZE_CHECKING` is on. `glViewportArrayv(first, count, v)` needs
  `count * 4` floats, and the scissor, depth-range and multicast arrays need
  their own multiples. An array of strings needs at least `count` of them; this
  covers `glTransformFeedbackVaryings`, `glCreateShaderProgramv`,
  `glCompileShaderIncludeARB` and `glGetUniformIndices`. A shorter array, or
  `None` for a positive count, raises `ValueError`. Without the check, the
  driver would have read past the array or from address zero. A longer array is
  accepted, and a `GLchar *const *` built by the caller is passed without a
  check. Strings are counted whatever `ARRAY_SIZE_CHECKING` says. PyOpenGL
  allocates the pointer array the driver reads, and sizes it from the length of
  the sequence. A larger count would read past the end of that buffer.
- Three entry points sized their output array by looking up a count in the
  `glGet` size table, as if a byte count or a name count were an enum. They
  were `glGetUniformIndices` in GL and in GLES3, and
  `glGetNamedBufferSubDataEXT`. If the table happened to contain the count, the
  result was a one-element array for the driver to write every value into. That
  is a heap overrun, and `glGetNamedBufferSubDataEXT(buffer, offset, 16)`
  aborted the process on a real driver. If the table did not contain the count,
  the call raised `KeyError`. Each is now sized from its count argument. The
  suite checks that every remaining `glGet`-table size lookup names an enum.

## Type stubs and `py.typed`

- 1,310 `.pyi` stubs and a `py.typed` marker, covering the constants, the entry
  points and their signatures. The generated modules fill their namespaces from
  declaration tables at import time, so editor completion and type checkers
  read the stubs instead.
- GLU, GLUT and GLE have stubs as well. None of the three is a Khronos API, so
  each is written by hand and the registry-driven generator does not cover
  them. Their stubs are generated from the declarations themselves: 354 GLUT
  names, 219 GLU and 52 GLE.
- Docstrings give GL types using the registry's own names, so they read
  `glBindTexture(target: GLenum, texture: GLuint) -> None` and not
  `glBindTexture(target, texture) -> None`.
- Entry points that `OpenGL.GL` exports through its own wrapper are described
  with the wrapper's arguments, not the C function's.
  `glDeleteTextures(textures)` reads the count from the array it is given, and
  the stub offers that form alongside the `(n, textures)` pair. `glMap1d`,
  `glMap1f`, `glMap2d` and `glMap2f` take the points array without the strides,
  and the stub offers only that form, because it is the only one they accept.
  `glCallLists` and `glAreTexturesResident` gain their Python forms the same
  way. GLU and GLE have many such wrappers.
  `gleExtrusion(contour, cont_normal, up, point_array, color_array)` takes five
  arguments where the C entry point takes seven, because both counts are read
  from the arrays passed with them. `gluProject(objX, objY, objZ)` fills in the
  three matrices from the current GL state. Each stub describes what its
  wrapper accepts.
- The stub for a friendly module (such as `OpenGL.GL.VERSION.GL_1_5`)
  describes the wrappers that module binds, as the namespace stub does.
  `from OpenGL.GL.VERSION.GL_1_5 import glBufferData` allows
  `glBufferData(target, data)`. `glGetUniformIndices` imported from
  `OpenGL.GL.VERSION.GL_3_1`, `OpenGL.GL.ARB.uniform_buffer_object` or
  `OpenGL.GLES3.VERSION.GLES3_3_0` takes the names and returns `GLuint`
  indices.
- The stubs are checked, and a defect in them fails the build. `mypy` runs over
  all 1,310 of them in CI. The suite checks each stub against the object it
  describes, including the number of arguments each GLU, GLUT and GLE entry
  point takes in its Python form. `[tool.mypy]` in `pyproject.toml` states what
  the check covers, and why the package's own source is excluded.
- A `mypy` run over a program that imports PyOpenGL reads the stubs, and
  reports no errors from inside the package's own modules.

## Configuration flags

The flags `OpenGL/__init__.py` documents are read from the environment as
`PYOPENGL_<NAME>`. CI runs the whole suite with `PYOPENGL_ERROR_ON_COPY=1`, with
`PYOPENGL_ARRAY_SIZE_CHECKING=0` and with `PYOPENGL_SIZE_1_ARRAY_UNPACK=0`, as
well as with the defaults.

- `SIZE_1_ARRAY_UNPACK` reads `PYOPENGL_SIZE_1_ARRAY_UNPACK`. It was the only
  flag in the set with no environment variable. Setting the variable did
  nothing, and only assigning the name before the first import had any effect.
- With `PYOPENGL_SIZE_1_ARRAY_UNPACK=0`, `vbo.VBO` could not create a buffer. It
  read the result of `glGenBuffers(1)` with `long()`, which cannot read a
  one-element array. It now reads through `OpenGL._scalar.as_int`, which
  accepts either shape.
- With `PYOPENGL_ERROR_ON_COPY=1`, a parameter declared as a bare pointer got
  no converter on the ctypes path. This included `GLintptr` and `GLsizeiptr`,
  and the surface arrays of `GL_NV_vdpau_interop`. So ctypes rejected every
  array passed to such a parameter, including the array whose memory the call
  needed. Such a parameter now resolves to the array class for its element type.
  That class rejects a copy the same way, so the flag behaves as before.
- With `PYOPENGL_ERROR_ON_COPY=1`, a typed client-array setter passed the array
  it was given to the driver without converting it. `glVertexPointerb` always
  passes GL_INT, so an array of bytes was passed as ints and read at four times
  its length. `glColorPointerf` given float64 data had it read as float32. The
  setters now convert under the flag as they do without it. For an array of
  another type, that conversion raises the `CopyError` the flag exists to raise.
- With `PYOPENGL_ERROR_ON_COPY=1`, `VBO.delete()` could not delete a buffer. It
  passed the buffer name as an int, which the wrapper copies into an array. It
  now builds a `GLuint`, as the deleter that runs at garbage collection already
  did.
- `FORWARD_COMPATIBLE_ONLY` has no effect from 4.0, but reading or setting it is
  still allowed. It was meant to make the entry points removed in OpenGL 3.1
  refuse calls. It checks a `deprecated` mark on each entry point as it is
  built, and nothing sets that mark. The list of forward-compatible names is in
  `OpenGL/platform/entrypoint31.py`, and nothing imports it. Requesting a
  forward-compatible context from the window system is a separate feature and
  is unaffected.
- `TYPE_ANNOTATIONS` affects nine entry points: OSMesa's eight and one EGL
  extension, which are the raw modules still written by hand. Everything the
  registry generates comes from the declaration tables and never goes through
  `OpenGL.platform.types`, the decorator the flag controls. Type checkers read
  the `.pyi` stub beside each package.
- With `PYOPENGL_CONTEXT_CHECKING=1`, an OSMesa program could not create its
  first context. The check applies to GL calls, and skips the display APIs that
  live in the GL library: `libGL` exports `glX*` and `opengl32` exports `wgl*`.
  OSMesa is a third such API, since its GL library is `libOSMesa` itself. So
  `OSMesaCreateContext` was checked for a current context before one could
  exist. `OSMesa*` calls are now skipped along with the other two.
- `ALLOW_NUMPY_SCALARS` has no effect from 4.0, but reading or setting it is
  still allowed. A numpy integer scalar is accepted wherever an integer is
  expected, with or without the flag, because ctypes converts it through
  `__index__`. The flag only added a retry through `int()`, which also accepted
  a numpy float and silently truncated it.

## Context creation

- Headless EGL - `OpenGL.EGL.devices` lists the EGL devices a system offers,
  each driver's name for itself, and which devices rasterise on the CPU. It
  also gives the handle `eglGetPlatformDisplayEXT` needs. Without it, getting
  this information takes three extensions and two string queries.
- macOS without a window server - `OpenGL.CGL` creates a context with no window
  and no window server. `headless_context()` and `OffscreenTarget` provide a
  target to draw into.
- Tkinter: new class `OpenGL.Tk.GLFrame` is a direct GLX/WGL context without
  the use of Togl, and on macOS an `NSOpenGLContext` on a view over the widget
  (profiles through `OpenGL.CGL`; core 3.2 to 4.1, or the 2.1 legacy profile)
- `OpenGL.Tk.RawOpengl` and `OpenGL.Tk.Opengl` are now `GLFrame` sub-classes
  that do not need Togl
- `OpenGL.Tk.Togl` remains a Togl-using widget, but loads the library when
  first instantiated rather than when first imported
- Wayland - on Linux, the choice between GLX and EGL is made by probing at
  context creation, so GLUT runs under Wayland with XWayland.
- Windows - Windows does not include OpenGL ES or EGL. ANGLE is how a Windows
  machine gets either. `PYOPENGL_PLATFORM=angle` binds them to an installed
  ANGLE, and
  `PYOPENGL_ANGLE_PATH` selects which copy to use. Applications ship their own
  copy of ANGLE, so it is not installed system-wide and a machine may have
  several. The `angle` platform provides ES and no desktop GL, because ANGLE
  provides only ES.
- Windows, without selecting a platform - the default platform looks for
  `libEGL`, `libGLESv1_CM` and `libGLESv2`, the names an ANGLE or Mesa build
  installs beside the application that ships it. It also looks for the bare
  names `EGL`, `GLESv1_CM` and `GLESv2` that an SDK or driver vendor uses.
  `OpenGL.GLES1`, `OpenGL.GLES2` and `OpenGL.GLES3` import whether or not a
  machine has these libraries. A call with no entry point behind it raises
  `NullFunctionError` naming the function. The WGL calls that live in `gdi32`
  are resolved there, instead of only in `opengl32`.
- Windows loads its own OpenGL - `opengl32` and `glu32` are passed to the
  loader by name, so Windows' search order applies and the system directory is
  searched before `PATH`. `System32\opengl32.dll` forwards to whatever the
  graphics driver installed. Searching `PATH` first meant that in a conda
  environment, which puts a Mesa `opengl32.dll` earlier on `PATH`, programs
  rendered in software with no indication.
- `NullFunctionError` now distinguishes three causes. The message used to be
  the same whether the library was not installed, no context had been created
  yet, or the driver lacked the entry point. These are three problems with
  three different fixes. When the library is absent, the message names the
  library and where to get it. It also says that every entry point in that
  library is undefined, so the reader does not investigate the one function
  they called. When no context is current, the message says so. Above GL 1.1 a
  function address comes from the context. On Windows, `wglGetProcAddress`
  needs a current context, so a missing context is the usual reason a call
  like `glGenVertexArrays` is undefined on a machine whose driver supports it.
- OSMesa on Windows reaches OpenGL 2.0 and above - Mesa's Windows `osmesa`
  library exports only the `opengl32` list, which is the GL 1.1 set. It
  provides everything above that through `OSMesaGetProcAddress`. The ctypes
  binding path looked only in the library, so `glVertexAttribPointer` and every
  other entry point above GL 1.1 was undefined, even on a context that had just
  cleared and read back a frame. Both are now searched, as the Windows platform
  has always searched `opengl32` and then `wglGetProcAddress`.
- A GLUT you installed is found by its own name - the Windows platform looks
  for `freeglut` and `glut32` before the builds PyOpenGL ships. These are the
  names used by the official freeglut binaries, MSYS2, vcpkg and the original
  GLUT. A library built for the wrong architecture no longer stops the search
  at the first name.

## Packaging and freezing

- The Windows GLUT and GLE builds are an optional download. They used to ship
  inside every wheel on every platform. So a Linux server rendering through EGL
  downloaded twelve Windows libraries it could never load. Some security
  scanners flagged the decade-old vendored binaries and quarantined PyOpenGL
  itself, for users who never wanted GLUT (#164). The builds are now in
  `PyOpenGL-glut-binaries`:

  ```
  pip install PyOpenGL[glut]
  ```

  **A Windows program that calls `glutInit()` needs that extra**, where a
  plain `pip install PyOpenGL` used to be enough. Nothing else changes. A
  freeglut the system provides still takes priority over the shipped build.
  Where neither is present, the error names the command to run, instead of
  reporting an undefined function. The same download includes GLE.
- PyOpenGL includes a PyInstaller hook, which PyInstaller finds automatically.
  It lists the modules PyOpenGL's plug-in registries would import, including
  plug-ins added by other packages. It also lists the Windows GLUT and GLE
  libraries, from wherever the running loader would find them. An application
  frozen on a host without the extra is frozen without GLUT. Other freezers can
  call `OpenGL.plugins.registered_modules()` for the same list.
- Building `PyOpenGL_accelerate` from a source tree deletes the generated C
  when the Cython or numpy version that generated it has changed. Those modules
  `cimport numpy`, and `cythonize` uses timestamps to decide whether to
  regenerate the C. Without this step, C left over from an earlier build could
  be compiled against numpy headers it no longer matches.

## Testing and CI

- Around 1,500 test cases across GL, GLU, GLES and EGL, run against whatever
  driver is present instead of a fixed list, with GLFW, pygame, Tk, EGL and CGL
  backends. `TEST_VISIBLE=false` runs much of the suite without opening
  windows.
- Coverage is measured against what the test machine's driver exports, not
  against the registry. The GL versions have 1,052 of 1,052 commands covered. A
  reference driver provides 1,910 entry points, and the five that no test calls
  are `GL_EXT_semaphore` calls that need a semaphore imported from Vulkan or
  Direct3D.
- CI runs on every push, on three platforms and their software renderers:
  - Linux on llvmpipe, through an EGL device and through OSMesa;
  - Windows on Mesa, through a WGL pbuffer;
  - macOS 15 through CGL, on both Intel and Apple Silicon.

  One Linux cell runs on arm64. The `PyOpenGL_accelerate` wheels for aarch64
  are built on an arm64 machine, without emulation.
- The interpreter sweep runs 3.9, 3.10, 3.12, 3.13 and 3.14. 3.9 is the
  `requires-python` floor, and the test suite is what checks it. mypy refuses
  `--python-version=3.9`, and numpy's own stubs need 3.12 to parse.
- Further cells cover numpy absent, `accelerate` built with the C entry points
  selected, `accelerate` built with the ctypes entry points selected,
  `accelerate` built and then declined with `PYOPENGL_USE_ACCELERATE=0`, and the
  configuration flags above. A run that requests the C entry points where the
  extension is not installed fails, instead of falling back to ctypes.
- The stub typecheck is a cell of the matrix, so `tox` runs it.
- A weekly job pulls the Khronos registry, regenerates the bindings and opens a
  pull request when anything changed. A new entry point reaches PyOpenGL before
  a user tries to call it.

## Compatibility

- Python 3.9 or newer, and numpy 2.x. numpy remains optional; the suite runs and
  is tested without it.
- `PyOpenGL_accelerate` must match the PyOpenGL it was generated from. The two
  are released together, and its dispatch tables are generated from that
  PyOpenGL release, so install both in one command.
- PyPy runs the ctypes bindings. `PyOpenGL_accelerate` is built for CPython, so
  neither the C dispatch layer nor the Cython accelerators are available on
  PyPy. `OpenGL.dispatch.status()` reports which implementation is running and
  why. The buffer-protocol array handler reads CPython's C API through
  `ctypes.pythonapi`, which PyPy does not have. So on PyPy a `memoryview` has no
  array handler, and passing one reports a missing handler instead of an error
  from inside the call.
- The platform module is now named `linux` rather than `unix`.
- Licence metadata is in SPDX form; the licence itself is unchanged BSD-3-Clause.

## Documentation

- [The C dispatch layer](https://mcfletch.github.io/pyopengl/c-dispatch.html)
  (what it covers, what differs, contexts, arrays, strings and error checking)
- [EGL devices](https://mcfletch.github.io/pyopengl/egl-devices.html)
- [Offscreen OpenGL on macOS](https://mcfletch.github.io/pyopengl/cgl-offscreen.html)
- [OpenGL in a Tkinter widget](https://mcfletch.github.io/pyopengl/tk-widget.html)
- [Offscreen OpenGL on Windows](https://mcfletch.github.io/pyopengl/wgl-offscreen.html)
- [OpenGL ES through ANGLE](https://mcfletch.github.io/pyopengl/angle-gles.html)
