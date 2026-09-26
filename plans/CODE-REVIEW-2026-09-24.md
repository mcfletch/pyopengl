# Code review: `v4.0.0a6..HEAD`, 4.0.0a6 to `develop`

2026-09-24. Eight commits (`git log v4.0.0a6..HEAD`), two of them merges,
1,699 lines added and 139 removed outside the generated C. HEAD is `ea29cc30`.
The one uncommitted change in the tree, to `build-docs.py`, is reviewed
separately at the end.

| Commit | Subject |
|---|---|
| `de2f1be7` | RELEASE accelerate carries the version its PyOpenGL does |
| `7e4aaf99` | ACCELERATE The requirements files include each other one way only |
| `3d9e8715` | DISPATCH A function derived from a C entry point carries its own customisations |
| `dde8a06c` | BINDINGS glGetUniformIndices takes the names and answers the indices |
| `61f1b048` | ARRAYS An input array is measured against the count that says how long it is |
| `5c9723d8` | Merge branch 'pointer-lifetime' into develop |
| `868ec78c` | Merge branch 'uniform-indices' into develop |
| `ea29cc30` | TESTS The GLX cases skip where the named display does not answer |

Reviewed in `/workspaces/OpenGL-dev/.venv` with the C dispatch layer built,
against Mesa through GLFW on `DISPLAY=:3`. Reproductions were run as separate
processes from the scratchpad, and nothing in the tree was modified.

## Verdict

The window improves the codebase. Three of its fixes close real memory-safety
defects: a typed pointer setter handing the driver float64 memory labelled
`GL_FLOAT`, outputs sized by looking a *count* up in the glGet table (an abort
on radeonsi), and viewport-array inputs read past the end of the caller's
buffer. The dispatch fix is correct for the order in which the friendly modules
build their chains. The input-array mechanism is small, has one implementation
per path, is driven from the annotation table, and is tested on both paths
without a context.

One of the new APIs adds a crash. `glGetUniformIndices(program, 3)` segfaults
under both implementations (finding 1), and under the workspace rule on core
dumps it has to be fixed before 4.0.0a7. The rest of the findings are API
divergence, one global-state design that breaks when chains are built out of
order, fixes applied downstream of their causes, and test defects.

## Findings

### High

#### 1. `glGetUniformIndices(program, N)` dereferences a null `char **` and segfaults

Problem - The friendly form in `OpenGL/GL/VERSION/GL_3_1.py:37` is
`glGetUniformIndices(program, uniformCount, uniformNames=None, uniformIndices=None)`.
When `uniformCount` is an integer and `uniformNames` is left at its default,
the wrapper allocates `uniformCount` indices and passes `None` for the names.
Both paths turn that into a null `GLchar *const *`, and the driver reads
`uniformNames[0]` from address zero.

Evidence - Reproduced under both implementations with a GL 3.3 core context
(`scratchpad/ui.py`):

```text
$ python ui.py nonames            # glGetUniformIndices(prog, 3)
Fatal Python error: Segmentation fault
  File ".../OpenGL/GL/VERSION/GL_3_1.py", line 68 in glGetUniformIndices
exit 139
$ PYOPENGL_DISPATCH=ctypes python ui.py nonames
Fatal Python error: Segmentation fault      (same frame)
```

Before a6 the names argument was required, so reaching this took an explicit
`None`. The new default makes a two-argument call that reads as valid crash the
process. `61f1b048` introduces a rule for this class of input ("`None` is
refused unless the count asks for nothing"), but `uniformNames` is a
string-array input sized by `uniformCount` and the rule was not applied to it.

Fix - Remove the C ordering from the friendly form (finding 2), so the names are
required and a count is never taken from the caller. Separately, apply the
`61f1b048` rule to string arrays: have `PYGL_STRING_ARRAY` and
`StringArray.from_param` refuse `None` when the governing count is greater than
zero, keyed from the annotation table in the same way as `PYGL_ARRAY_IN_MIN`.
That also covers `glShaderSource`, `glTransformFeedbackVaryings` and the other
entry points of this kind reached through `OpenGL.raw`. Add a red case for
`glGetUniformIndices(program, 3)` and `(program, 3, None)` on both paths.

### Medium

#### 2. GL and GLES3 now offer two different friendly `glGetUniformIndices`

Problem - `dde8a06c` writes a second friendly implementation of this entry
point rather than sharing the one GLES3 already had. The two signatures and
the two string helpers differ:

| | GL (`GL_3_1.py:37`) | GLES3 (`GLES3_3_0.py:271`) |
|---|---|---|
| signature | `(program, uniformCount, uniformNames=None, uniformIndices=None)` | `(program, uniformNames, uniformIndices=None)` |
| names helper | `_string_array.as_bytes_list` | `_string_array` (count, array) |
| C ordering | accepted | not accepted |
| `uniformNames=` by keyword | `TypeError: missing ... 'uniformCount'` | works |

Evidence - The keyword failure is reproduced (`ui.py kw`). The release note says
"on desktop GL as it already did on GLES3", which tells users the two behave
the same.

The GL form overloads its second positional parameter: it is either a count or
the names, and when it is the names the third positional becomes the output
array. A parameter named `uniformCount` that accepts a list of names is hard
to read, it breaks keyword calls, and it is how finding 1 became reachable.

Fix - Give both APIs one implementation with the GLES3 signature,
`(program, uniformNames, uniformIndices=None)`, in a module both import (for
example next to `_string_array`). A caller who has built the pointer array
calls `OpenGL.raw.GL.VERSION.GL_3_1.glGetUniformIndices`, which is the purpose
of the raw modules. This removes the overloaded parameter, the positional
shuffle (`GL_3_1.py:61-66`) and finding 1's entry point.

#### 3. The type stub for `glGetUniformIndices` lost every type

Problem - `OpenGL/GL/__init__.pyi:8410` changed from

```python
def glGetUniformIndices(program: int, uniformCount: int, uniformNames: AnyArray, uniformIndices: UIntArray | None = None) -> UIntArrayResult:
```

to

```python
def glGetUniformIndices(program: Any, uniformCount: Any, uniformNames: Any = ..., uniformIndices: Any = ...) -> Any:
```

Evidence - The diff of `dde8a06c`. `src/cdispatch/emit_pyi.py:437` has a
fallback for `lazy`-wrapped functions that emits `Any` for every parameter and
the return. The friendly form is now a better API with worse types: mypy
accepts `glGetUniformIndices(p, 3)` (finding 1) and calls the result `Any`.

Fix - Once finding 2 settles the signature, emit
`def glGetUniformIndices(program: int, uniformNames: str | bytes | Sequence[str | bytes], uniformIndices: UIntArray | None = None) -> UIntArrayResult`.
The generator needs a source for this. Have `emit_pyi` read annotations from
the `lazy` function when it has them (and give this one annotations), or keep a
small hand-written overrides table beside the generator. Either is better than
a fallback that erases types without saying so.

#### 4. Per-chain customisation tracking depends on chains being built one at a time

Problem - `3d9e8715` keys `_open_chains` by entry point and infers where a
chain ends: a chain is open until the next `wrapper.wrapper(entry_point)` or
until it demotes (`OpenGL/_dispatch/support.py:367-440`). Under the C layer,
`wrapper.wrapper(proc)` returns the `GLProc` itself, so every chain on that
entry point is the same object and nothing identifies which chain a
customisation belongs to. If two chains on one entry point interleave, the
customisations of one are recorded against the other.

Evidence - `scratchpad/chain.py`, under the C layer:

```python
a = wrapper.wrapper(p)            # a is b is p
b = wrapper.wrapper(p)            # begins chain B; A is now closed
a = a.setPyConverter('pointer', C('A'))    # recorded into B
b = b.setPyConverter('pointer', C('B'))    # overwrites it
b = b.setCConverter(...).setPyConverter('size')   # demotes B, pops the chain
a = a.setCConverter(...).setPyConverter('size')   # demotes A with nothing to replay
```

```text
same object True
a pointer converter: None
b pointer converter: B
```

Chain A loses its converter with no error, and the result converts the array
with the default. That is the same class of defect `3d9e8715` fixed (the wrong
converter handed to the driver). No friendly module in the tree builds chains
this way, since `OpenGL.GL.pointers` finishes each one before starting the
next. Third-party code that builds its own derived functions from an entry
point is not bound by that order, and the ordering requirement is not written
down anywhere.

The two dicts are also mutated with no lock, while `FREE-THREADING.md` plans
for the C layer to declare free-threading support. Two modules importing on
two threads can interleave in the same way.

Fix - Carry the chain's state on the object the chain holds, so that the
object answers which chain a customisation belongs to. `GLProc_declarative`
and the swallowing setters can return a lightweight chain view: a small C type
holding a reference to the `GLProc` and its own swallowed tuple, whose
`__call__` forwards to the proc's vectorcall. Demotion replays the view's own
tuple, and `_open_chains` and `begin_chain` go away. The cost is that a chain
which never demotes ends at a view rather than at the `GLProc`. If identity
with the entry point matters to callers, which is worth checking, the cheaper
fallback is to document the invariant in `wrapper.wrapper`'s docstring and have
`record_custom` raise when a customisation arrives for a chain that has
already been closed by a later `begin_chain`.

#### 5. The version skew is caught by a test and left in place at its cause

Problem - a6 bumped `OpenGL/version.py` and not
`accelerate/OpenGL_accelerate/__init__.py`, because `tools/release.toml:40-43`
declares two distributions for pyopengl and one `version_file`, and
`release.py --bump` rewrites only that file. `de2f1be7` fixes the number and
adds `test_the_two_distributions_state_the_same_version`, which fails after the
next bump rather than preventing it. The next `release.py pyopengl --bump pre`
will produce the same skew and a red suite.

Evidence - `tools/release.toml:40-43` and `tools/release.py:609-633` (one
`version_file`, one `git add`). In the same file,
`accelerate/OpenGL_accelerate/__init__.py:15` keeps
`__version_tuple__ = (4, 0, 0)`. `OpenGL/acceleratesupport.py` compares it
with its floor, nothing keeps it in step with `__version__`, and neither the
new comment nor the new test mentions it. (Corrected; see Resolution.) The test's regex
(`test_dispatch_selection.py:354`) also duplicates the reader in
`accelerate/setup.py:35`, with a different anchor.

Fix - Accept a list for `version_file` in `release.toml` and rewrite every
entry, making it
`["OpenGL/version.py", "accelerate/OpenGL_accelerate/__init__.py"]`. Keep the
test as a backstop. Derive `__version_tuple__` from `__version__`. Have the test call the reader `setup.py` uses, moved into a
small importable helper, rather than a second regex.

#### 6. The documentation site no longer publishes unless someone runs the workflow

Problem - `de2f1be7` removes the `push: master` trigger from
`.github/workflows/documentation.yml` to avoid building while PyPI is
half-published. After the change nothing publishes the site. It moves only when
somebody remembers to run the workflow and tick `publish`, so the published
documentation will fall behind the released code.

Evidence - The diff of `documentation.yml`: `on:` is now `workflow_dispatch`
only, and `publish` defaults to `false`.

Fix - Keep publishing automatic and make it wait for PyPI. Trigger on
`workflow_run` of `accelerate-manylinux.yml` with `types: [completed]` on
`master`, gated on `conclusion == 'success'`, because that is the workflow that
uploads both distributions. Alternatively, keep the push trigger and add a
first step that retries `pip download --no-deps PyOpenGL==$V
PyOpenGL-accelerate==$V` until both resolve. Keep `workflow_dispatch` for
manual rebuilds.

#### 7. `test_something_listening_that_is_not_a_server_we_may_use` passes for the wrong reason

Problem - The case binds a listening socket at `tmp_path/X79` and asserts that
`xdisplay.answers(':79', directory=tmp_path)` is false. `directory` reaches only
`listens()`. The Tk probe in `answers()` runs with `DISPLAY=:79` and looks for
the socket where every X client does, `/tmp/.X11-unix/X79`, where nothing
exists. The probe never touches the listener, so the case would pass the same
way if `answers()` did not open a client at all.

Evidence - `tests/xdisplay.py:48-51`: the subprocess environment sets only
`DISPLAY`. `tests/bindings/glx/test_xdisplay.py:47-57`.

Fix - Use TCP, where the listener and the client meet at the same address.
Bind `127.0.0.1:6000+N`, listen without answering, and assert that
`answers('127.0.0.1:%d' % N)` is false. Give the probe a short timeout for this
case, since a listener that never answers leaves the client waiting until the
timeout.

### Low

#### 8. `xdisplay.answers()` probes the wrong thing, at collection time, and misses abstract sockets

Problem - There are three issues. (a) The probe is a Tk window. The GLX cases
need libX11 to open the display, and Tk adds a tkinter dependency. When
tkinter is absent, `answers()` returns true for anything that accepts a
connection (`xdisplay.py:43-46`), which is the "something else listening" case
the commit set out to handle. (b) `answers()` runs in a `skipif` at import, so
every collection of `tests/bindings/glx/` starts a subprocess with a 30 s
timeout, including runs that deselect those cases. (c) On Linux, libxcb tries
the abstract socket `@/tmp/.X11-unix/X<n>` before the filesystem path.
`listens()` checks only the path, so a container that shares the host's
network namespace but not `/tmp/.X11-unix` can reach a server while `listens()`
reports none, and the GLX cases skip where they could run. (c) is from libxcb's
connection order and was not reproduced here, because this machine has the
directory.

Fix - In the subprocess, probe with
`ctypes.CDLL(ctypes.util.find_library('X11')).XOpenDisplay(None)` and exit
non-zero on NULL. That tests what GLX needs and drops tkinter. Cache the answer
with `functools.cache` and evaluate it from a session-scoped fixture or
`pytest_collection_modifyitems` instead of at import. On Linux, try
`'\0/tmp/.X11-unix/X%d'` before the path.

`test_it_says_what_a_client_finds` (`test_xdisplay.py:60-66`) runs the same
`CLIENT` string `answers()` runs and compares the two results, which tests
`answers()` against itself and starts up to six subprocesses. Delete it.

#### 9. The new viewport-array class took two `TestGL41` methods with it

Problem - `TestViewportArraysAreMeasuredAgainstTheCount` was inserted in the
middle of `TestGL41` in `tests/gl/test_gl41.py`. The methods after it,
`test_double_attribs_and_es_compat` (line 189) and `test_program_binary` (line
224), now belong to the viewport-array class, whose docstring says it is about
viewport arrays.

Evidence - `grep -n "^class \|def test_" tests/gl/test_gl41.py`. The tests
still run, because both classes ask for the same profile and version, but
`-k TestGL41` no longer selects them and a reader will not find them where
they belong.

Fix - Move the new class to the end of the file.

#### 10. `glVertexPointerb` widens to `GL_INT` and the other `b` setters to `GL_SHORT`

Problem - `3d9e8715` fixes `glIndexPointerb` and `glTexCoordPointerb`
(`GL_BYTE` is not accepted there) by widening to `GL_SHORT`.
`glVertexPointerb` widens the same signed bytes to `GL_INT`. The release note
points out the difference without giving a reason for it.

Evidence - `OpenGL/GL/pointers.py:83,94,100`. `glVertexPointer` accepts
`GL_SHORT`, and `GL_SHORT` holds every signed byte at half the copy.

Fix - Pick one widening for all three `b` setters and record the reason next
to the table. If `glVertexPointerb` changes, that is a visible change (the
returned array's dtype) and needs its own release-note line. Otherwise add a
comment explaining why vertices differ.

#### 11. The two paths refuse `None` with different messages and exception shapes

Problem - For a null array with a positive count, the C path raises
`ValueError("Expected at least 16 byte array, got None")`
(`pygl_runtime.c:356-360`), and the ctypes path raises
`ValueError("Expected at least 16 byte array, got 0 byte array", incoming)`
(`arrayhelpers.py:220-225`), with two arguments. `c-dispatch.rst` says the two
implementations differ only in which exception carries a refusal.

Evidence - The two sources. `test_none_is_a_null_pointer_the_driver_would_read`
checks only the exception type.

Fix - Have `AsArrayTypedCountChecked` say `got None` when `result is None`, and
add a `match=` to the `None` case so it holds on both paths.

#### 12. `from-argument` records `divisor` always and `multiplier` only when it is not 1

Problem - `src/cdispatch/annotations.py:46-50` writes `divisor: 1` explicitly
and omits `multiplier: 1`. The same data then has two spellings, and the tests
encode both (`test_annotations.py:56` and `:61-66`).

Fix - Omit both at their defaults, or write both always. Omitting both shrinks
`annotations.json`. Writing both makes every size self-describing. Either
choice needs a regeneration and nothing else.

#### 13. An output with a multiplier is cast twice

Problem - `_size_expression` (`emit_c.py:94`) now casts the argument, and the
output emitter casts the whole expression again. The generated C reads
`(Py_ssize_t)((Py_ssize_t)n * 2)`, and `test_emit_c.py:246` locks that in.

Fix - Leave the widening to `_size_expression` and drop the outer cast when the
expression already carries it. Alternatively, have `_size_expression` return
an uncast expression and let each caller cast once.

#### 14. Two new test docstrings narrate history

Problem - `tests/gl/test_ext_dsa.py` (`test_named_buffer_sub_data_allocates_the_bytes_asked_for`:
"``data`` used to be sized by…") and `tests/gl/test_uniform_indices.py`
(`test_a_count_the_glget_table_does_not_hold`: "The output used to be sized
by…") describe the defect that was fixed rather than what is checked. The
workspace rule says docstrings describe what is.

Fix - Say what is checked: "The answer holds `size` bytes: a byte count is not
a glGet enum, and three is one the table does not hold." Keep the history in
the commit message, where it already is.

#### 15. Tests decode private declaration formats themselves

Problem - `TestWhatIsSizedFromTheGLGetTable.annotations_and_declarations`
(`test_glget_consistency.py:215-231`) calls `_declarations._data_source` and
unpacks each `marshal` blob into a four-tuple itself.
`test_input_array_counts.ctypes_wrapper` calls `_declarations._array_parameters`.
Both copy `_declarations`' own decoding, so a change to the blob layout breaks
them with an unpacking error rather than a message about sizes.

Fix - Add a public iterator to `_declarations`, for example
`declared_commands(api) -> Iterator[(name, argument_names, types)]`, and a
public way to build one customised entry point. Use them in both tests.

#### 16. The requirements gate walks the whole checkout to find three files

Problem - `tests/gates/test_requirements_files_resolve.py` walks roughly
30,000 files at import to find the three `*requirements*.txt` files. It
descends into `.mypy_cache`, `.ruff_cache`, `PyOpenGL.egg-info` and
`documentation/`, which `SKIP` leaves out, and it picks up untracked files. The
walk takes 0.02 s here, so this is tidiness rather than cost. The `INCLUDE`
pattern also misses `-c`/`--constraint`, which pip follows the same way, and
the no-space spelling `-rfile`.

Fix - Use `git ls-files '*requirements*.txt'`, falling back to the walk when
there is no `.git`. Extend `INCLUDE` to `(?:--requirement|--constraint|-r|-c)[ \t=]*`.

## Uncommitted: `build-docs.py`

#### 17. Sphinx's locale is overridden unconditionally

Problem - The working-tree change sets `LC_ALL=C.UTF-8` for every Sphinx run.
That replaces a working locale the builder already had, and `C.UTF-8` is not
installed on every platform, so on a machine without it the override causes
the `locale.Error` it was added to avoid. The comment next to it also uses two
sentences where one would do.

Evidence - `git diff HEAD -- build-docs.py`. `locale -a` here lists `C.utf8`
because glibc ships it.

Fix - Probe first and override only on failure:
`try: locale.setlocale(locale.LC_ALL, '') except locale.Error: env['LC_ALL'] = 'C.UTF-8'`.
Leave the environment untouched otherwise. The mode change to 755 is correct,
since the file has a shebang.

## Checked and cleared

- Per-chain replay against ctypes semantics. Under ctypes,
  `wrapper.wrapper(raw)` builds a new `Wrapper` for each call, so each derived
  setter carries only its own chain. The per-chain replay in `3d9e8715` matches
  that, and the earlier first-chain-wins record did not.
- Whether `61f1b048` switched on checking beyond its family. It did not. The 14
  input `from-argument` annotations in `annotations.json` are exactly the
  entry points listed in `plans/INPUT-ARRAY-SIZES.md`, so no other input moved
  from unchecked to checked without being named.
- `PYGL_ARRAY_IN_MIN` overflow. The count is widened to `Py_ssize_t` before the
  multiply, and a negative count gives a negative minimum that every array
  meets. The driver then raises `GL_INVALID_VALUE`, which is the right owner
  for that error.
- The two merge resolutions. The conflicts were add/add in generated modules,
  and each resolution is the union of both sides (`git show --remerge-diff`).
- The `test`/`dev` requirements direction. `_build-manylinux.sh` installs
  `dev-requirements.txt` into the wheel-build interpreters, so `test` including
  `dev` is the right direction.
- The glGet-table gate (`test_every_one_names_an_enum`). It keys on the declared
  `GLenum` type and lists its exceptions, with a second case that keeps the
  exception list from going stale.

## Test evidence

```text
pytest tests/bindings/dispatch tests/bindings/arrays/test_input_array_counts.py \
  tests/bindings/generated tests/cdispatch \
  tests/gates/test_requirements_files_resolve.py tests/bindings/glx \
  tests/gl/test_uniform_indices.py tests/gl/test_client_array_pointers.py \
  tests/gl/test_gl41.py tests/gl/test_ext_dsa.py
4065 passed, 8 skipped, 42 subtests passed in 51.51s
```

The suite is green, and findings 1 and 4 are outside it: neither case is
tested.

## Suggested order

1. Finding 1 with finding 2: one signature, names required, and `None` refused
   for string arrays with a positive count, with red cases on both paths.
2. Finding 3, once the signature is settled.
3. Findings 5 and 6, before the a7 release runs.
4. Finding 4. Decide whether the entry point's identity must survive a chain,
   then carry chain state on the chain.
5. Findings 7 to 16 as one tidying pass.

## Resolution

2026-09-24, same day. Every finding except 6 is fixed in the working tree,
each with a test that failed first. Finding 6 is by design: the site is
published by hand because running the sample build on CI costs more than the
automation saves.

| Finding | Outcome |
|---|---|
| 1 | Fixed. The friendly form requires the names. Separately, ten string-array parameters carry a `from-argument` count in the table; the C emits `PYGL_STRING_ARRAY_MIN` and the ctypes path applies `arrayhelpers.StringArrayCountChecked`, so fewer strings than the count, or `None` for a positive count, raises `ValueError`. `glGetUniformIndices(program, 3)` raises `TypeError` on both paths where it dumped core. |
| 2 | Fixed differently from the review. `OpenGL._uniform_indices` is the one implementation `OpenGL.GL`, the ARB module and `OpenGL.GLES3` share. It keeps the C ordering, told apart by the second argument being a count, because that ordering is the 3.x API (`tests/gl/test_gl31.py` and `tests/gl/test_string_arrays.py` call it), and removing it would break existing callers. `uniformNames=` works by keyword. |
| 3 | Fixed. `cdispatch/exceptional.py` has a typed row for `glGetUniformIndices` on GL and GLES3, and rows can name a wrapper defined outside `OpenGL/GL/exceptional.py`. |
| 4 | Fixed with per-chain objects. The first swallowed call answers a `GLProc` of the chain's own (`GLProc._chained()`), sharing the command, stub and slot and holding the record in `_swallowed`. `_open_chains`, `begin_chain` and the module-level `_swallowed` dict are gone. The binding a friendly module exports is therefore a separate object from the entry point `OpenGL.raw` exports; demoting the raw one gives the bare binding. |
| 5 | Fixed. `tools/release.py` takes `version_files`, refuses to release while they disagree, and writes and stages them all; pyopengl lists both. `__version_tuple__` is derived from `__version__`. The review's first draft said nothing reads `__version_tuple__`; `OpenGL/acceleratesupport.py` does, so it stays. The pairing test reuses `setup.py`'s reader. |
| 6 | By design, not changed. |
| 7, 8 | Fixed. `tests/xdisplay.py` probes with libX11's `XOpenDisplay`, caches the answer, is asked from a fixture, and tries the Linux abstract socket first. The listening-but-not-a-server case runs over TCP. The self-comparing test is gone. |
| 9 | Fixed. |
| 10 | Fixed differently from the review: `glIndexPointerb` and `glTexCoordPointerb` widen to `GL_INT`, as `glVertexPointerb` has since 3.x, so no working call changes its result type. |
| 11-16 | Fixed. 12 writes both scales, and the ctypes path now sizes an output by the multiplier as well. 15 adds `_declarations.declared_commands()` and `_declarations.ctypes_entry_point()`. 16 lists the files `git ls-files` tracks and reads `-c` and `-rfile`. |
| 17 | Fixed. `build-docs.py` sets `LC_ALL` only where `setlocale(LC_ALL, '')` fails. |

### Found while fixing

18. `tests/bindings/arrays/test_input_array_counts.py` skipped every C case
    when run on its own, because nothing had installed the dispatch layer;
    `c_entry_point` now settles it. Fixed.
19. `src/cdispatch/extract.py` defined `_literal` twice. The second (returning
    `None`) replaced the first (returning `_UNKNOWN`), so every `is _UNKNOWN`
    test in the chain reader was dead, and a chain computing an input size
    (`setInputArraySize('v', len(x))`) read as one stating no size. Fixed: the
    second is `_literal_or_none`, used where the listing of a chain's calls
    wants `None`, and such a chain marks its command a hand-written
    `converter`. Ruff's F811, which reports a definition hiding another, was
    ignored for the whole project because the friendly modules rebind
    generated names; it is now ignored under `OpenGL/` alone, and the
    redefinitions it then found in `tests/` and `accelerate/setup.py` are
    gone.
20. The per-module stubs (`OpenGL/GL/VERSION/GL_1_5.pyi` and the rest) carried
    only the C form of every wrapped entry point. Fixed: a module's stub
    describes the `lazy` wrappers that module defines and the rows of
    `cdispatch/exceptional.py` whose wrapper it binds, through the same
    `emit_pyi._wrapped_lines` the namespace stubs use.
21. `tests/bindings/test_what_the_wheel_ships.py` built its wheel in the
    checkout, so its own `build/lib` went stale on the next source change and
    the case failed until someone removed it -- which it asked for, and which
    held the preflight gate red twice in this work. Fixed: the wheel is built
    from a copy of the files git tracks or would add, so no earlier build
    reaches it and the case writes nothing into the checkout.
