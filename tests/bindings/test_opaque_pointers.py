#! /usr/bin/env python3
"""``OpenGL._opaque``: a handle the API hands back and takes again.

EGL contexts and displays, OSMesa contexts, GLX contexts and ``GLsync`` fences
are all opaque pointers -- the C API says only "a handle", and PyOpenGL wraps
each in a pointer class of its own so one kind cannot be passed where another
belongs.

What matters about a handle is that two of them naming the same object are the
same handle.  Nothing hands back the identical Python object twice:
``GetCurrentContext`` builds a new pointer on every call, and so does every
entry point returning one.  So a handle that compares by object identity is a
handle that is never equal to itself, and the two places that matters are

- **as a dictionary key**, which is how ``OpenGL.contextdata`` stores anything
  per context: the client-side arrays the GL goes on reading after the call
  that registered them, and the cached version and extension list.  A key that
  hashes alike and compares unequal is a lookup that always misses -- so the
  arrays are never found again, a fresh entry accumulates on every call, and
  the cache re-pulls the extension string every time it is asked.

- **in a caller's own code**, where ``if context == self.context`` is the
  ordinary way to ask whether the context has changed.

These are asked of the classes rather than of a driver, so they run everywhere
and need no GL.

https://github.com/mcfletch/pyopengl/issues/33
"""

import ctypes
import importlib
import pickle

import pytest

from OpenGL._opaque import opaque_pointer_cls
from OpenGL.raw.GL._types import GLsync

#: The real handle classes, named rather than imported at module level: a raw
#: module for a window-system API is built against the platform plugin this
#: run selected, so importing EGL's under the OSMesa platform -- or OSMesa's
#: under any other -- is an error before a single case is collected.  GL's is
#: always there, so the list is never empty.
_REAL_HANDLES = (
    ('OpenGL.raw.EGL._types', 'EGLContext'),
    ('OpenGL.raw.EGL._types', 'EGLDisplay'),
    ('OpenGL.raw.osmesa._types', 'OSMesaContext'),
    ('OpenGL.raw.GLX._types', 'GLXContext'),
)


def _handle_classes():
    found = {'GLsync': GLsync}
    for module_name, name in _REAL_HANDLES:
        try:
            found[name] = getattr(importlib.import_module(module_name), name)
        except Exception:      # this run's platform has no such binding
            continue
    # One made here as well, because `opaque_pointer_cls` is public and a
    # binding for a new API calls it -- so the behaviour has to belong to the
    # factory rather than to the four classes that happen to exist today.
    found['made-for-this-case'] = opaque_pointer_cls('SomethingContext')
    return found


HANDLES = _handle_classes()


def at(cls, address):
    """A handle of `cls` naming `address`, as an entry point would return."""
    return ctypes.cast(ctypes.c_void_p(address), cls)


@pytest.mark.parametrize('cls', list(HANDLES.values()), ids=list(HANDLES))
class TestTwoHandlesForOneObject:
    """Built separately, as two calls into the driver would build them."""

    def test_they_are_not_the_same_object(self):
        """The premise: nothing caches these, so identity is not the answer."""
        assert at(cls_ := self.cls, 0x1234) is not at(cls_, 0x1234)

    def test_they_compare_equal(self):
        assert at(self.cls, 0x1234) == at(self.cls, 0x1234)

    def test_they_hash_alike(self):
        assert hash(at(self.cls, 0x1234)) == hash(at(self.cls, 0x1234))

    def test_one_finds_what_the_other_stored(self):
        """The property ``contextdata`` depends on."""
        stored = {at(self.cls, 0x1234): 'the value'}
        assert stored.get(at(self.cls, 0x1234)) == 'the value'

    def test_a_second_store_replaces_the_first(self):
        """Otherwise every call adds an entry nothing will ever look up."""
        stored = {}
        for _ in range(50):
            stored[at(self.cls, 0x1234)] = 'the value'
        assert len(stored) == 1

    def test_different_addresses_are_different_handles(self):
        assert at(self.cls, 0x1234) != at(self.cls, 0x5678)
        assert not (at(self.cls, 0x1234) == at(self.cls, 0x5678))

    def test_a_null_handle_is_readable(self):
        """A driver answers "none" with a null pointer, and a caller compares
        it like any other rather than knowing to test it differently."""
        null = at(self.cls, 0)
        assert null == at(self.cls, 0)
        assert null != at(self.cls, 0x1234)
        hash(null)

    def test_a_handle_is_not_equal_to_a_bare_integer(self):
        """The address is not the handle: a class the API distinguishes must
        not compare equal to the number inside it."""
        assert at(self.cls, 0x1234) != 0x1234

    # `cls` arrives as an attribute through parametrize's class form.
    @pytest.fixture(autouse=True)
    def _bind(self, cls):
        self.cls = cls


def test_two_kinds_of_handle_are_never_equal():
    """Two kinds at one address are different things; comparing by address
    alone would say otherwise."""
    one = opaque_pointer_cls('OneKind')
    other = opaque_pointer_cls('AnotherKind')
    assert at(one, 0x1234) != at(other, 0x1234)
    assert {at(one, 0x1234): 'one'}.get(at(other, 0x1234)) is None


def test_the_address_of_a_null_handle_is_none_rather_than_a_fault():
    assert at(GLsync, 0).address is None
    assert at(GLsync, 0x1234).address == 0x1234


def test_pickling_is_still_refused():
    """A handle belongs to a driver in this process. Whatever ctypes does with
    one, adding equality must not turn it into something that travels."""
    with pytest.raises(Exception):
        pickle.dumps(at(GLsync, 0x1234))
