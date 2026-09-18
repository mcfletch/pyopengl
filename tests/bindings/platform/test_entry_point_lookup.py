#! /usr/bin/env python3
"""Where an entry point is looked for when the library does not export it.

Which names a GL library exports is the implementation's business, and it does
not follow the declarations.  Windows' ``opengl32`` exports the GL 1.1 set and
nothing above it, and Mesa's Windows ``osmesa`` library is built to the same
export list -- so ``glVertexAttribPointer`` is declared by a core version,
lives in the library on Linux, and on Windows arrives only through
``wglGetProcAddress`` or ``OSMesaGetProcAddress``.

:class:`OpenGL.platform.baseplatform.SplitEntryPointPlatform` is that: the
library first and the platform's procedure lookup after it.  Windows has asked
both since long before this; OSMesa asked only the library, which is what made
a ``dispctypes`` run on Windows report ``glVertexAttribPointer`` undefined
against an OSMesa context the same run had just rendered through.

The route belongs only to a platform whose lookup can say no.  The cases at the
bottom are why: under libglvnd ``glXGetProcAddressARB`` answers with a dispatch
stub for any name at all, so a Linux platform taking this route would report
every undefined entry point as present.
"""

import ctypes
import sys

import pytest

from OpenGL.platform import baseplatform, osmesa

#: A name no library exports and no driver has.
ABSENT = 'glNoSuchEntryPointExists'

#: A name the library below really does export, so that "found in the library"
#: is a fact rather than a stand-in.
EXPORTED = 'malloc'


@pytest.fixture
def library():
    """A real library to look symbols up in, whichever platform.

    ``CDLL(None)`` is the process itself, which is POSIX's way of reaching the
    C library; Windows has no such handle and names the C runtime instead.
    ``buildFunction`` goes through ctypes' own ``(name, dll)`` lookup, so what
    these need is a genuine library with a name in it -- which library is not
    the question.
    """
    return ctypes.CDLL('msvcrt' if sys.platform == 'win32' else None)


class SplitPlatform(baseplatform.SplitEntryPointPlatform):
    """The class under test, with the one thing every real platform supplies.

    A calling convention: the base declares none, because which one a library
    was built with is the platform's own business.
    """

    DEFAULT_FUNCTION_TYPE = staticmethod(ctypes.CFUNCTYPE)


class RecordingLookup:
    """A ``getExtensionProcedure`` that answers for the names it was given."""

    def __init__(self, **addresses):
        #: Every name it was asked about, in order.
        self.asked = []
        self.addresses = addresses

    def __call__(self, name):
        self.asked.append(name)
        return self.addresses.get(name.decode('ascii'), None)


def lookup_for(platform, **addresses):
    """Give ``platform`` a recording procedure lookup and answer with it.

    An instance attribute, since a platform's ``getExtensionProcedure`` is a
    lazy property that would otherwise reach for the real library.
    """
    platform.getExtensionProcedure = RecordingLookup(**addresses)
    return platform.getExtensionProcedure


@pytest.fixture
def platform(library):
    """A split platform with the library above, and a lookup that has ABSENT"""
    platform = SplitPlatform()
    platform.GL = library
    # Any address will do: the case is which route answered, and a ctypes
    # function pointer is built from an integer without dereferencing it.
    lookup_for(platform, **{ABSENT: 0xF00D})
    return platform


def built(platform, name, **named):
    return platform.constructFunction(
        name, platform.GL, resultType=None, argTypes=(), argNames=(), **named
    )


class TestANameTheLibraryExports:
    def test_it_comes_from_the_library(self, platform):
        assert built(platform, EXPORTED) is not None

    def test_the_lookup_is_not_asked(self, platform):
        """It costs a call into the driver, and the library already answered."""
        built(platform, EXPORTED)
        assert platform.getExtensionProcedure.asked == []


class TestANameTheLibraryDoesNotExport:
    def test_the_lookup_answers_for_it(self, platform):
        assert built(platform, ABSENT) is not None

    def test_the_lookup_was_asked_for_that_name(self, platform):
        built(platform, ABSENT)
        assert platform.getExtensionProcedure.asked == [ABSENT.encode('ascii')]

    def test_a_name_neither_has_is_still_an_attribute_error(self, platform):
        """Which is what ``createBaseFunction`` turns into a null function."""
        with pytest.raises(AttributeError):
            built(platform, 'glSomeOtherNameNothingHas')


class TestTheRoutesAPlatformDeclares:
    """``entryPointRoutes`` is what says where a platform keeps its names."""

    def test_the_library_is_asked_before_the_lookup(self, platform):
        routes = platform.entryPointRoutes(platform.GL)
        assert routes[0] == dict(dll=platform.GL)
        assert routes[-1].get('force_extension') is True

    def test_a_route_that_raises_something_else_is_not_swallowed(self, platform):
        """Only ``AttributeError`` says "not here"; anything else is a defect
        in the route and has to reach the caller."""

        def refuse(name):
            raise RuntimeError('the driver refused the question')

        platform.getExtensionProcedure = refuse
        with pytest.raises(RuntimeError):
            built(platform, ABSENT)


class TestTheOSMesaPlatformTakesTheRoute:
    """OSMesa is the platform this reaches, and the reason it was found.

    Its library is the whole of Mesa on Linux and exports every entry point in
    it, so the ctypes path never had to look further there.  The same library
    built for Windows exports the GL 1.1 set, and ``OSMesaGetProcAddress`` is
    what the platform offers for the rest.
    """

    def test_a_name_the_library_lacks_comes_from_its_lookup(self, library):
        platform = osmesa.OSMesaPlatform()
        platform.GL = library
        lookup = lookup_for(platform, **{ABSENT: 0xF00D})
        assert built(platform, ABSENT) is not None
        assert lookup.asked == [ABSENT.encode('ascii')]

    def test_the_lookup_it_offers_is_osmesa_get_proc_address(self):
        """Named rather than assumed: it is the only route to GL 2.0 and above
        on a platform whose library was built to the GL 1.1 export list."""
        platform = osmesa.OSMesaPlatform()

        class FakeLibrary:
            OSMesaGetProcAddress = staticmethod(lambda name: None)

        platform.GL = FakeLibrary
        assert platform.getExtensionProcedure is FakeLibrary.OSMesaGetProcAddress


class TestAPlatformWhoseLookupCannotSayNo:
    """Which is why this is a route a platform opts into rather than the rule.

    Under libglvnd ``glXGetProcAddressARB`` answers with a dispatch stub for
    any name at all -- ``somebodyElsesEntryPoint`` included -- so a Linux
    platform that fell back to it would report every undefined entry point as
    present and hand the caller a stub to call.  The GLU, GLUT and GLE errors
    that say "the library was not found" are the ones that would go first.
    """

    def test_the_linux_platform_does_not_take_it(self):
        from OpenGL.platform import linux

        assert not issubclass(
            linux.LinuxPlatform, baseplatform.SplitEntryPointPlatform
        )

    @pytest.mark.skipif(
        sys.platform != 'linux', reason='glXGetProcAddressARB is the subject'
    )
    def test_this_machine_s_lookup_answers_for_a_name_no_api_has(self):
        """The fact the case above is protecting against, on the machine in
        front of us.  A driver whose lookup *is* a query makes this a skip
        rather than a pass, so the case never claims more than it showed."""
        from OpenGL.platform import PLATFORM

        if isinstance(PLATFORM, baseplatform.SplitEntryPointPlatform):
            pytest.skip('this machine selected a platform that takes the route')
        if not PLATFORM.getExtensionProcedure(b'somebodyElsesEntryPoint'):
            pytest.skip("this machine's lookup is a query and answers no")
        assert PLATFORM.getExtensionProcedure(b'glNoSuchEntryPointExists')
