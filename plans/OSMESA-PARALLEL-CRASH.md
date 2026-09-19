# A worker crash on the OSMesa row: a framebuffer freed under Mesa

**Fixed.** `OpenGL.osmesa.offscreen.OffscreenContext` owned a Mesa context and
the array Mesa rasterises into, and had no finaliser. A program that dropped
one -- without calling :meth:`release` -- left Mesa holding a live context
whose framebuffer Python had already freed. The next ``OSMesaMakeCurrent`` on
that thread flushed the dropped context's front buffer through that pointer: a
512-byte ``memcpy`` into freed memory, corrupting whatever the allocator had
since put there. The process then fell over somewhere else entirely -- a
different case each run, in ``glClear``, ``glFinish``,
``OSMesaDestroyContext`` or a malloc inside an unrelated call.

The OSMesa CI row (`py312-num1-accel1-dispc`, `TEST_WINDOWING=osmesa`) is where
it showed, because that row is the only one whose framebuffer belongs to the
caller. Every other backend's default framebuffer belongs to the driver, so a
dropped context costs a leak rather than a write into freed memory.

## The fix

`OffscreenContext.__del__` releases. `release` is idempotent, so a caller who
released loses nothing by having one, and a caller who forgot gets the context
destroyed while the array is still alive.

Two further things were found on the way in and are fixed with it:

- **A context switch was never reported to the dispatch layer.**
  `OffscreenContext.make_current` now calls `OpenGL.dispatch.make_current`, as
  `OpenGL.WGL.offscreen` and `OpenGL.Tk.context` already did. The compiled
  layer keeps a table of resolved entry points per context and re-reads which
  is current only on the resolution slow path, so a second OSMesa context went
  on dispatching through the first one's table -- holding its slots, and its
  flags for which commands the context has.
- **`release` now retires that table**, and takes `forget=False` for the one
  caller that wants a context torn down with the layer never told, matching
  `OpenGL.WGL.offscreen`'s signature.

`tests/bindings/osmesa/test_osmesa_api.py` holds the finaliser and the
let-go-of-the-thread behaviour;
`tests/bindings/osmesa/test_osmesa_dispatch_notification.py` holds the
notification.

## Reproducing it, before the fix

Five test cases, under a second, aborting every time:

```bash
TEST_WINDOWING=osmesa PYOPENGL_DISPATCH=c MALLOC_CHECK_=3 \
  python -m pytest \
    tests/harness/test_shared_context_setup.py::TestTheDecoratorFinishesTheFrame::test_through_the_teardown_every_other_test_uses \
    tests/harness/test_shared_context_setup.py::TestAContextThatGoesIsForgotten::test_tearing_one_down_forgets_its_handle \
    tests/gles/test_es2_program.py::TestES2Program::test_lifecycle_and_introspection \
    tests/gles/test_es2_program.py::TestES2Program::test_shader_binary \
    tests/gl/test_ext_legacy_shaders.py::TestLegacyShaders::test_shader_objects
```

It began as `-n 4 --dist loadfile` over `tests/gl tests/gles tests/harness`,
which crashed six runs out of six; xdist mattered only because `--dist
loadfile` puts a particular set of files in one worker. Delta-debugging the
152 collected ids down to five is what turned it from a scheduling story into
a readable one.

## How it was found

`LD_PRELOAD` of a shim whose constructor installs `SIGSEGV`/`SIGABRT` handlers
calling `backtrace_symbols_fd` gets a native backtrace out of an xdist worker,
which gdb cannot easily wrap because execnet hands a worker its bootstrap over
stdin. That put every fault inside Mesa, reached through `ctypes`.

**AddressSanitizer as a preloaded runtime** -- `LD_PRELOAD` of `libasan.so.8`
with `detect_leaks=0`, no rebuild of anything -- is what named it. Its
allocator's redzones and quarantine turn a use-after-free into a report
instead of a fault, with the freeing and allocating stacks:

```
ERROR: AddressSanitizer: heap-use-after-free ... WRITE of size 512
    #0 memcpy
    #5 OSMesaMakeCurrent
freed by thread T0 here:
    #1 array_dealloc  (numpy)
previously allocated by thread T0 here:
    #1 default_calloc (numpy)
```

Note that ASan *hides* the crash while it reports it: with its allocator in
place the write lands in a redzone rather than on an unmapped page, so a run
under it comes out green. The report is in the log file, not the exit status.

Wrapping `OSMesaMakeCurrent`/`OSMesaDestroyContext`/`OffscreenContext.release`
to log each context with its buffer's data pointer then matched the freed
block to the context that was made current with it and never released.

## What it was not

Each was measured rather than assumed, and each is worth not re-testing:

- Not the entry-point routes in `SplitEntryPointPlatform`: it reproduced at
  `07c40bc8`, before that class existed, and removing the route left the rate
  unchanged.
- Not a context used after it was destroyed: every `OSMesaMakeCurrent` and
  `OSMesaDestroyContext` was audited against the live set, and nothing stale
  was ever passed. The *buffer* was the thing being used after free.
- Not two GL implementations in one process: the crashing worker had only
  `libOSMesa.so.8` mapped. Loading GLU does bring libglvnd's
  `libGLdispatch.so.0` in, but preloading it into a clean configuration
  changed nothing, and nor did loading GLU `RTLD_LOCAL`.
- Not llvmpipe's rasteriser threads (`LP_NUM_THREADS=1`: still crashed), the
  Mesa shader cache (`MESA_SHADER_CACHE_DISABLE`: still crashed), the
  `GL_KHR_debug` callback the layer arms (`PYOPENGL_ERROR_DEBUG_OUTPUT=0`:
  still crashed), or an abandoned `glBegin` block.
- Not context churn on its own: four concurrent processes making, drawing in
  and destroying 400 contexts each came through clean, because each released
  what it made.

`PYOPENGL_DISPATCH=c` crashed 6/6 against `ctypes` 1/6 interleaved, which
pointed at the compiled layer for a long time. It is a real asymmetry and not
the cause: the compiled layer resolves an entry point once per context and
caches it, so it makes the calls that flush the front buffer where the ctypes
path re-resolves and makes fewer of them.
