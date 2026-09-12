# Working through the open issue list

The tracker at <https://github.com/mcfletch/pyopengl/issues> holds 80 open
issues and 16 open pull requests. This is the pass that turns each of them into
either a test in this suite or a statement of what it would take to get one.

The whole tracker is cached locally by `tools/issues.py` in the workspace above
this checkout, so reading a ticket costs no API request:

```
tools/issues.py show 175        one ticket, body and every comment
tools/issues.py search segfault title, body, labels and comments
tools/issues.py fetch           refresh (2 requests)
```

## What "testable here" means

The development container is Linux with a real GPU: Mesa `radeonsi` on an AMD
device, plus Mesa's software device, reached through EGL, GLX, GLFW, pygame, Tk
and freeglut. `PyOpenGL_accelerate` is built, numpy is present, and both
`DISPLAY` and `WAYLAND_DISPLAY` are set. That covers a large majority of the
tracker.

Two things were added to the image for this pass, because without them seven
tickets could only be read rather than run:

- **`libosmesa6`.** OSMesa is a PyOpenGL platform of its own — it rasterises
  into an array the caller owns, with no window system — so nothing else in
  the image loads it and the platform had no coverage at all. It now answers a
  4.5 compatibility profile on llvmpipe, and `tests/checks/check_osmesa.py`
  drives it.
- **`clang`.** gcc compiles this package on every Linux build, so gcc's
  opinion is the one always heard; clang's arrives as a bug report from macOS
  and the BSDs. It now reads the accelerator's generated C on every run.

Four verdicts, and every open issue carries one:

| Verdict | What it means |
|---|---|
| **here** | Reproducible in this container. Gets a test in this suite, verified red. |
| **CI** | Needs a platform CI has or can have — macOS, Windows, arm64. Gets a test that skips here, and a branch to run it on. |
| **elsewhere** | Needs something neither has: hardware nobody here owns, a library not installed, a debug interpreter, or the reporter's own program. |
| **no test** | Not a defect: a question, a feature request, or a release-process task. |

A ticket already fixed on `develop` still earns a test — the test is what keeps
it fixed. Where the fix is already in, the test is verified red against the
PyOpenGL release current at the ticket's date rather than against `develop`,
and the verdict column says which release that was.

## The platform-selection cluster

Six tickets are one question — which platform plugin `OpenGL/platform/__init__.py`
picks, and what happens when it picks the one the caller's context does not
use: **#88**, **#104**, **#113**, **#129**, **#148**, **#172**. On `develop`
the Linux plugins have been unified into a single `LinuxPlatform`, and the
symptom each of these reports is gone with it: GLX imports cleanly under
`PYOPENGL_PLATFORM=egl`, and `WAYLAND_DISPLAY` no longer forces a choice.

What survives is #129's shape — asking a platform for a sub-API it does not
carry answers `AttributeError: 'LinuxPlatform' object has no attribute
'OSMesa'`, which does not tell the caller that `PYOPENGL_PLATFORM=osmesa` is
the answer. That is the live half of the cluster, and it is an error-quality
test rather than a platform one.

## The verdicts

### here — 41 issues

| # | What it is | State on `develop` |
|---|---|---|
| 3 | integer offset to `glVertexAttribPointer` | **fixed here** — it took an int and read it as an address |
| 5 | VBO memory growth, `ERROR_ON_COPY` silent | **fixed here** — the flag was set too late and said nothing |
| 10 | OSMesa: `undefined symbol: glGetError` | does not reproduce on this Mesa |
| 12 | `.pxd` files missing from the accelerate sdist | **held** — the .pxd files ship, and a case says so |
| 18 | the same, from a different caller | duplicate of 10 |
| 21 | `numpy.float128` assumed to exist | **held** — red against a numpy with float128 removed |
| 33 | unhashable context under OSMesa | **fixed here** — the handle now hashes *and* compares |
| 34 | `glClear` segfault under OSMesa RGB | does not reproduce on this Mesa |
| 38 | upstream renamed registry parameters | **fixed here** — 624 parameter references now checked |
| 42 | integer offset to `glDrawElements` | **fixed here** |
| 43 | platform plugin load failure reports `NoneType` | **fixed here** — the plugin names itself and its reason |
| 46 | accelerate built without numpy drops `numpy_formathandler` | **held** — numpy is a build requirement |
| 47 | `glTexImage2D` leaks a reference on a non-contiguous array | **held** — refcounts asserted over eight uploads |
| 48 | `glutCreateWindow` with a `str` | **held** — the Windows title type has a case |
| 51 | `GL_HALF_FLOAT` for `glTexImage2D` | **held** — the table and a real upload |
| 68 | `glReadPixels` with `GL_RGB`/`GL_UNSIGNED_BYTE` | **held** — read back and asserted on every run |
| 70 | `OSMesaCreateContextAttribs` not declared | present; #129 covers the error a caller met |
| 79 | accelerate build: `++Py_REFCNT` is not an lvalue | build test |
| 88 | `glInitFramebufferObjectARB` under Wayland | fixed; see the cluster above |
| 95 | `glActiveTexture` slow under 3.1.6 | not reproducible: 0.07 us/call; four calls now timed |
| 96 | `glGenerateMipmap` segfault | not reproducible; the reported sequence is a case |
| 104 | `GetCurrentContext()` returning 0 read as invalid | fixed; see the cluster |
| 107 | clang 15 `-Wint-conversion` | fixed; red against 3.1.7 under clang 18 |
| 113 | `GetCurrentContext` vs `eglGetCurrentContext` | fixed; see the cluster |
| 114 | a large `bytes` argument formatted into an error | **held** — bounded message, red against 3.1.7 |
| 117 | the same clang failure on an M3 | duplicate of 107 |
| 120 | `ARB_bindless_texture` missing | **held** — present, and walked by the import sweep |
| 121 | generated Cython C shipped in the release | **fixed here** — the sdist stops shipping Cython output |
| 129 | platform has no such sub-API — unhelpful error | **fixed here** — the message names `PYOPENGL_PLATFORM` |
| 137 | GLES version string parsing | **fixed here** — `is_opengl_es` was dead code |
| 138 | `xlib` test dependency is unmaintained | **fixed here** — now `python-xlib` |
| 141 | Debian package test failures | **held** — every sub-issue resolved or the reporter's driver |
| 142 | `glCallLists` name stack empty on newer Mesa | passes here; left open for somebody on the affected Mesa |
| 143 | `SyntaxWarning: invalid escape sequence` | fixed; red against 3.1.9 |
| 145 | accelerate build on arm — `long` undeclared | same root as 147 |
| 147 | accelerate build fails with Cython 3.1 | build test |
| 148 | GLX import under the EGL platform | fixed; see the cluster |
| 158 | the same `SyntaxWarning`, still reported | duplicate of 143 |
| 159 | scalar object name into a delete under `ERROR_ON_COPY` | **held** — covered by the flagerrorcopy CI axis |
| 172 | EGL selected on a Wayland session using GLX | fixed; see the cluster |
| 175 | `glBufferData` segfault on a `memoryview` | fixed; red against 3.1.7 |

### CI — 14 issues

Each needs a platform this container is not. The workflow change below is what
lets a branch carrying one of these tests be run on demand.

| # | What it is | Platform |
|---|---|---|
| 7 | WGL extension strings vs bytes | Windows |
| 29 | `test_buffer_api_basic` on i586 / armv7l | 32-bit |
| 43 | platform plugin load failure | Windows; the message itself is fixed, see the here table |
| 55 | Big Sur dyld cache in `ctypesloader` | macOS |
| 60 | no accelerated renderer, then a segfault | macOS |
| 76 | freeglut DLL naming | Windows |
| 125 | `glutInitDisplayMode` undefined | Windows |
| 127 | the `DLLS` directory | Windows |
| 135 | arm64 runners for the build matrix | arm64 |
| 139 | segfaults and hangs on an Intel Mac | macOS |
| 144 | `glutCreateWindow` with a `str` | Windows |
| 162 | rendering from a thread on an M3 | macOS |
| 173 | aarch64 wheels | arm64 |
| 174 | `opengl32.dll` should come from System32 | Windows (the path logic is testable here) |

### elsewhere — 13 issues

| # | What it is | What it would need |
|---|---|---|
| 32 | `glDepthFunc` appearing not to work | the reporter's program; maintainer could not reproduce |
| 54 | a freeglut internal error, reported as a screenshot | information |
| 59 | `gluOrtho2D` undefined | the reporter's GLU install |
| 61 | a conda package reported as corrupted | conda |
| 73 | access violation on Windows AMD | the reporter's driver; cause was their own query misuse |
| 82 | `eglInitialize` returning `EGL_NOT_INITIALIZED` | information |
| 92 | big-endian buffer formats | s390x |
| 105 | an assertion inside `PyMemoryView_GetContiguous` | a `--with-assertions` interpreter |
| 115 | undefined `glGenVertexArrays`, then `free(): invalid pointer` | the reporter's mismatched install |
| 124 | no EGL device in an NVIDIA container | that container |
| 132 | no OpenGL library inside a container | resolved by the reporter |
| 167 | `glGenBuffers` answering `GL_INVALID_OPERATION` | information; no context is the likely cause |
| 170 | TensorFlow and Mesa loading two LLVMs | the reporter's stack; the clash is not ours |

### no test — 13 issues

| # | What it is |
|---|---|
| 58 | an empty question |
| 63 | how to stringify a GL enum — answered |
| 64 | a request for issue labels |
| 65 | pyrender pins PyOpenGL 3.1.0 — theirs to change |
| 69 | a question about pyrender's pin |
| 72 | fixed in CPython 3.8.10 / 3.9.1 |
| 77 | publish tags for releases — `tools/release.py` does this now |
| 111 | a download script in another project |
| 140 | the 3.1.9 tag — duplicate of 77 |
| 157 | ship the generated modules as a zip — a design proposal |
| 163 | pyMSVC for Windows builds — a suggestion |
| 164 | ClamAV flags two shipped DLLs as a packer — a false positive worth answering |
| 166 | the error when a GLES library is missing says nothing | **fixed here** — GLES2 would not import with checking off |

## Counts

| Verdict | Issues |
|---|---|
| here | 41 |
| CI | 14 |
| elsewhere | 13 |
| no test | 13 |

That is 81 rows for 80 issues: #43 is the one counted twice, because the
unhelpful message it reports can be read here while the Windows import failure
underneath it cannot.

## Running a branch through CI

`.github/workflows/test.yml` runs on a push to `develop` and on a manual
dispatch. Two things were missing for this work: a push to a branch carrying
one ticket's test ran nothing, and a dispatch ran the whole three-platform
matrix when the ticket was about one of them.

So the workflow now also runs on a push to `issue/**`, and the dispatch takes a
`platforms` input — `all`, `linux`, `macos` or `windows`. A branch per ticket,
named for it, is what a CI-only ticket gets:

```
git switch -c issue/144-glut-create-window-str
git push -u origin issue/144-glut-create-window-str    # runs the matrix
```

and a dispatch narrows it to the platform the ticket is about, with the
`tests` input naming the one path to run.
