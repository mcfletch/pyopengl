# PyOpenGL project plan

An index of what is planned, in progress and landed, so that the documents
beside it can be found without reading all of them. Each row's summary is that
document's own account of itself; the document is the detail.

**Status legend:** ✅ **Landed** — shipped, nothing outstanding · 🟡 **Partial**
— core landed, named pieces still missing · 📋 **Planned** — has a plan
document, not yet built · ⬜ **Todo** — wanted, no plan document yet.

| Plan | Status | Summary |
|------|--------|---------|
| [BUNDLED-DLLS.md](BUNDLED-DLLS.md) | 📋 Planned | **Eighteen vendored Windows binaries ship in every wheel on every platform.** freeglut and GLE, for vc9, vc10 and vc14 in 32- and 64-bit, none rebuilt in about a decade, none of them ours. A Linux server rendering through EGL downloads six freeglut builds it can never load, and a scanner has already objected to two of them (#164) in a way we cannot answer because we did not build them. They come out into `PyOpenGL-glut-binaries`, asked for as `pip install PyOpenGL[glut]`. The deciding work is not the packaging but the error: `glutInit` with no library has to name the extra, or a working program becomes a puzzle. Settles #164 and gives #76, #125 and #127 an answer either way. |
| [C-DISPATCH.md](C-DISPATCH.md) | ✅ Landed | Replacing the ctypes call path with C generated from the Khronos registry, at measured parity with an empty Python function call, across the ~3,500 registry-defined entry points in `OpenGL/raw`. Shipped in `PyOpenGL_accelerate`; `OpenGL.dispatch.status()` says which implementation a process got and why. |
| [TK-WIDGET.md](TK-WIDGET.md) | 🟡 Partial | `OpenGL.Tk` makes its own context rather than wrapping Togl, a Tcl C extension a user had to build. X11 and Windows landed and verified; macOS is the platform still to land, and is wanted for the next release. |
| [GLGET-SIZES.md](GLGET-SIZES.md) | ✅ Landed | A recorded `glGet` output size that is shorter than what the driver writes is a heap overrun. Two tessellation pnames were recorded one value each where the driver writes two and four; `tests/gl/test_glget_sizes.py` now walks the whole shipped table against the live driver. |
| [TEST-SUITE.md](TEST-SUITE.md) | 🟡 Partial | The suite reviewed as software in its own right. Much has since landed — the directory layout, the windowing backends, the check-script runner — and the document is the record of what that was for. |
| [FREE-THREADING.md](FREE-THREADING.md) | 📋 Planned | The pure-Python package runs on a free-threaded interpreter; what it does not do is let one *stay* free-threaded. What the nine Cython modules and the C dispatch layer need before they can declare support. Nothing measured on a free-threaded build yet. |
| [ISSUE-TRIAGE.md](ISSUE-TRIAGE.md) | ✅ Landed | A verdict for every one of the 80 open tracker issues: reproducible here, needs a platform CI has, needs something neither has, or not a defect. The pass it describes closed 15 with a test red first and held 26 more. |
| [ISSUE-PLATFORM-HANDOFF.md](ISSUE-PLATFORM-HANDOFF.md) | 📋 Planned | The tickets left needing Windows, macOS or an arm machine, written so somebody at one can pick a ticket up: what the reporter saw, what would settle it, where the test goes, and the branch to push. Records which two no runner can answer, and why. |

## Not yet written down

Wanted, with no plan document:

- **Historical release tags.** `tools/release.py` tags every release it makes,
  so this is closed going forward; the tags #77 asks for cover releases made
  before that and have to be reconstructed from the changelog.
- **The remaining open tickets that need a person rather than a machine.**
  Twelve reports — #32, #54, #59, #61, #73, #82, #105, #115, #124, #132, #167,
  #170 — describing a machine, program or driver in too little detail to
  reproduce, several of them years old. Each wants one specific question
  asked, not a silent close.
