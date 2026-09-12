#! /usr/bin/env python3
"""A destroyed context takes its cached description with it.

A GL context's extension list and version are properties of that context, and
PyOpenGL caches them against its handle.  A handle is an address the driver
hands out again: three hundred contexts through this suite reuse a couple of
dozen addresses.  So a cache that outlives its context is read by the next one,
and answers about a context that no longer exists.

What that looks like from outside is an entry point the current context exports
reported as absent, because the gate that admits it asked the dead context's
extension list.  It is not a corner: a program that closes one window and opens
another hits it, and so does one that makes a desktop-GL context and then an
OpenGL-ES context -- which is what the suite does, and why several ES cases used
to skip depending on which files a run happened to collect first.
"""

import unittest

import pytest

from glcontext import Context
from OpenGL import contextdata, dispatch, platform


def held_for(handle):
    """Everything cached against `handle`, across the context stores.

    The handle is whatever ``GetCurrentContext`` answered and is kept as that
    -- an integer on some platforms, an opaque pointer on others -- because it
    is the key ``contextdata`` filed the entries under.  Reducing it to an
    integer would look up something that was never stored, and on a platform
    whose handle is a pointer ``int()`` will not even convert it.
    """
    keys = []
    for storage in contextdata.STORAGES:
        keys.extend(storage.get(handle, {}))
    return keys


class TestTheCachesGoWithTheContext(unittest.TestCase):
    def test_the_description_is_dropped_when_the_context_is_forgotten(self):
        with Context(profile='compatibility', gl_version=(2, 1)):
            handle = platform.PLATFORM.GetCurrentContext()
            platform.PLATFORM.checkExtension('GL_ARB_multitexture')
            described = [key for key in held_for(handle)
                         if dispatch._describes_a_context(key)]
            assert described, 'nothing was cached to test the dropping of'
        left = [key for key in held_for(handle)
                if dispatch._describes_a_context(key)]
        assert left == [], (
            'these describe a context that has been destroyed: %r' % (left,)
        )

    def test_what_the_caller_stored_is_left_alone(self):
        """Only the description goes.  Client array pointers are the caller's,
        and the driver may still be reading them -- which is what
        ``contextdata.cleanupContext`` warns about."""
        with Context(profile='compatibility', gl_version=(2, 1)):
            handle = platform.PLATFORM.GetCurrentContext()
            contextdata.setValue('a caller of ours', [1, 2, 3], weak=False)
        assert 'a caller of ours' in held_for(handle)
        contextdata.delValue('a caller of ours', context=handle)


class TestAnEntryPointFollowsTheCurrentContext(unittest.TestCase):
    """The symptom the caching bug produced, asserted directly."""

    def test_an_es_extension_is_seen_after_a_gl_context_held_the_handle(self):
        from OpenGL.GLES2.EXT.texture_border_clamp import glTexParameterIivEXT

        with Context(profile='compatibility', gl_version=(2, 1)):
            first = platform.PLATFORM.GetCurrentContext()
            # Desktop GL does not offer it, so this resolves to nothing and the
            # answer is cached against `first`.
            bool(glTexParameterIivEXT)

        try:
            with Context(api='gles', gl_version=(3, 1)):
                second = platform.PLATFORM.GetCurrentContext()
                # Asked of the platform rather than through the fixture's
                # helper: this is an ES context, and the indexed query the
                # helper uses is GLES3's.
                available = platform.PLATFORM.checkExtension(
                    'GL_EXT_texture_border_clamp'
                )
                answered = bool(glTexParameterIivEXT)
        except unittest.SkipTest:
            raise
        if first != second:
            self.skipTest(
                'the driver did not reuse the handle, so the stale cache this '
                'is about was never in the way'
            )
        if not available:
            self.skipTest('this driver has no GL_EXT_texture_border_clamp on ES')
        assert answered, (
            'the ES context offers the extension, but the entry point was '
            'reported absent -- the destroyed GL context on the same handle '
            'still had its extension list cached'
        )


if __name__ == '__main__':
    unittest.main()
