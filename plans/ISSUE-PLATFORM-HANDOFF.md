# Tickets that need a machine this container is not

The issue pass in [ISSUE-TRIAGE.md](ISSUE-TRIAGE.md) answered every ticket it
could from a Linux container. This is what is left that needs Windows, macOS
or an arm machine, written so that somebody sitting at one can pick a ticket
up without reading the rest of the tracker.

One section per ticket. Each says what the reporter saw, what would settle it,
where the test lives or would go, and what to paste back. Where the work can
be started here, it says so and how far it goes: several of these are only
*confirmed* off-platform, and the fix is ordinary Python that can be written
and tested anywhere.

## Running the suite somewhere else

CI is `.github/workflows/test.yml`. It runs on a push to `develop` or to any
`issue/**` branch, and on a manual dispatch against any ref:

```
git switch -c issue/144-glut-window-title
git push -u origin issue/144-glut-window-title      # runs the whole matrix
gh workflow run test.yml --ref issue/144-glut-window-title \
    -f platforms=windows -f tests=tests/bindings/glut
```

`platforms` is `all`, `linux`, `macos` or `windows`; `tests` narrows what runs.
A ticket about one platform does not need the other two, and the Linux matrix
alone is thirteen jobs.

On a developer's own machine the suite needs no CI:

```
python -m pytest tests/                      # picks a windowing backend
TEST_WINDOWING=wgl python -m pytest tests/   # Windows, headless pbuffer
TEST_WINDOWING=cgl python -m pytest tests/   # macOS, no window server
```

`python tests/check_wgl_offscreen.py` says whether a Windows machine can serve
the headless backend, and names the WGL extensions it lacks if not.
`python tests/report_cgl_context.py` says which GL version each profile
actually hands back on a Mac.

## What the CI matrix does not cover

Worth knowing before picking a ticket up, because two of these cannot be
answered by pushing a branch:

- **No window server anywhere.** Every runner is headless: Linux renders
  through EGL's device platform, macOS through CGL, Windows through a WGL
  pbuffer. A ticket about a window being moved, resized, or driven from a
  second thread cannot be reproduced on any of them.
- **macOS runners are Apple Silicon.** `macos-14` and `macos-15` both are. An
  Intel Mac needs `macos-13` adding to the matrix.
- **No arm Linux runner yet**, and no GPU on any of them: GitHub's GPU runners
  are larger runners, billed per minute and never free.

---

## Windows

### #174 — `opengl32.dll` should come from System32

**Can be started here.** The fix is ordinary Python; only the confirmation
needs Windows.

`OpenGL/platform/ctypesloader.py:_loadLibraryWindows` asks
`ctypes.util.find_library` first, which walks `PATH`. The reporter's point is
that `C:\Windows\System32\opengl32.dll` is a trampoline to whatever the
graphics driver installed, so it is always the right one — and conda puts
`Library\bin`, which carries a Mesa `opengl32.dll`, ahead of System32 on
`PATH`. A conda user therefore gets software rendering with nothing saying so.

- **Where the test goes**: `tests/bindings/platform/`, driving
  `_loadLibraryWindows` with a stubbed `find_library` and loader. That runs on
  Linux, because what is wrong is the choice, not the load.
- **What settles it**: the same suite on a Windows runner, plus somebody with
  a conda environment confirming they get the driver's GL.
- **Branch**: `issue/174-opengl32-from-system32`

### #76, #125, #127 — GLUT is not found on Windows

**Can be started here.** All three are "`glutInit` or `glutInitDisplayMode` is
an undefined function on Windows", and #127's thread answers itself: "The
DLLS folder is missing."

The package does ship freeglut: `OpenGL/DLLS/` holds `freeglut32/64` for
vc9, vc10 and vc14, and a wheel built from this checkout contains 18 such
members. So the question is not whether they are shipped but why those users
had none — a wheel built differently, an installer that dropped them, or
`DLL_DIRECTORY` not being consulted.

- **Where the test goes**: a packaging case beside
  `tests/bindings/test_accelerate_generated_c.py::TestWhatTheSdistShips`,
  asserting the wheel carries `OpenGL/DLLS/*.dll`; and a
  `tests/bindings/glut/` case that the loader looks in `DLL_DIRECTORY`.
- **What settles it**: `pip install` of the built wheel on a clean Windows
  box, then `python -c "from OpenGL.GLUT import *; glutInit()"`.
- **See also** #164, which is ClamAV flagging two of those same DLLs as a
  packer. Whether these are still worth shipping at all is one decision for
  all four tickets.
- **Branch**: `issue/127-windows-glut-dlls`

### #144 — `glutCreateWindow` with a `str`

**Needs only a run.** The case exists:
`tests/bindings/glut/test_glut_window_title.py` holds the argument type of the
Windows route specifically — FreeGLUT there calls `exit()` on a fatal error, so
the binding goes through `__glutCreateWindowWithExit`, and that override
declaring the wrong title type is what made this a `ctypes.ArgumentError` on
Windows and nowhere else.

- **What settles it**: that file green on a Windows runner.
- **Branch**: none needed; a dispatch of `develop` with
  `platforms=windows tests=tests/bindings/glut` answers it.

### #7 — WGL extensions not found under Python 3

**Partly startable here.** Reported fixed by the maintainer in 2020 and
disputed by a second reporter, with nobody since. The querier's string
handling in `OpenGL/raw/WGL/_types.py` is testable anywhere; whether
`wglGetExtensionsStringARB` then answers is not.

- **Where the test goes**: `tests/bindings/wgl/`.
- **What settles it**: `from OpenGL.WGL.EXT import swap_control;
  swap_control.wglGetSwapIntervalEXT()` against a real context on Windows.
- **Branch**: `issue/7-wgl-extension-strings`

---

## macOS

### #139 — segfaults and hangs on an Intel Mac

**Needs a matrix change first.** `macos-14` and `macos-15` are both Apple
Silicon, so the current matrix cannot see this. Adding `macos-13` is the
first step and is a one-line change here.

The report is 3.1.8 segfaulting in the suite on Python 3.11 and 3.12, and
`master` at the time failing a lot and then hanging. The suite has moved a
long way since; the honest first move is to run it and see.

- **What settles it**: the whole suite on `macos-13`. The job already
  collects crash reports (`~/Library/Logs/DiagnosticReports`) and uploads them
  as an artifact, so a segfault arrives with its faulting frame.
- **Branch**: `issue/139-intel-mac`

### #60 — no accelerated renderer, then a segfault

**Needs only a run.** pyqtgraph's maintainer reporting their macOS CI dying in
`paintGL` after "Unable to create basic Accelerated OpenGL renderer".

Our macOS jobs are exactly that machine: a runner with no accelerated renderer
and no window server. If PyOpenGL segfaults there, we own it; if it does not,
the answer is about how a program should detect the software fallback, and
`report_cgl_context.py` already prints what CGL hands back.

- **What settles it**: the suite green on `macos-14`/`macos-15`, plus a note
  on the ticket about detecting the fallback.

### #55 — Big Sur's dyld cache

**Probably answerable without a Mac.** The reporter's point was that Big Sur
stopped keeping dynamic libraries as files, so checking for one by path fails
— and that CPython fixed this in 3.8.10 and 3.9.1. `requires-python` here is
`>=3.9`, so every supported interpreter has the fix.

- **What settles it**: reading `ctypesloader.py` for a remaining
  `os.path.isfile` on a framework path, and one macOS run.

### #162 — rendering from a thread on an M3

**No runner can answer this.** It needs a window to resize, and every runner
is headless. It also only happens sometimes, and more often at higher frame
rates.

- **What it needs**: somebody at an Apple Silicon Mac running the reporter's
  `test_minimal.py` (attached to the ticket: two windows, each with an update
  and a render thread, GLFW).
- **What to look for**: the errors quoted are Metal's
  (`A command encoder is already encoding to this command buffer`), which
  suggests Apple's GL-on-Metal layer rather than PyOpenGL — but that is a
  conclusion to reach from a backtrace, not to assume. `faulthandler` plus the
  crash report in `~/Library/Logs/DiagnosticReports` is what turns it into
  one.
- **Branch**: `issue/162-threaded-rendering-macos`

---

## Other architectures

### #135 — arm64 runners

**The change is writable here.** GitHub's `ubuntu-24.04-arm` and
`ubuntu-22.04-arm` runners are free for public repositories. Adding one row to
the Linux matrix is the whole of it; the job's Mesa install and EGL device
backend work unchanged.

- **What settles it**: a green arm64 row.
- **Branch**: `issue/135-arm64-runner`

### #173 — aarch64 wheels

**Depends on #135**, and on `accelerate-manylinux.yml` rather than the test
workflow: the accelerator is the only part with anything to compile. Once
there is an arm64 runner, cibuildwheel builds `manylinux_aarch64` on it
natively rather than under emulation.

- **What settles it**: an aarch64 wheel on PyPI that installs on the
  reporter's DGX Spark.
- **Branch**: `issue/173-aarch64-wheels`

### #29 — `test_buffer_api_basic` on i586 and armv7l

**Partly startable here.** A 32-bit failure in the buffer format strings, from
a distribution build in 2019. #92 was the same shape on s390x and was fixed by
having the case read `sys.byteorder` rather than assuming little-endian; this
one is about pointer width rather than byte order, and the same treatment
probably applies.

- **Where the test goes**: `tests/bindings/arrays/test_arraydatatype.py`,
  which is where #92's fix went.
- **What settles it**: a 32-bit run. No hosted runner offers one, so this is a
  distribution packager or an emulated build.
- **Branch**: `issue/29-32-bit-buffer-formats`

---

## What to write back

Each of these ends in a comment on the ticket, and
[RELEASE-NOTES-4.0.0b1-ISSUES.md](../RELEASE-NOTES-4.0.0b1-ISSUES.md) is the
model: what was actually wrong, the case that holds it, the commit, and the
release. Where a ticket turns out not to reproduce, say so with what was tried
and on what — an old report closed with "cannot reproduce" and no detail is
worth less than one left open.
