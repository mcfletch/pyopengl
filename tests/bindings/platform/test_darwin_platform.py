"""What the macOS platform layer does, checked without a Mac to check it on.

Both behaviours here are decisions about *which* call to make, and neither
needs Apple's implementation to be read back: releasing the thread's context is
``CGLSetCurrentContext(NULL)`` guarded by whether one was current, and looking
an entry point up is the dynamic loader, because the OpenGL framework exports
every entry point it serves as an ordinary symbol and offers no
get-proc-address call of its own.

So the loader is asked for a symbol this process really has, and CGL is stood
in for.  What is left for a Mac to answer is only whether the framework exports
a particular ``gl*`` name, which is the machine's business rather than this
layer's.
"""

import ctypes
import sys

import pytest

from OpenGL.platform import darwin


@pytest.fixture
def c_library():
    """A library this process can look a symbol up in, whichever platform.

    ``CDLL(None)`` is the process itself, which is POSIX's way of reaching the
    C library; Windows has no such handle and names the C runtime instead.
    What the cases below need is only a real library with a symbol they can
    name, since the lookup is what is under test rather than anything about
    which library answered.
    """
    return ctypes.CDLL('msvcrt' if sys.platform == 'win32' else None)


@pytest.fixture
def platform():
    """A DarwinPlatform with nothing loaded, for the tests to fill in.

    ``GL`` and ``GetCurrentContext`` are lazy properties, which set themselves
    on the instance on first read -- so an instance attribute stands in for
    either without the framework ever being reached for.
    """
    return darwin.DarwinPlatform()


class TestLookingUpAnEntryPoint:
    """The framework has no get-proc-address, so the loader is asked."""

    def test_it_answers_the_address_of_a_symbol_that_exists(
        self, platform, c_library
    ):
        platform.GL = c_library
        address = platform.getExtensionProcedure(b'malloc')
        assert address == ctypes.cast(c_library.malloc, ctypes.c_void_p).value

    def test_a_name_nothing_exports_is_no_address_rather_than_an_error(
        self, platform, c_library
    ):
        """Which is what the callers expect: `constructFunction` reads the
        answer as "the extension is claimed but the function is not there"."""
        platform.GL = c_library
        assert platform.getExtensionProcedure(b'glNoSuchEntryPointExists') is None

    def test_the_name_may_be_text_as_well_as_bytes(self, platform, c_library):
        platform.GL = c_library
        assert platform.getExtensionProcedure('malloc') == (
            platform.getExtensionProcedure(b'malloc')
        )


class FakeCGL:
    """CGL's current-context pair, with the context a plain integer."""

    def __init__(self, current=0):
        self.current = current
        self.calls = []

    def get(self):
        return self.current

    def set(self, context):
        self.calls.append(context)
        self.current = context or 0
        return 0


class TestReleasingTheContext:
    def test_releasing_what_was_current_says_so(self, platform):
        cgl = FakeCGL(current=0x1234)
        platform.GetCurrentContext = cgl.get
        platform.SetCurrentContext = cgl.set
        assert platform.releaseCurrentContext() is True
        assert cgl.calls == [None], 'CGL is released by making NULL current'
        assert not cgl.get()

    def test_releasing_when_nothing_is_current_says_that_too(self, platform):
        cgl = FakeCGL(current=0)
        platform.GetCurrentContext = cgl.get
        platform.SetCurrentContext = cgl.set
        assert platform.releaseCurrentContext() is False
        assert cgl.calls == [], 'nothing to release is nothing to call'

    def test_a_release_that_did_not_take_is_not_reported_as_one(self, platform):
        """A caller releases so that another binding API may take the thread,
        and takes the answer as permission to.  Saying yes for a context still
        current hands that caller the failure this call exists to avoid."""
        cgl = FakeCGL(current=0x1234)
        platform.GetCurrentContext = cgl.get
        platform.SetCurrentContext = lambda context: 0  # refuses, silently
        assert platform.releaseCurrentContext() is False
