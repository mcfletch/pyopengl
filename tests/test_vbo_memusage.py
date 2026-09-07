import testdecorator
import os, sys, platform

# We have to import at least *one* VBO implementation...
from OpenGL import GL, arrays
from OpenGL.arrays import vbo
from OpenGL.arrays.arraydatatype import ArrayDatatype

try:
    import psutil
except ImportError:
    psutil = None
try:
    unicode
except NameError:
    unicode = str
    long = int
import pytest
import gc

try:
    import numpy as np
except ImportError:
    np = None


def get_current_memory():
    return psutil.Process(os.getpid()).memory_info().rss


@pytest.mark.resources
@pytest.mark.skipif(not psutil, reason="No psutil available")
@pytest.mark.skipif(not np, reason="No Numpy available")
@testdecorator.gltest
def test_sf_2980896():
    """Test SF#2980896 report of memory leak on VBO transfer.

    The original leak re-transferred (and lost) the whole data buffer on every
    VBO bind, so a regression grows the resident set on *every* iteration.  We
    detect that sustained, per-iteration growth rather than comparing each
    iteration to a single baseline: RSS only moves in page/arena-sized chunks, so
    one-time allocations -- a GL-driver buffer pool, a malloc arena, a lazily
    imported module elsewhere in the suite -- produce a single multi-KB/MB step
    that a tight byte threshold misreports as a leak (the old version failed in
    full-suite runs for exactly this reason).
    """
    data = arrays.GLfloatArray.zeros((1000,))
    try:
        chunk = ArrayDatatype.arrayByteCount(data)  # bytes transferred per bind
    except Exception:
        chunk = len(data) * 4
    # PyPy reaches steady state later (the JIT compiles this loop over the first
    # several iterations) and its incremental GC releases arenas lazily, so its
    # resident set steps up more often without any leak.  Give it a longer warm-up
    # and a looser step tolerance; a real leak still grows on (nearly) all 25
    # iterations, far above either tolerance.
    is_pypy = platform.python_implementation() == 'PyPy'
    warmup, iterations = (10, 30) if is_pypy else (5, 25)
    leak_step_tolerance = 8 if is_pypy else 3
    samples = []
    for i in range(iterations):
        new_vbo = vbo.VBO(data)
        with new_vbo:
            # data is transferred to the VBO
            assert new_vbo is not None, new_vbo
        new_vbo.delete()
        del new_vbo
        gc.collect()
        GL.glFinish()
        samples.append(get_current_memory())
    # ignore warm-up iterations (library/driver pools allocate early), then count
    # how many steady-state iterations grew by at least one transfer's worth.
    tail = samples[warmup:]
    leak_steps = sum(1 for a, b in zip(tail, tail[1:]) if b - a >= chunk)
    # a real leak grows on (nearly) every iteration; tolerate a few one-time jumps.
    assert leak_steps <= leak_step_tolerance, (
        "VBO transfer appears to leak: %d of %d post-warm-up iterations grew by "
        ">=%d bytes\nRSS samples: %s" % (leak_steps, len(tail) - 1, chunk, samples)
    )
    sys.stdout.write('OK\n')
    sys.stdout.flush()
