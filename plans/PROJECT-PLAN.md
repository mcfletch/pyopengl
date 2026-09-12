# PyOpenGL project plan

An index of what is planned, in progress and landed, so that the documents
beside it can be found without reading all of them. Each row's summary is that
document's own account of itself; the document is the detail.

**Status legend:** ✅ **Landed** — shipped, nothing outstanding · 🟡 **Partial**
— core landed, named pieces still missing · 📋 **Planned** — has a plan
document, not yet built · ⬜ **Todo** — wanted, no plan document yet.

| Plan | Status | Summary |
|------|--------|---------|
| [BUNDLED-DLLS.md](BUNDLED-DLLS.md) | 🟡 Partial | **Eighteen vendored Windows binaries ship in every wheel on every platform.** freeglut and GLE, for vc9, vc10 and vc14 in 32- and 64-bit, none rebuilt in about a decade. A Linux server rendering through EGL downloads six freeglut builds it can never load, and a scanner has already objected to two of them (#164), which quarantines PyOpenGL itself for users who never wanted GLUT. They come out into `PyOpenGL-glut-binaries`, a separate GitHub project with its own releases under the PyOpenGL umbrella, so still ours but an optional include, asked for as `pip install PyOpenGL[glut]`. The deciding work is not the packaging but the error: `glutInit` with no library has to name the extra, or a working program becomes a puzzle. Settles #164 and gives #76, #125 and #127 an answer either way. The new project exists in the workspace and PyOpenGL finds it where it is installed, falling back to `OpenGL/DLLS` where it is not; what is left is the GitHub repository, the first PyPI release, and then — only then — the extra, the message and the deletion. |
| [C-DISPATCH.md](C-DISPATCH.md) | ✅ Landed | Replacing the ctypes call path with C generated from the Khronos registry, at measured parity with an empty Python function call, across the ~3,500 registry-defined entry points in `OpenGL/raw`. Shipped in `PyOpenGL_accelerate`; `OpenGL.dispatch.status()` says which implementation a process got and why. |
| [TK-WIDGET.md](TK-WIDGET.md) | 🟡 Partial | `OpenGL.Tk` makes its own context rather than wrapping Togl, a Tcl C extension a user had to build. X11 and Windows landed and verified; macOS is the platform still to land, and is wanted for the next release. |
| [GLGET-SIZES.md](GLGET-SIZES.md) | ✅ Landed | A recorded `glGet` output size that is shorter than what the driver writes is a heap overrun. Two tessellation pnames were recorded one value each where the driver writes two and four; `tests/gl/test_glget_sizes.py` now walks the whole shipped table against the live driver. |
| [TEST-SUITE.md](TEST-SUITE.md) | 🟡 Partial | The suite reviewed as software in its own right. Much has since landed — the directory layout, the windowing backends, the check-script runner — and the document is the record of what that was for. |
| [FREE-THREADING.md](FREE-THREADING.md) | 📋 Planned | The pure-Python package runs on a free-threaded interpreter; what it does not do is let one *stay* free-threaded. What the nine Cython modules and the C dispatch layer need before they can declare support. Nothing measured on a free-threaded build yet. |
| [ISSUE-TRIAGE.md](ISSUE-TRIAGE.md) | ✅ Landed | A verdict for every one of the 80 open tracker issues: reproducible here, needs a platform CI has, needs something neither has, or not a defect. The pass it describes closed 15 with a test red first and held 26 more. |
| [STATIC-GATES.md](STATIC-GATES.md) | ✅ Landed | A reading of the 132 fixes among the last three years' commits, sorted by what kind of defect each was, and eleven gates that would refuse the ones a tool reading the tree can settle: an error path nothing has entered, a foreign function with no prototypes, two sibling modules that drifted, a flag read somewhere other than where it is set, a test that cannot fail, a declared gate nothing runs. Seven live in `tests/gates/` and run on every row of the matrix; three are somebody else's tool behind a tox environment of their own. They found twelve defects on the way in, among them a public classmethod that raised `TypeError` wherever the accelerators are installed, an ES coverage report that had been printing 0% of nothing, and four documented environment variables that did nothing. Also names the classes a parser cannot answer, so that the matrix keeps the work that is the matrix's. |
| [ISSUE-PLATFORM-HANDOFF.md](ISSUE-PLATFORM-HANDOFF.md) | 🟡 Partial | The tickets needing Windows, macOS or an arm machine, written so somebody at one can pick a ticket up: what the reporter saw, what would settle it, and which case holds it. Everything that could be written from Linux has been, so nine of them now need a run rather than a change and the document opens with the one command that settles most. The Windows pass has been made on a machine with a real driver: #174, #76, #125, #7 and #144 are confirmed, and running the cases there found two that could not do their job on Windows — a macOS framework path composed with the host separator, and a numpy case that asserted its own simulation. What is left wants machines this workspace has none of: macOS for #139, #60, #55 and #162, arm for #135 and #173, and 32-bit for #29. |

## Not yet written down

Wanted, with no plan document:

- **Historical release tags.** `tools/release.py` tags every release it makes,
  so this is closed going forward; the tags #77 asks for cover releases made
  before that and have to be reconstructed from the changelog.
- **The remaining open tickets that need a person rather than a machine.**
  Nine reports — #32, #61, #73, #82, #105, #124, #132, #167, #170 —
  describing a machine, program or driver in too little detail to reproduce,
  several of them years old. Each wants one specific question asked, not a
  silent close. #54, #59 and #115 have left this list: all three were
  `NullFunctionError` saying the same thing for three different problems, and
  the message now tells them apart.
