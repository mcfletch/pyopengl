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

## Why

**They are somebody else's binaries, and we are redistributing them.**
freeglut is not ours and neither is GLE; both are vendored, both are from
compilers three generations old (vc9 is Visual Studio 2008), and neither has
been rebuilt in about a decade. Shipping a third party's compiled code inside
our wheel makes us responsible for it in ways nothing here can discharge: we
cannot patch it, we do not know what is in it, and we cannot say what it was
built against.

**A scanner has already objected.** #164 is ClamAV reporting
`gle32.vc14.dll` and `freeglut32.vc9.dll` as `PUA.Win.Packer.NspackDotnetNor-2`.
Almost certainly a false positive — the files have not changed in ten years —
but it is not answerable by us: we did not build them, so we cannot say what
the scanner is seeing. It will recur, and every recurrence costs a ticket. A
user whose corporate scanner quarantines a pip install has no way to proceed
and no way to understand why.

**Everyone pays for them and few use them.** They are in the pure-Python
`py3-none-any` wheel, so a Linux server rendering headlessly through EGL
downloads six freeglut builds it can never load. GLUT is a 1990s windowing
toolkit that a new program has no reason to choose over GLFW, pygame or Qt;
GLE is a tubing library that one module (`OpenGL.GLE`) wraps.

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

## Shape

**`PyOpenGL-glut-binaries`** — a new distribution, `win32`/`win_amd64` wheels
only, containing the DLLs and nothing else. Not pure-Python: the point of the
split is that a Linux user never downloads it, and only a platform-tagged
wheel achieves that.

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
   `PyOpenGL[glut]`. Red first; it is the whole compatibility story.
3. The new distribution, built from the files as they stand. No rebuild: a
   rebuild is a separate decision with its own risk, and doing both at once
   makes any regression unattributable.
4. The extra, the loader change, and the messages.
5. `OpenGL/DLLS/` deleted, in the same change that publishes the new package —
   never before it.

## What it settles

- **#164** — the scanner has nothing of ours to object to. Anyone who wants
  the binaries opts in, and can decline.
- **#76 / #125 / #127** — either way the user is told what to do. Today they
  get `NullFunctionError` naming a function.
- The `py3-none-any` wheel becomes what it claims to be: pure Python.

None of those closes on the packaging alone. All of them close on the error
message, which is why it is step two rather than step five.

## Open

- **Does GLE go too?** Same argument, much smaller audience — `OpenGL.GLE`
  wraps one library and the tests for it skip wherever `libgle` is absent. One
  package for both, or two? One, unless somebody wants GLE without GLUT.
- **Who builds the new package**, and does it get its own repository? The
  release tool in this workspace releases in dependency order and would need
  to know about it.
- **Is a rebuild wanted eventually?** vc9 binaries load on current Windows,
  but nothing says how long that stays true. Not part of this change.
