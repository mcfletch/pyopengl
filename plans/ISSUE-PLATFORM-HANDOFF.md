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

## Start here

Every ticket below that could be written from Linux has been. Nine of them now
need a run rather than a change, so the first pass on a Windows machine is one
command:

```
python -m pytest tests/
```

Green settles #144 and confirms the fixes for #174, #76, #125 and #7. The
cases that hold each are named under it. What no case can answer is the last
step in three of them -- whether the driver's GL is the one that arrived,
whether a GLUT the machine already had is found, whether the driver lists an
extension -- and each says below what to run by hand for that.

**That run has happened.** Windows 10, Python 3.13, an Intel UHD 630 with the
driver's own GL: 5511 passed, 633 skipped, and three failures the run itself
found. Two were defects and are fixed -- see *What the Windows run turned up*
below; the third was #144's answer, which is that it passes. Every by-hand
step named above has been taken and each is recorded under its ticket.

| Ticket | State | What is left |
|---|---|---|
| #174 | confirmed | Nothing; the driver's GL loads and outranks a `PATH` copy |
| #76, #125 | confirmed | Nothing; a freeglut on `PATH` under its own name is found |
| #7 | confirmed | Nothing; the extension lists and the swap interval round-trips |
| #144 | confirmed | Nothing; the case is green on Windows |
| #127 | guarded | Nothing here; a wheel from this tree carries the DLLs |
| #55 | fixed | One macOS run; the Windows half of its cases is now green |
| #29 | fixed | A 32-bit run to confirm |
| #139, #60 | — | A runner exists now; run it |
| #162 | — | Needs a person at an Apple Silicon Mac |

Each of the confirmed rows is now a comment to write on the ticket rather than
a question to answer. What that comment says is under *What to write back*.

### What the Windows run turned up

Neither is a ticket; both are cases that could not do their job on Windows,
found by being run there for the first time.

- **A framework path was built with the host's separator.**
  `_loadLibraryWindows` serves macOS and Windows both, and its macOS fallback
  composed `/System/Library/Frameworks/<name>.framework/<name>` with
  `os.path.join`, which spells it with backslashes on Windows. A macOS
  filesystem path has a slash in it whatever machine writes it down, so the
  join is `posixpath.join`; the two `TestAMacOSFramework` cases that hold #55
  now run on Windows as well as on macOS.
- **The numpy case asserted the simulation rather than the state.**
  `test_numpy_without_float128` builds the handler in a child with
  `numpy.float128` deleted, and guarded against a vacuous run by asserting
  something had been deleted. Windows numpy has no `float128` to delete --
  which is the machine #21 was reported from, and where the case is at its
  least vacuous. It asserts what the handler saw instead: that the attributes
  are absent, however they came to be.

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

The matrix now covers x86-64 and arm64 Linux, Intel and Apple Silicon macOS,
and x86-64 Windows. Two gaps remain, and they are the reason some tickets
below cannot be answered by pushing a branch:

- **No window server anywhere.** Every runner is headless: Linux renders
  through EGL's device platform, macOS through CGL, Windows through a WGL
  pbuffer. A ticket about a window being moved, resized, or driven from a
  second thread cannot be reproduced on any of them. #162 is one.
- **No GPU anywhere.** Every renderer in the matrix is a software one --
  llvmpipe on Linux and Windows, Apple's software renderer on macOS. So
  nothing here can answer a question about a driver, and #60 is a report
  *about* the software fallback rather than in spite of it. GitHub's GPU
  runners are larger runners, billed per minute and never free whatever the
  repository's visibility.
- **No 32-bit anything.** GitHub offers no i586 or armv7l runner, which is
  what #29 is about. See the note under it.

---

## Windows

### #174 — `opengl32.dll` should come from System32

**Fixed; needs confirming.** `_loadLibraryWindows` asked
`ctypes.util.find_library` first, which walks `PATH`.
`C:\Windows\System32\opengl32.dll` is a trampoline to whatever the graphics
driver installed, so it is the only correct one — and conda puts
`Library\bin`, which carries a Mesa `opengl32.dll`, ahead of System32 on
`PATH`. A conda user asking for their GPU's OpenGL got software rendering,
with nothing saying so.

`opengl32` and `glu32` now go to the loader bare, which is what the reporter
suggested: Windows' own search order reaches the system directory before
`PATH`. freeglut is deliberately not on that list, since where the user put it
is exactly what `PATH` is for.

- **The case**: `tests/bindings/platform/test_library_loading.py`, class
  `TestALibraryWindowsItselfProvides`. It runs on Linux, because what was
  wrong is the choice rather than the load.
- **Confirmed.** On Windows 10 with an Intel UHD 630,

  ```
  python -c "from OpenGL.GL import *; from OpenGL.GLUT import *; \
             glutInit(); glutCreateWindow(b'x'); print(glGetString(GL_RENDERER))"
  ```

  answers `Intel(R) UHD Graphics 630` on GL `4.6.0 - Build 31.0.101.2114` --
  the graphics card, not `llvmpipe` or `GDI Generic`.

  The conda half is the same question without needing conda: what conda does
  is put a directory holding an `opengl32.dll` ahead of System32 on `PATH`.
  With such a directory on `PATH`, `GetModuleFileNameW` on the handle PyOpenGL
  loaded answers `C:\WINDOWS\SYSTEM32\opengl32.DLL`, while
  `ctypes.util.find_library('opengl32')` -- the call this fix removed --
  answers the copy on `PATH`. That is the ticket in two lines: the old route
  reaches the decoy and the current one does not.

### #76, #125 — GLUT is not found on Windows

**Fixed; needs confirming.** Both are "`glutInit` or `glutInitDisplayMode` is
an undefined function on Windows", and #76 says why. The reporter downloaded
the official freeglut, put it on `PATH`, got the same error, and read the
source to find out that the only names asked for were `freeglut64.vc14` and
`glut64.vc14` — names nothing ships under but us. They renamed the file and it
worked.

`Win32Platform.GLUT_LIBRARY_NAMES` now asks for the names such a GLUT actually
has, and first: `freeglut`, which the official Windows binaries, MSYS2 and
vcpkg all install, and `glut32`, the original GLUT. The bundled builds follow.

- **The case**: `tests/bindings/glut/test_glut_library_names.py`, which holds
  the order and runs anywhere.
- **Confirmed.** With a freeglut on `PATH` under the name it ships with,
  `freeglut.dll`, and not renamed,

  ```
  python -c "from OpenGL.GLUT import *; glutInit(); print('ok')"
  ```

  prints `ok`, and `OpenGL.platform.PLATFORM.GLUT._name` names that file --
  so the one the user installed wins over the bundled build, which is what
  the reporter had to rename their copy to get. On a machine with no freeglut
  of its own the bare `freeglut` name finds nothing and
  `freeglut64.vc14.dll` from `OpenGL/DLLS` answers, so the fallback the
  bundling exists for is intact.
- **See also** #164 and `BUNDLED-DLLS.md`: whether to keep shipping the
  bundled builds at all is one decision for all four tickets.

### #127 — the DLLS folder is missing from an installation

**Guarded here; nothing left to write.** The thread answers itself with "the
DLLS folder is missing, copy one in yourself". A wheel built from this
checkout carries all eighteen files, so whatever produced that install was not
this configuration.

What was worth doing was asking the built artifact. `OpenGL/DLLS` is a
directory inside a package with no `__init__.py`, so `packages.find` does not
see it and it arrives only as package data — named in `MANIFEST.in` and not in
`[tool.setuptools.package-data]`, which works because `include-package-data`
defaults to true for a project configured through `pyproject.toml`. Every
Windows GLUT user depends on a default in another project's tool. Dropping
that one `MANIFEST.in` line removes all eighteen from the wheel with nothing
failing.

- **The case**: `tests/bindings/test_what_the_wheel_ships.py`. It builds the
  wheel and reads it, in about two seconds.
- **What is left**: nothing that needs Windows. If the ticket is answered, it
  is answered by asking the reporter where their PyOpenGL came from — conda,
  a distribution package, or PyPI.

### #144 — `glutCreateWindow` with a `str`

**Needs only a run.** The case exists:
`tests/bindings/glut/test_glut_window_title.py` holds the argument type of the
Windows route specifically — FreeGLUT there calls `exit()` on a fatal error, so
the binding goes through `__glutCreateWindowWithExit`, and that override
declaring the wrong title type is what made this a `ctypes.ArgumentError` on
Windows and nowhere else.

- **Confirmed.** The file is green on Windows 10 under Python 3.13, as is the
  rest of `tests/bindings` -- 4408 cases.

### #7 — WGL extensions not found under Python 3

**Fixed; needs one live call.** Reported fixed by the maintainer in 2020,
disputed by a second reporter, nobody since.

The str-versus-bytes handling the ticket describes was already right. Writing
the cases for it found something else: `pullExtensions` ends in
`except AttributeError: return []`, the answer for a platform that is not WGL,
and the lookup that raises it sat *outside* the `try`. The clause could never
run, so a `WGL_` specifier on a machine with no WGL raised out of whatever
import asked. Both lines are now inside it.

- **The case**: `tests/bindings/wgl/test_wgl_extension_query.py` — the list
  comes back as bytes, the entry point is asked for by a bytes name, a `str`
  and a `bytes` specifier both match, and the device context is declared `HDC`
  so a 64-bit handle keeps its top half.
- **Confirmed.** Against a real context on Windows -- an Intel UHD 630 --
  `WGLQuerier.pullExtensions()` answers 22 names, every one of them `bytes`,
  `WGL_EXT_swap_control` among them; the querier matches it given either a
  `str` or a `bytes` specifier; `glInitSwapControlEXT()` is true; and

  ```
  from OpenGL.WGL.EXT import swap_control
  swap_control.wglGetSwapIntervalEXT()
  ```

  answers, with `wglSwapIntervalEXT(0)` and `wglSwapIntervalEXT(1)` each read
  back by the getter.

---

## macOS

### #139 — segfaults and hangs on an Intel Mac

**`macos-13` added, not yet run.** It is the last Intel runner GitHub offers;
14 and 15 are both Apple Silicon, so nothing in the matrix could previously
have seen this.

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

**Fixed; needs one macOS run.** Big Sur stopped keeping the system libraries
as files, so checking for one by path fails. CPython's `find_library` learned
about the dynamic linker cache in 3.8.10 and 3.9.1, and `requires-python` here
is `>=3.9`, so every supported interpreter has that fix.

Nothing in `ctypesloader.py` checked a framework path, and there is now a
fallback for the machines where `find_library`'s heuristics come up empty:
`/System/Library/Frameworks/<name>.framework/<name>`, handed straight to
`dlopen`, because `dlopen` is what asks the cache.

- **The case**: `tests/bindings/platform/test_library_loading.py`, class
  `TestAMacOSFramework` — including that nothing asks whether the framework is
  a file, which is the whole of the ticket. It stands in for the loader, so it
  runs anywhere; running it on Windows is what found the `os.path.join` in the
  fallback, and it is green there now.
- **What is left**: the suite on any macOS runner, which is the half no
  stand-in can answer -- whether `dlopen` on that path reaches the cache. It
  is covered by the runs #139 and #60 need.

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

**Added, not yet run.** `test.yml` carries an `ubuntu-24.04-arm` row
(`py312-num1-accel1-dispc`), and the job takes its runner from
`matrix.runner`, defaulting to `ubuntu-latest`. The Mesa install and the EGL
device backend are unchanged; only the label differs.

- **What settles it**: that row green. Nothing here can run it.
- **What might not work**: the test dependencies. `glfw` and `pygame-ce` need
  aarch64 wheels or the tox environment will not build — the EGL backend needs
  neither, but tox installs the extra whole. If that is what fails, the answer
  is to mark them as x86-64 only rather than to drop the row.

### #173 — aarch64 wheels

**Added, not yet run.** `accelerate-manylinux.yml` builds on
`ubuntu-24.04-arm` as well, so cibuildwheel produces `manylinux_aarch64`
natively rather than under emulation.

- **What settles it**: an aarch64 wheel on PyPI that installs on the
  reporter's DGX Spark. A build is not the same as an install: the wheel
  should be tried on real hardware before the ticket is answered, and the job
  runs the test command cibuildwheel is given.

### #29 — `test_buffer_api_basic` on i586 and armv7l

**Fixed; needs a 32-bit run to confirm.** A distribution build in 2019, and
the traceback on the ticket says exactly what happened:
`assert '<l' in ['(3)<i', '(3)<l', '<i']`. The case listed the format strings
CPython reports for a `(GLint * 3)` and asserted the answer was one of them. A
4-byte signed int is a `c_long` on i586 and armv7l, so the letter is `l` and
the list did not have it.

#92 was the same failure on s390x, where the byte-order character is `>`, and
was fixed by branching on `sys.byteorder` — which left this half in place and
made the list one architecture longer.

`format_letter` in `tests/bindings/arrays/test_arraydatatype.py` now reads the
item-type letter out of the format string and the case asserts what the value
*is*: a signed integer, an unsigned one. No width is lost, because `itemsize`
is asserted on the line above and is what pins it.
`TestReadingAFormatString` covers the reader over the spellings both tickets
reported. A machine that reports a fifth one changes nothing.

- **What is left**: a 32-bit run, to confirm that nothing *after* the format
  assertion fails as well — the traceback stops at the first, so the shape and
  strides checks below it have never been seen on a 32-bit machine. GitHub
  offers no i586 or armv7l runner, so this is the one ticket here that no
  addition to the matrix reaches.

Three ways to get one, cheapest first:

1. **An emulated container.** `docker run --platform linux/arm/v7` with
   `qemu-user-static` registered gives armv7l on any x86-64 host, and
   `--platform linux/386` gives i586. Slow, and qemu is not the hardware, but
   it exercises the pointer width and the struct formats, which is what this
   ticket is about. Neither docker nor qemu is installed in the development
   container today.
2. **A Raspberry Pi.** A Pi 4 or Pi 5 on 32-bit Raspberry Pi OS is armv7l --
   the reporter's exact architecture, on real hardware. It brings two things
   no runner has: a real GPU and a real window server. That makes it the only
   machine discussed here that could also serve the GLES suite against a real
   driver, which is where several of the SBC reports came from (#137 and #166
   from OrangePi boards, #158 from a Pi Zero W, #145 from a Pi 5). It does
   *not* answer #135, which asks for hosted runners, and a Pi as a
   self-hosted runner on a public repository would let a fork's pull request
   run arbitrary code on it.
3. **A distribution packager.** #29 came from one, and openSUSE and Debian
   both still build for 32-bit arm. The reporter of #141 builds the Debian
   package and has been responsive.

---

## What to write back

Each of these ends in a comment on the ticket, and
[RELEASE-NOTES-4.0.0b1-ISSUES.md](../RELEASE-NOTES-4.0.0b1-ISSUES.md) is the
model: what was actually wrong, the case that holds it, the commit, and the
release. Where a ticket turns out not to reproduce, say so with what was tried
and on what — an old report closed with "cannot reproduce" and no detail is
worth less than one left open.
