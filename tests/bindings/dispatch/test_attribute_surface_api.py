#! /usr/bin/env python3
"""An entry point knows which API it belongs to, and everything keyed on a name
uses it.

``glClear`` exists in GL and in GLES2 as separate bindings resolved from
separate libraries, so a name alone does not identify one.  Every place that
looks an entry point up has to say which -- otherwise demoting a GLES2 binding
finds the desktop GL function, from the GL library, which on a system serving
both is a call into the wrong library.
"""

import pytest

dispatch = pytest.importorskip('OpenGL._dispatch')

from OpenGL import dispatch as _dispatch_api  # noqa: E402

# Built is not the same as running: PYOPENGL_DISPATCH=ctypes leaves the
# extension importable and its entry points uninstalled, and everything below
# reads them.  settle() makes the choice now rather than at the first entry
# point, which is what lets this be asked before the imports underneath.
if _dispatch_api.settle() != 'c':  # pragma: no cover - depends on the axis
    pytest.skip(
        'the C dispatch layer is not the implementation running: %s'
        % (_dispatch_api.status().reason,),
        allow_module_level=True,
    )

# Both, because the point is that they are different entry points: importing
# one installs the C layer over its bindings and leaves the other's alone.
import OpenGL.GL  # noqa: E402,F401
import OpenGL.GLES2  # noqa: E402,F401


class TestAnEntryPointSaysWhichAPI:
    def test_the_two_glClears_are_different_entry_points(self):
        desktop = dispatch.entry_points[('GL', 'glClear')]
        embedded = dispatch.entry_points[('GLES2', 'glClear')]
        assert desktop is not embedded

    def test_each_reports_its_own_api(self):
        assert dispatch.entry_points[('GL', 'glClear')].api == 'GL'
        assert dispatch.entry_points[('GLES2', 'glClear')].api == 'GLES2'

    def test_api_is_read_only(self):
        proc = dispatch.entry_points[('GL', 'glClear')]
        with pytest.raises(AttributeError):
            proc.api = 'GLES2'


class TestLookupsKeyOnTheAPI:
    def test_demotion_binds_the_library_the_entry_point_came_from(self):
        """``demote_and_call`` falls back to the ctypes wrapper for a
        customisation the C does not implement.  Which binding it falls back to
        has to be the one underneath *this* entry point."""
        from OpenGL import platform
        from OpenGL._dispatch import support

        gles2 = getattr(platform.PLATFORM, 'GLES2', None)
        if gles2 is None:
            # Windows ships no OpenGL-ES: it arrives only with an application
            # carrying ANGLE, and the platform answers None where the machine
            # has none.  There is then a single library for every entry point,
            # so which one a demotion binds is not observable here.
            pytest.skip('this platform offers no separate OpenGL-ES library')
        embedded = dispatch.entry_points[('GLES2', 'glClear')]
        binding = support.ctypes_callable(embedded.__name__, embedded.api)
        assert binding.DLL is gles2 or (
            binding.DLL is not getattr(platform.PLATFORM, 'GL', None)
        )

    def test_a_swallowed_customisation_is_not_replayed_onto_another_api(self):
        """A customisation the C already performs is remembered so that a
        *derived* function built from the same entry point can replay it.  Two
        APIs declaring the same name must not share that record."""
        from OpenGL._dispatch import support

        desktop = dispatch.entry_points[('GL', 'glClear')]
        embedded = dispatch.entry_points[('GLES2', 'glClear')]

        # Saved and put back, not cleared.  The record is the process's, and
        # the friendly modules fill it while they are being imported: a test
        # that empties it takes away what `demoted_callable` needs to rebuild
        # a wrapper, and every later test in the process gets the raw binding
        # instead.  (Which is what happened -- as a failure in a different
        # file, in whichever suite happened to be collected afterwards.)
        before = dict(support._swallowed)
        support._swallowed.clear()
        try:
            support.record_custom(desktop, 'setStoreValues', ('mask',))
            assert support.swallowed_for(embedded) == {}
            assert support.swallowed_for(desktop) != {}
        finally:
            support._swallowed.clear()
            support._swallowed.update(before)


class TestSignaturesAreBuiltNotCompiled:
    """``inspect.signature()`` reads ``__text_signature__`` only from the
    builtin callable types, so an entry point answers with a Signature of its
    own.  Building one out of the parts it already carries is both cheaper than
    compiling a function definition and unable to raise SyntaxError at the
    point a documentation tool asks."""

    def test_a_no_argument_entry_point(self):
        import inspect

        proc = dispatch.entry_points[('GL', 'glFinish')]
        assert str(inspect.signature(proc)) == '()'

    def test_an_ordinary_entry_point(self):
        import inspect

        proc = dispatch.entry_points[('GL', 'glBindTexture')]
        signature = inspect.signature(proc)
        assert str(signature) == '(target, texture, /)'
        assert all(
            parameter.kind is inspect.Parameter.POSITIONAL_ONLY
            for parameter in signature.parameters.values()
        )

    def test_an_optional_argument_is_optional(self):
        """glGenTextures(n, textures=None): the output array may be passed in."""
        import inspect

        proc = dispatch.entry_points[('GL', 'glGenTextures')]
        parameters = inspect.signature(proc).parameters
        assert parameters['n'].default is inspect.Parameter.empty
        assert parameters['textures'].default is None

    def test_the_module_compiles_no_source(self):
        from OpenGL._dispatch import support

        with open(support.__file__, encoding='utf-8') as handle:
            source = handle.read()
        assert 'exec(' not in source
        assert "compile(" not in source

    def test_two_apis_declaring_one_name_do_not_share_a_signature(self):
        import inspect

        # glClear takes one argument in both, so this is about the cache key
        # rather than about the answer: an entry point whose signature is
        # looked up by name alone can be handed another API's.
        for api in ('GL', 'GLES2'):
            proc = dispatch.entry_points[(api, 'glClear')]
            assert str(inspect.signature(proc)) == '(mask, /)'
