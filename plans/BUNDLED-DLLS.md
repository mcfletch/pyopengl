# The bundled Windows DLLs become an optional package

**Status:** Landed in both repositories, unreleased. `OpenGL/DLLS` is gone and
`PyOpenGL[glut]` is what replaces it. What is left is not code: the new
project needs a GitHub repository and a first PyPI release, and **PyOpenGL
must not be released before that happens** — the extra would resolve to
nothing and the error would name a command that does not work.

What is done:

- **`pyopengl-glut-binaries/`** is a project in this workspace, carrying the
  eighteen files, its own `pyproject.toml`, suite, CI and release workflow.
  Its wheels come out `py3-none-win32` and `py3-none-win_amd64`, so a Linux or
  macOS install never downloads them, and every Python 3 is served by one wheel
  rather than one per interpreter release.
- **`ctypesloader.DLL_DIRECTORY`** is the new package where it is installed and
  `OpenGL/DLLS` where it is not. Confirmed on Windows both ways: with the
  package on the path `OpenGL.GLUT` and `OpenGL.GLE` load out of it, and
  without it they load out of `OpenGL/DLLS` as before.
- It is registered with `verify-everything.py`, `tools/preflight.toml` and
  `tools/release.toml` — the last as `publish = false`, since there is nothing
  to push to yet.
- **`OpenGL/DLLS/` is deleted**, with the `MANIFEST.in` line that shipped it.
  `tests/bindings/test_what_the_wheel_ships.py` is inverted: it asserts the
  wheel carries no `.dll` at all, that the checkout tracks none, and that the
  `glut` extra is declared — because nothing else would announce their return.
- **`PyOpenGL[glut]`** is declared, Windows-only, so the same command is
  harmless in a cross-platform install script.
- **The errors name it.** `LIBRARY_SOURCES` for GLUT and GLE say
  `pip install PyOpenGL[glut]` instead of pointing at a directory that no
  longer exists, and the GLE entry says that one download carries both.
- **Freezing follows the split.** The PyInstaller hook collected from
  `DLL_DIRECTORY` already, but wrote to a hardcoded `OpenGL/DLLS` — which
  would have produced applications carrying the libraries and unable to find
  them. `ctypesloader._bundled_dll_destination()` derives the bundle path from
  the same lookup, and the hook adds `pyopengl_glut_binaries` to
  `hiddenimports` so the loader's import of it succeeds inside the bundle.
- **The build recipes moved with the binaries.** `downloadglut.py`,
  `buildgledll.py` and `gle32.zip` are in the new project's `tools/`, with a
  README saying what each is and why neither script runs on a current machine.

Every step of *Doing it* below is done but the third. What is left is the
repository and the first PyPI release — no code, and the ordering constraint
above.

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

There is no extension module to make the wheel impure, so its `setup.py`
answers `has_ext_modules` yes and overrides `get_tag` to `py3-none-<platform>`
— a platform tag, but no interpreter or ABI, since a DLL reached through
ctypes is tied to neither. `--plat-name` then chooses the platform, which is
how one Linux runner builds both Windows wheels: nothing is compiled, so the
tag is the only thing the machine would have decided. The release workflow
asserts both filenames and refuses an `any` wheel, because an `any` wheel is
silently the state this change exists to leave.

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

Originally this listed two red-first cases before the packaging. Each asserted
the state *after* the deletion, so neither could land before it without
carrying a known failure. They were written red at the point the deletion was
made instead, which is step 4 below.

Everything but step 3 is done. Step 3 is the release, and it is a hard gate on
releasing PyOpenGL, not merely the next task.

1. ~~The new project~~ — **done as a directory in this workspace.**
   `pyopengl-glut-binaries/`, built from the files as they stand. No rebuild: a
   rebuild is a separate decision with its own risk, and doing both at once
   makes any regression unattributable.
2. ~~The loader change~~ — **done.** `ctypesloader.DLL_DIRECTORY` is the new
   package where it is installed and `OpenGL/DLLS` where it is not, held by
   `TestWhereTheBundledLibrariesAre` in
   `tests/bindings/platform/test_library_loading.py`. Nothing changes for a
   user who does not have the package, which is every user today.
3. **Its repository and its first release to PyPI** — the only step left. A
   GitHub project under the same umbrella, added here as a submodule like the
   others, and released by the workflow it already carries.
   `tools/release.toml` holds it at `publish = false` until then. Two of its
   three actions are outward-facing: creating the repository, and configuring
   trusted publishing on PyPI, which claims the distribution name for good.
   Check the name is free before relying on it.
4. ~~The extra, the messages, and the deletion~~ — **done, in one change.**
   The extra is declared Windows-only; `LIBRARY_SOURCES` for GLUT and GLE name
   it; `OpenGL/DLLS` and its `MANIFEST.in` line are gone; the wheel cases are
   inverted; the PyInstaller hook writes to the directory the loader will
   compute rather than to a hardcoded one.

**Until step 3 lands, PyOpenGL is unreleasable.** A `pip install
PyOpenGL[glut]` would resolve to nothing, and every Windows GLUT user would
get an error naming a command that does not work — which is worse than the
`NullFunctionError` this set out to replace. `tools/release.toml` records the
ordering; nothing enforces it automatically.

## What it settles

- **#164** — the core wheel carries nothing for a scanner to object to. The
  binaries are still ours to ship, to the users who ask for them.
- **#76 / #125 / #127** — either way the user is told what to do. Today they
  get `NullFunctionError` naming a function.
- The `py3-none-any` wheel becomes what it claims to be: pure Python.

None of those closes on the packaging alone. All of them close on the error
message, which is why it landed with the deletion rather than after it.

## Why not download them instead

Asked, and answered no. The appeal is obvious: ship no binaries anywhere and
fetch the official builds when a user needs them. It has no clean form.

**A wheel has no install hook.** pip unpacks a wheel; it does not execute one.
So a fetch can only happen in a source build, at runtime, or in a command the
user runs. Publishing an sdist and no wheel is the first, and it breaks
`pip install --require-hashes`, offline and mirrored indexes, `pip download`
for air-gapped transfer, and distribution packaging, which forbids network
access during a build. Fetching from inside `glutInit` is the second, and is
silent network access from a graphics call. The third — `pyopengl-fetch-glut`,
the way a browser automation library installs its browsers — is honest and
does work, but it adds a step to every install, Dockerfile and CI job, and it
fails behind the proxies that a corporate user has.

**"Official" is one person's website.** freeglut upstream publishes source.
The Windows MSVC binaries everyone uses, ours included, are Martin Payne's
builds — `freeglut_README.txt` says "freeglut 3.0.0-1.mp for MSVC". An
install-time dependency on a personal site means a beginner's install breaks
the day it moves.

**`PyOpenGL[glut]` already is download-on-install**, through pip, which brings
hashes, mirroring, offline support and reproducibility with it. A bespoke
fetcher is that mechanism rebuilt worse.

What does survive the question is fetching at *release* time: the release
workflow could download the official archive, check a pinned SHA-256, and
build the wheel from that, so the network dependency sits in CI where a failure
is loud. That is the rebuild question below rather than this one, and it is
deliberately not being done at the same time as the split.

## Open

- **Does GLE go too?** Decided: one package for both. `OpenGL.GLE` wraps one
  library with a much smaller audience than GLUT's, and nobody has asked for
  GLE without GLUT, so a second distribution would be release machinery for
  nothing. `PyOpenGL[glut]` brings both.
- **Should the two Windows wheels differ?** They are identical but for the
  tag: both carry all eighteen files, so a 64-bit user downloads six 32-bit
  builds they cannot load. Splitting by word size halves the download and is a
  change to make on its own, where a regression in it is attributable.
- **Release ordering.** The new package releases on its own cycle, but the
  first `PyOpenGL[glut]` release depends on it being on PyPI already. The
  release tool in this workspace releases in dependency order and needs to
  know about it.
- **Is a rebuild wanted eventually?** vc9 binaries load on current Windows,
  but nothing says how long that stays true. Not part of this change.
