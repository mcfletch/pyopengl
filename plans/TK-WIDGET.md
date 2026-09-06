# The Tk widget makes its own context

**Status:** X11 landed and verified (2026-09-06). Windows and macOS are the
two platforms still to land, and both are wanted for the next release --
see [Still to land](#still-to-land).

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
| `win32` | `wglCreateContextAttribsARB` on the DC of that `HWND` | Implemented, not verified here |
| `aqua` | `NSOpenGLContext.setView:` on the `NSView` Tk owns | Raises, naming what it needs |

macOS is the one that needs a language binding rather than a call: the context
is attached to a view through Objective-C, and Tk's Aqua windows are `NSView`s
that `winfo_id()` does not hand out as such. What it raises says so, and says
that Togl and `pyopengltk` are what there is meanwhile.

## Still to land

Both are wanted for the next release, and neither can be finished in this
container -- there is no Windows and no macOS here, and a context is exactly the
thing that cannot be checked without the platform that makes it.

**Windows (WGL).** `OpenGL/Tk/win32.py` is written: `wglChoosePixelFormatARB`
and `wglCreateContextAttribsARB`, with the dummy-context dance those two need
because the ARB entry points can only be resolved through a context that already
exists. What it needs is a run: `TEST_WINDOWING=tk python -m pytest tests` on a
Windows machine, which exercises the same suite X11 passes, and
`examples/tk_shader.py`, which is the core profile doing something only a core
profile can. Any correction belongs in that module; nothing above it should have
to change.

**macOS (Aqua).** Not implemented. Tk's Aqua windows are `NSView`s, and a
context is attached to one through Objective-C -- `NSOpenGLContext` over the CGL
layer `OpenGL/CGL` already binds. `AGL` is the Carbon-era API and is gone from
current SDKs, so it is not the way in. The work is `objc_msgSend` through
`ctypes`: get the `NSView` behind `winfo_id()`, build an `NSOpenGLPixelFormat`
from the same `ContextAttributes` the other two platforms translate, make the
context, and answer `makeCurrent` / `swapBuffers` / `setSwapInterval` from it.
`OpenGL/Tk/context.py` already dispatches on `tk windowingsystem`, so an `aqua`
implementation registers beside the other two and nothing else moves.

## Four defects it turned up

Each was found by needing it, and each is fixed with a test of its own.

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
