# The accelerators on a free-threaded interpreter

**Status:** Proposed. Nothing has landed, and nothing here has been measured on
a free-threaded build.

**Scope:** the nine Cython modules in `accelerate/src/*.pyx` and the C dispatch
layer in `accelerate/src/c/`. The pure-Python package works on a free-threaded
interpreter already, in the sense that it imports and runs; what it does *not*
do is let one stay free-threaded, which is the whole of the problem below.

## Why

PEP 703's free-threaded build was experimental in CPython 3.13 and is an
officially supported configuration from 3.14 — which `tox.ini` already runs a
`py314` cell against. A GL binding is a place threads are wanted: a loader
decoding images or building vertex arrays on worker threads, while the render
thread draws, is the shape every application in this workspace already has.

**An extension that says nothing re-enables the GIL for the whole process.** A
free-threaded interpreter importing a module built without
`Py_mod_gil = Py_MOD_GIL_NOT_USED` turns the GIL back on at run time, warns, and
carries on. So `import OpenGL` on such a build silently takes the interpreter
back to where it started, and every other extension the application loaded pays
for it. That makes this a question about whether a *user's* program can be
free-threaded, not about whether PyOpenGL is faster.

The warning names the module responsible, but only to whoever is reading
warnings. What settles it instead is a test that asserts the interpreter is
still free-threaded after the import.

## What has to be true

Declaring `Py_mod_gil = Py_MOD_GIL_NOT_USED` is one line per module and is the
*last* step, not the first: it is a promise that the module's own state is safe
without the GIL. Four kinds of state have to be looked at before it can be made.

### 1. `pygl_current` and the dispatch tables

`accelerate/src/c/pygl.h:253` declares `PYGL_THREAD_LOCAL __thread` and
`pygl_current` is per thread, which is right — a GL context is current on one
thread at a time, and the table it dispatches through follows it.

The hazard is the lifetime of the *table*, not the pointer, and it has already
bitten once: [C-DISPATCH.md](C-DISPATCH.md) records `forget_context()` freeing a
table other threads were still dispatching through, found with a proof of
concept that faulted 7 runs in 10. The fix there was to empty and retire a
forgotten table rather than free it. That reasoning was done under the GIL and
has to be redone without it: retiring is a write other threads read, and what
orders the two is the GIL today.

**What to establish:** whether a retired table can be read after the retiring
thread has moved on, and what makes the store visible — an atomic, a lock, or
the free-threaded build's own guarantees about `__thread` and object lifetime.

### 2. The late-bound call cache

`LateBind.getFinalCall` and `LateBind.__call__` (`latebind.pyx`) both read
`_finalCall`, and where it is empty call `finalise()` and store the result.
Two threads reaching an unbound entry point together each call `finalise()` and
each store; under the GIL the store is atomic and the loser's result is
discarded.

**What to establish:** that `finalise()` is idempotent for every subclass — a
second resolution of the same entry point must be equal and cost nothing — and
that the store cannot tear. Cython 3.1+ handles the reference counting of a
`cdef object` attribute on a free-threaded build; what it does not do is make
read-check-write one step, so the question is whether losing the race is
harmless rather than whether the race exists.

### 3. The runtime's module-level statics

`pygl_runtime.c` holds `pygl_support`, `pygl_array_types` and
`pygl_ctypes_argument_error` as file statics, filled during initialisation and
read on every call thereafter. `pygl_debug_pending` is `PYGL_THREAD_LOCAL`
already (`pygl_runtime.c:56`), so the audit flag is per thread and is not one of
these.

**What to establish:** that every one of the three is genuinely
write-once-before-use, and that nothing rebinds one from a later call — a
lazily-filled `pygl_array_types` would be the same race as the late bind, on
state shared by every thread rather than by one entry point.

### 4. Array type registration

A client registering a new array element type writes a registry every thread
reads. That path is documented as a supported extension point, so it is not
enough for it to be safe when nobody uses it.

**What to establish:** whether registration is confined to import time by
contract. If it is, say so and check it; if it is not, it needs a lock, and the
lock belongs on the write rather than on the read path that every call takes.

## How it would be done

1. **A build to test against.** `uv python install 3.14t` gives a free-threaded
   interpreter — the `t` suffix is the whole difference, and 3.14 is where the
   configuration is supported rather than experimental.
   `sysconfig.get_config_var('Py_GIL_DISABLED')` is how a test asks which build
   it is on. The accelerator has C extensions, so this is a real compile rather
   than a wheel download.
2. **The gate first, red.** A test that imports `OpenGL`, then asserts
   `sys._is_gil_enabled()` is still false. It fails on a free-threaded build
   today, which is the point: it states the goal before anything implements it.
3. **Work through the four sections above**, each with its own cases. The
   dispatch-table lifetime (§1) is the one with a known failure mode and a
   known reproduction shape, so it goes first.
4. **`freethreading_compatible = True`** in the `compiler_directives` beside
   `language_level` in `accelerate/setup.py:230`. Cython emits the `Py_mod_gil`
   slot from it, and the directive is present in the Cython the tree builds with
   (3.3.0). The C dispatch module already uses multi-phase initialisation —
   `pygl_module_slots` with `Py_mod_exec` at `pygl_runtime.c:2946` — so its half
   is one more entry in that array rather than a restructuring. This is the line
   that makes the promise, and it goes in last.
5. **A tox axis and a CI cell**, as `dispc`/`dispctypes` already are. A promise
   nothing runs is one that stops being true — the same argument
   `tools/preflight.toml` makes for a declared gate.

## What this does not claim

**No speed-up is promised.** Free threading removes a constraint on *callers*;
it does not make a GL call faster, and a free-threaded interpreter is slower
single-threaded than the default one. The benefit is that an application may
put its loading, decoding and simulation on threads without the binding forcing
them back into one — and measuring that benefit against the single-threaded
cost is the application's decision, not this binding's.

**A free-threaded interpreter does not make GL thread-safe.** A context is
current on one thread at a time and that does not change. What changes is that
the *other* threads are no longer blocked while one of them draws.

**The pure-Python path is a separate question.** It is the fallback when the
accelerator is absent, and it has its own shared state — the context data
dictionaries, the format-handler registry. Whether it is safe without the GIL
is worth its own pass; nothing here covers it.

## Open questions

- Does `numpy` on a free-threaded build carry the same promise? The
  `numpy_formathandler` module calls into it on the array path, and a
  dependency that re-enables the GIL makes ours moot.
- Is `glfw`'s ctypes binding — and ctypes generally — free-threading clean? The
  suite reaches its contexts through it.
- Is the 3.13t build worth a `tox` cell before any of this lands, simply to
  record what breaks?
