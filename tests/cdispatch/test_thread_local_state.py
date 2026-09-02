"""Error checking is suspended per thread, not per process.

``glBegin``/``glEnd`` brackets a region in which most queries are illegal, so
the layer stops checking for errors inside one.  Which thread is inside a
``glBegin`` block is a property of that thread: another thread drawing to
another context at the same time is still entitled to have its errors raised.

The ctypes implementation keeps the flag on the shared ``_ErrorChecker``
(``OpenGL/error.py``), so there one thread's ``glBegin`` silences another's
checking.  The C implementation keeps it in thread-local storage instead.  This
is a deliberate divergence rather than an oversight, which is why it has a test
naming it.
"""

import threading

import pytest

import OpenGL._dispatch as dispatch
from OpenGL import _configflags

pytestmark = pytest.mark.skipif(
    not dispatch.AVAILABLE or _configflags.DISPATCH != 'c',
    reason='thread-local suspension is the C implementation',
)


@pytest.fixture
def restore_suspension():
    """Leave the calling thread's flag as it was, whatever the test did."""
    from OpenGL._dispatch import _c

    yield _c
    _c.suspend_error_checking(False)


def test_suspending_in_one_thread_leaves_another_checking(restore_suspension):
    checker = restore_suspension
    checker.suspend_error_checking(True)

    seen = []

    def other():
        seen.append(checker.error_checking_suspended())

    worker = threading.Thread(target=other)
    worker.start()
    worker.join()

    assert seen == [False], (
        'the other thread inherited this one\'s glBegin block: %r' % (seen,)
    )
    assert checker.error_checking_suspended() is True


def test_a_thread_starts_out_checking(restore_suspension):
    """A fresh thread's flag is zero rather than whatever was last set."""
    checker = restore_suspension
    checker.suspend_error_checking(True)

    results = []

    def other():
        results.append(checker.error_checking_suspended())
        checker.suspend_error_checking(True)
        results.append(checker.error_checking_suspended())

    for _ in range(3):
        worker = threading.Thread(target=other)
        worker.start()
        worker.join()

    assert results == [False, True] * 3, results
