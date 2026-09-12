# The bundled Windows DLLs become an optional package

**Status:** Proposed. Nothing has landed.

**Scope:** `OpenGL/DLLS/`, which is eighteen files — freeglut for vc9, vc10 and
vc14 in 32- and 64-bit, the GLE tubing library in the same six flavours, and
their licence and readme files. Every wheel and every sdist of PyOpenGL
carries all of them, on every platform.

They come out into a package of their own, and a caller who wants them asks:

```
pip install PyOpenGL[glut]
```

**PyOpenGL remains the provider.** The new package is a GitHub project of its
own, with its own release process, created and managed under the same umbrella
as PyOpenGL — a Windows user who asks for GLUT gets the same builds from the
same people as today. What changes is that they are an optional include rather
than something every install carries. This is not a step towards dropping
them.

## Why

**Every install carries them, whether it can use them or not.** They are in
the pure-Python `py3-none-any` wheel, so a Linux server rendering headlessly
through EGL downloads six freeglut builds it can never load. GLUT is a 1990s
windowing toolkit that a new program has no reason to choose over GLFW, pygame
or Qt; GLE is a tubing library that one module (`OpenGL.GLE`) wraps. Both
still have users, and those users keep getting them — by asking.

**A scanner has already objected.** #164 is ClamAV reporting
`gle32.vc14.dll` and `freeglut32.vc9.dll` as `PUA.Win.Packer.NspackDotnetNor-2`.
Almost certainly a false positive — the files have not changed in ten years —
and hard to answer from the files alone, since they are vendored builds from
compilers three generations old (vc9 is Visual Studio 2008). It will recur. As
long as the files are in the core wheel, a corporate scanner that quarantines
them quarantines PyOpenGL itself, for users who never wanted GLUT; once they
are an extra, the objection lands on a package only GLUT users install, and
PyOpenGL installs cleanly everywhere.

**The bundling does not even work reliably.** #76, #125 and #127 are all
Windows users finding GLUT absent, and #127's own thread answers it with "the
DLLS folder is missing." Whatever went wrong for them, the mechanism that is
supposed to make this seamless did not — so the cost is being paid without the
benefit being delivered.

## Against

Recorded because the decision is not free.

**It will break somebody's install.** A Windows program doing `glutInit()`
today works with `pip install PyOpenGL` and will need `PyOpenGL[glut]`. That
is a real break for the tutorials, textbooks and course materials that use
GLUT precisely because it was the thing that worked out of the box, and their
authors will not update them.

**GLUT is what beginners meet first.** Much of the material that teaches
OpenGL in Python teaches it through GLUT. Making it an extra puts a step
between a beginner and a triangle on screen, and the error they get when they
skip that step has to be worth reading.

The answer to both is the same: the error. `glutInit` with no library must say
`pip install PyOpenGL[glut]`, not `NullFunctionError`. That is the deciding
piece of work, not the packaging.

**Half of that has landed.** `NullFunctionError` now tells the three cases
apart, and where the library itself is absent it names the library and where
to get it — `OpenGL.platform.baseplatform.LIBRARY_SOURCES` holds the wording,
one entry per library, and `tests/bindings/platform/test_missing_library_errors.py`
holds it. So what this change needs is the GLUT entry's wording changed from
"PyOpenGL bundles builds in OpenGL/DLLS" to `pip install PyOpenGL[glut]`, not
a mechanism built. Same for GLE.

## Shape

**`PyOpenGL-glut-binaries`** — a new distribution, `win32`/`win_amd64` wheels
only, containing the DLLs and nothing else. Its own GitHub repository and its
own release process, created and maintained under the PyOpenGL umbrella, and
a submodule of this workspace like the other projects. Not pure-Python: the
point of the split is that a Linux user never downloads it, and only a
platform-tagged wheel achieves that.

**`PyOpenGL[glut]`** — an extra that requires it, on Windows only:

```toml
[project.optional-dependencies]
glut = ["PyOpenGL-glut-binaries; sys_platform == 'win32'"]
```

**`ctypesloader.DLL_DIRECTORY`** stops being a directory inside `OpenGL/` and
becomes a lookup of the new package where it is installed, falling back to
what it does today. The search order a user needs is unchanged: a freeglut the
*system* provides still wins, because a user who installed one meant it.

**The error is the deliverable.** `OpenGL.GLUT`'s null-function path grows a
message naming the extra, the way the platform errors fixed for 4.0.0b1 name
`PYOPENGL_PLATFORM`. Same for `OpenGL.GLE`. Without that this is a change that
turns a working program into a puzzle.

## Doing it

1. A case asserting the wheel carries no `.dll` at all — red first, and the
   thing that keeps them out afterwards. Beside the sdist cases in
   `tests/bindings/test_accelerate_generated_c.py::TestWhatTheSdistShips`.
2. A case that `glutInit` with no library raises something naming
   `PyOpenGL[glut]`. Red first; it is the whole compatibility story. The
   mechanism is already there — see *Half of that has landed* above — so this
   is `LIBRARY_SOURCES['GLUT']` and the case that reads it.
3. The new project: its repository, its CI and release workflow, and its first
   release to PyPI, built from the files as they stand. No rebuild: a rebuild
   is a separate decision with its own risk, and doing both at once makes any
   regression unattributable.
4. The extra, the loader change, and the messages.
5. `OpenGL/DLLS/` deleted, in the PyOpenGL change that adds the extra — never
   before the new package is installable from PyPI.

## What it settles

- **#164** — the core wheel carries nothing for a scanner to object to. The
  binaries are still ours to ship, to the users who ask for them.
- **#76 / #125 / #127** — either way the user is told what to do. Today they
  get `NullFunctionError` naming a function.
- The `py3-none-any` wheel becomes what it claims to be: pure Python.

None of those closes on the packaging alone. All of them close on the error
message, which is why it is step two rather than step five.

## Open

- **Does GLE go too?** Same argument, much smaller audience — `OpenGL.GLE`
  wraps one library and the tests for it skip wherever `libgle` is absent. One
  package for both, or two? One, unless somebody wants GLE without GLUT.
- **Release ordering.** The new package releases on its own cycle, but the
  first `PyOpenGL[glut]` release depends on it being on PyPI already. The
  release tool in this workspace releases in dependency order and needs to
  know about it.
- **Is a rebuild wanted eventually?** vc9 binaries load on current Windows,
  but nothing says how long that stays true. Not part of this change.
