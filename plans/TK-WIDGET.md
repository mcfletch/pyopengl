# The Tk widget makes its own context

**Status:** X11 landed and verified (2026-09-06). Windows landed and verified
(2026-09-07) -- see [What Windows turned up](#what-windows-turned-up). macOS
written 2026-10-18 and **not yet run on a Mac**: the only place there is to run
it is CI -- see [macOS](#macos-aqua).

## What was there

`OpenGL.Tk` is a wrapper around **Togl**, a Tcl C extension that has to be
installed separately, whose last release was 2005 and which reaches Debian as
`libtogl2`. The module's own docstring recommends using something else.

Three things follow from that, and each is a defect on its own:

- **The module cannot be imported without a display and a Togl installation.**
  Importing it runs `_default_root = Tk()` at module scope, creates a root
  window as a side effect, appends to Tcl's `auto_path`, and does `package
  require Togl` — so `import OpenGL.Tk` raises on a build machine, in a test
  collection, and anywhere Togl is not installed. A library that opens a window
  when it is imported cannot be imported to ask what it offers.
- **It registers a process-wide `atexit` hook that destroys
  `tkinter._default_root`** and sets it to `None`, whoever created it and
  whatever else is using it.
- **Everything it offers is fixed-function.** `Opengl.tkRedraw` calls
  `glMatrixMode`, `gluPerspective` and `gluLookAt`; `basic_lighting` calls
  `glLightfv`. None of it exists in a core profile, and nothing in the module
  can ask for one, so a Tk application cannot use the shaders, vertex array
  objects or anything else written since 2008.

## What is there now

A Tk widget that creates its own GL context on its own native window, with no
Tcl extension involved. Tk hands out the platform's window handle
(`winfo_id()`), and every platform has a documented way to make a context
against one.

```python
from OpenGL.Tk import GLFrame
from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT

class Scene(GLFrame):
    def initgl(self):                      # once, with the context current
        glClearColor(0.2, 0.3, 0.3, 1.0)
    def redraw(self):                      # per frame
        glClear(GL_COLOR_BUFFER_BIT)

root = tkinter.Tk()
frame = Scene(root, width=640, height=480, profile='core', version=(3, 3))
frame.pack(fill='both', expand=True)
root.mainloop()
```

- `OpenGL/Tk/attributes.py` — `ContextAttributes`: what a caller asks a context
  for, in one object, translated per platform.
- `OpenGL/Tk/context.py` — `createContext(widget, attributes)`, which picks the
  implementation from **Tk's own** `tk windowingsystem` rather than from
  `sys.platform`, so an X11 Tk on macOS gets GLX and is right.
- `OpenGL/Tk/glx.py` — X11, through `glXChooseFBConfig` and
  `glXCreateContextAttribsARB`. The core profile comes from here.
- `OpenGL/Tk/win32.py` — Windows, through `wglChoosePixelFormatARB` and
  `wglCreateContextAttribsARB`, with the dummy-context dance those two need.
- `OpenGL/Tk/widget.py` — `GLFrame`: the context's lifecycle against the
  widget's, the customisation points, and a render loop an application can
  drive itself.
- `OpenGL/Tk/togl.py` — the historic `Togl` widget, loaded **on demand** for
  anyone who has it, and `RawOpengl` / `Opengl` rebuilt on `GLFrame` so the
  code that used them keeps working and stops needing Togl.

## What each platform needs, and what it gets

| Tk windowing system | How | State |
| --- | --- | --- |
| `x11` | `glXCreateContextAttribsARB` on the window `winfo_id()` names | Implemented, verified against Mesa |
| `win32` | `wglCreateContextAttribsARB` on the DC of that `HWND` | Implemented, verified against Intel UHD 630 |
| `aqua` | `NSOpenGLContext.setView:` on an `NSView` added over the widget | Implemented, awaiting its first CI run |

macOS is the one that needs a language binding rather than a call: see
[macOS](#macos-aqua).

## What Windows turned up

Run 2026-09-07 on Windows 10 Pro 19045, CPython 3.13.1, Intel UHD Graphics 630,
driver 31.0.101.2114. `TEST_WINDOWING=tk python -m pytest tests` and
`tests/test_tk_widget.py`. Five defects, each fixed with a test of its own; the
prediction that any correction would belong in `OpenGL/Tk/win32.py` held for two
of them and not for the rest.

**Every Win32 handle lost its top half.** `OpenGL/Tk/win32.py` reached `GetDC`,
`SetPixelFormat` and the rest through `ctypes.windll` with no prototypes
declared, and ctypes gives an undeclared function a return type of C `int` --
half the width of an `HDC`. `SetPixelFormat`, undeclared, was handed the
truncated value zero-extended; `wglCreateContext`, whose `HDC` *is* declared,
was handed it sign-extended. The format was set on one device context and the
context asked for on another, and the driver answered
`ERROR_INVALID_PIXEL_FORMAT` with nothing in it to say a handle was to blame.
Which half of the handle a window happened to land in decided whether it showed,
so the same program made a context on one window and not the next -- and a
failure to make one is a `skipTest`, so most of the suite skipped while
reporting green. `OpenGL/Tk/win32.py` now declares every entry point it calls in
`SIGNATURES`, on a `WinDLL` of its own rather than the one every library in the
process shares. `tests/test_tk_win32.py`.

**The widget's own suite never ran here.** `tests/test_tk_widget.py` gated its
windowed cases on `DISPLAY`, which names a display only on Linux, so 32 of its
36 cases skipped on Windows -- which is why the defect above was not caught by
the tests written for it. It asks `backends.has_window_server()` now, which is
the question in a form each platform can answer.

**Nothing said when a context went.** The dispatch layer's table of resolved
entry points is keyed by the context handle, and a handle is an address the
driver hands out again. WGL needs two throwaway contexts per widget -- one to
look `wglChoosePixelFormatARB` up through, one for
`wglCreateContextAttribsARB`, neither resolvable without a context that already
exists -- so this module creates and destroys three contexts where a caller
asked for one, and their addresses come back quickly. It said nothing about any
of them. A table left behind under a reused address answers for a context that
is no longer there: an entry point reported undefined where the context has it,
or resolved where it does not, which is what
`tests/gl/test_no_context_calls.py` saw as the C and ctypes layers disagreeing.
`OpenGL.Tk.context.nowCurrent` and `.gone` are the two notifications, used by
both platform implementations, exactly as
`OpenGL.WGL.offscreen.OffscreenContext` already used them -- a caller reaching
for the widget directly has no fixture to do it for them. The GLX side takes
the same two calls; it makes no throwaway contexts, so only its `destroy` was
missing one, and that half is **not** verified here for want of an X display.

**`TkBackend` had no `_make_current`,** so the suite's `_context_handle()`
answered None for every Tk context and none of them was ever forgotten -- the
stale-table hazard `_release_context` exists to prevent, run for the whole
suite. `tests/glcontext_tk.py` implements the hook, which is what
`test_shared_context_setup` was asking for all along.

**A context torn down inside a `glBegin` block took the process with it.** Not a
Tk defect -- it reproduced on GLFW too, and is
[the 2026-09-03 note's item D](2026-09-03-windows-suite-remaining-work.md)
("an access violation in `glfwCreateWindow`, seen once, not reproduced"). See
[A block outlives nothing](#a-block-outlives-nothing).

## A block outlives nothing

A `glBegin` block is closed in the context that opened it. A context created or
destroyed while one is still open is undefined, and Intel's Windows ICD does not
survive it: it leaves state that the **next** context creation in the process
faults on, so the access violation lands on whichever code asks for the next
context rather than on the one that abandoned the block.

Measured, `tests/gl/test_begin_block_recovery.py`, 20 runs each:

| what was left out of the sequence | access violations |
| --- | --- |
| nothing (the case as written) | 10/20 |
| the `glBegin` | 0/20 |
| the block left open -- `glEnd` called | 0/20 |
| `dispatch.forget_context` | 12/20 |
| destroying the context | 0/20 |
| creating the next context | 0/20 |
| making the next context current | 9/20 |

So the block, the destruction and the next creation are each necessary, and
neither the notification nor the make-current is. `ig9icd64.dll` 31.0.101.2114,
`0xC0000005`, fault offset `0x5b37bb` -- the same instruction in all of them.

The fix is that PyOpenGL closes such a block rather than handing the driver a
state the specification does not define. `OpenGL.error.end_abandoned_block()`
closes one and answers whether there was one; `make_current` and
`forget_context` call it for the changes PyOpenGL is told about, and a toolkit
calls it for the one it is not -- creating a context, which happens inside the
toolkit. `OpenGL.Tk` does that in `GLFrame.createContext`, and the suite's
fixture in `ContextTestCase._open_context`, since it owns the GLFW window.

After it: 0/30 on GLFW and 0/30 on Tk, where the same command was 7/30 and 9/20.
The two cases that used to skip with "driver did not provide the requested
context" now run, because that refusal was the driver declining to make a
context inside the open block.

## macOS (Aqua)

**Status: written, unrun.** There is no Mac in the container, so the first
verification is the `macos` job in `.github/workflows/test.yml`, which has three
areas for it (below). Expect the first runs to find defects; the places to look
are listed under [What CI will say](#what-ci-will-say).

Tk's Aqua widgets are rectangles drawn into the single `NSView` that fills each
toplevel, so `winfo_id()` names nothing a context can be attached to. The
implementation therefore adds a view of its own:

- `OpenGL/Tk/cocoa.py` -- `Runtime`, the few Objective-C messages needed, sent
  through `ctypes` with `objc_msgSend` cast to the shape of each message. Struct
  results are not used (Intel returns them through `objc_msgSend_stret`).
- `OpenGL/Tk/aqua.py` -- `AquaContext`. The pixel format and profile come from
  `OpenGL.CGL`, shared with the headless test backend: `profile_for`,
  `pixel_format_candidates` (a GPU renderer first, the CPU one where a machine
  has none), `PROFILE_VERSIONS`, `version_shortfall`, `set_swap_interval`. They
  moved there from `tests/glcontext_cgl.py` and `tests/glcontext.py`, which
  import them back.
- The decisions are plain functions -- `cglProfile`, `pixelFormatSizes`,
  `widgetOffset`, `viewFrame`, `chooseWindow` -- tested on every platform in
  `tests/bindings/tk/test_tk_aqua.py`; the Mac-only cases are `TestOnAqua`.

How a context is made: `NSOpenGLPixelFormat` from the CGL attribute list, an
`NSOpenGLContext` from that, a plain `NSView` added to the toplevel's content
view and made the size of the widget, `setView:`. The context's
`CGLContextObj` is the handle PyOpenGL keys its dispatch tables by, so
`CGLGetCurrentContext` agrees with it. A context lower than its profile
promises (a renderer that only implements 2.1) is refused after creation,
because the first 3.x call on it ends the process.

Which `NSWindow` is the toplevel's: Tk keeps no handle a script can read, so a
single Tk window is taken as it is, and with several the toplevel is given a
unique title for the length of the question and the window wearing it is the
one.

Limits, stated in `docs/tk-widget.rst`: the view is above Tk's own drawing; the
surface is in points, not Retina pixels; OpenGL up to 4.1; compatibility only
as the 2.1 legacy profile.

### CI

The `macos` job gains three areas, each recorded for the gate:

| area | runs |
| --- | --- |
| `tkprobe` | `tests/report_tk_aqua.py`: interpreter, Tk version, GUI session, Tk opened in a child process, a context for each profile, a clear colour read back, a screenshot (`test-logs/tk-aqua.png`) |
| `tk` | `tests/bindings/tk` |
| `tkgl` | `tests/gl` with `TEST_WINDOWING=tk`, every context made by the widget |

`tests/bindings/tk` is ignored by the `root` area so a crash in Tk does not take
the other suites with it.

### What CI will say

- **Does the runner have Tk, a window server, the Aqua build?** The probe says,
  and exits non-zero where not. Without it the widget suite skips every case and
  reports green. The workflow uses `actions/setup-python` (python.org's build,
  with Tcl/Tk 8.6) but runs the suite in `tox-uv` environments, whose
  interpreter is not pinned.
- `has_window_server()` answers False when `CGSessionCopyCurrentDictionary`
  returns NULL, which an earlier job reported for a runner; every windowed case
  skips then. The probe prints the session answer beside whether Tk opened.
- Whether the GL view composites above Tk's content view: the screenshot.
- Whether `winfo_x/winfo_y`, the host's `isFlipped` and the toplevel height give
  the right frame: the screenshot again; `TestOnAqua` does not read a frame.
- Whether a withdrawn toplevel (`TEST_VISIBLE=0`) keeps a working context.
- The `NSWindow` match by title, on Tk 8.6 and on Tk 9.

## Five defects X11 turned up

Each was found by needing it, and each is fixed with a test of its own.
Windows turned up its own, [above](#what-windows-turned-up).

**A context handle could not be read as an address.**  `nowCurrent` and `gone`
turned the widget's handle into the integer the dispatch tables are keyed by
with `int(handle)`, and `int()` reads anything offering the buffer protocol --
which every ctypes object does -- as a string of digits.  GLX's `GLXContext` is
a pointer to an opaque struct, so every one of the widget's `makeCurrent` calls
raised `ValueError: invalid literal for int() with base 10: b'@\xeb...'`, and
the 13 windowed cases went with it.  WGL's `HGLRC` fails the same way; it
survived only because the shape reaching `nowCurrent` there is a plain `int`.
The conversion belongs at the dispatch boundary rather than in each caller, so
`OpenGL.dispatch.make_current` and `forget_context` now take the handle in
whichever shape names a context on the platform, and the Tk helpers pass what
they hold.  `tests/bindings/dispatch/test_context_handles.py`.

**Every GLX extension read as absent.**  `_GLXQuerier.getDisplay()` passed a
`str` to `XOpenDisplay`, which takes a `char *`; with no `argtypes` set ctypes
passes `wchar_t *`, the connection fails, and the querier answers GLX version
`[0, 0]` and an empty extension list.  That gate is what every GLX extension
entry point is resolved through, so `GLX_ARB_create_context` (a context with a
profile), `GLX_EXT_swap_control` (vsync) and the rest were all reported missing
on every Python 3 program.  `tests/test_glx_extension_query.py`.

**A framebuffer configuration went stale under the caller.**  Indexing a ctypes
pointer array gives a **view onto that memory**, not a copy of the value, so
after `XFree` released the array the handle read back as whatever was in the
freed block -- and the driver answered `GLXBadFBConfig`, fatally, because of the
next one.

**Xlib's default error handler prints and calls `exit()`.**  A library cannot
leave that in place around a request a server may refuse: asking for a GL
version a driver will not give ended the application rather than raising
something it could answer.  Context creation runs under a handler that collects
the error and turns it into a `TkContextError`.

**A thread may hold one context, and EGL and GLX do not know about each
other.**  Asking EGL for a thread GLX holds is `EGL_BAD_ACCESS`; the reverse is
an X `BadAccess` that ends the process.  A program with two GL views in it has
both APIs, so `platform.PLATFORM.releaseCurrentContext()` says "let go" before
one takes the thread; `tests/gl/test_release_current_context.py`.

## Compatibility

`Togl`, `RawOpengl` and `Opengl` keep their names, their constructor signatures
and their documented methods. What changes underneath is that they no longer
need Togl: `RawOpengl` and `Opengl` are `GLFrame` subclasses that ask for a
compatibility profile, which is what their fixed-function drawing needs.
`from OpenGL.Tk import *` still gives the tkinter names it always did.

The import no longer creates a root window, requires a display, loads Togl or
registers an `atexit` hook. `import OpenGL.Tk` is now a question with an answer
rather than an action.

## Running the suite on it

`TEST_WINDOWING=tk` puts PyOpenGL's own GL suite on this widget, which is how it
is held to the same behaviour as everything else here. It skips what a Tk
context cannot be -- GLX and WGL make desktop contexts, and neither has an ES
equivalent -- and otherwise matches pygame's counts exactly.

```bash
TEST_WINDOWING=tk xvfb-run -a python -m pytest tests
```

`examples/tk_shader.py` is the widget doing what the old one could not: a GLSL
3.30 program, a vertex array object and a uniform matrix, in a window beside
ordinary Tk widgets. `documentation/tk-widget.html` is the page.
