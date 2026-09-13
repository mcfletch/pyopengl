#! /usr/bin/env python3
"""What a call says when the library it lives in is not on the machine.

Three tickets are one person meeting `NullFunctionError` and having nothing to
go on. #59 is `gluOrtho2D` undefined on Arch and on CentOS; #54 is GLUT, with
the answer arriving thirteen months later as a comment saying
`apt-get install freeglut3-dev`; #125 is `glutInitDisplayMode` on Windows.
Every one of them is the same thing: the library was not found, so *every*
entry point in it is undefined, and

    Attempt to call an undefined function gluOrtho2D, check for
    bool(gluOrtho2D) before calling

reads as a defect in PyOpenGL rather than as a package that is not installed.
It also sends the reader to check one name, when the answer is that none of
them will ever resolve.

The two situations are worth telling apart. A library that is absent is the
caller's to fix and there is one thing to do about it. An entry point missing
from a library that *is* there is a driver or a version, and nothing to
install.

GLU, GLUT and GLE are not Khronos APIs, so they have no registry entry, no
slot in the C dispatch layer, and always arrive through ctypes -- which is why
this is the only place the message is built for them.

https://github.com/mcfletch/pyopengl/issues/59
https://github.com/mcfletch/pyopengl/issues/54
https://github.com/mcfletch/pyopengl/issues/125
"""

import pytest

from OpenGL import error
from OpenGL.platform import PLATFORM, baseplatform


def absent(name):
    """An entry point declared when its library could not be loaded.

    Which is exactly what the raw modules build on a machine with no GLU:
    ``dll=platform.PLATFORM.GLU`` is evaluated at import and answers ``None``,
    so every declaration in the module becomes one of these.
    """
    return PLATFORM.nullFunction(name, dll=None, resultType=None, argTypes=(),
                                 argNames=())


def unexported(name):
    """An entry point whose library is here and does not export it."""
    return PLATFORM.nullFunction(name, dll=PLATFORM.GL, resultType=None,
                                 argTypes=(), argNames=())


def message(function):
    with pytest.raises(error.NullFunctionError) as raised:
        function()
    return str(raised.value)


class TestALibraryThatIsNotOnTheMachine:
    def test_it_says_the_library_was_not_found(self):
        assert 'not found' in message(absent('gluOrtho2D'))

    def test_it_names_the_library(self):
        assert 'GLU' in message(absent('gluOrtho2D'))

    def test_it_says_every_entry_point_in_it_is_undefined(self):
        """The reader is about to check one name and find the next one gone
        too."""
        assert 'every' in message(absent('gluOrtho2D')).lower()

    def test_it_says_how_to_get_the_library(self):
        """#54's answer was a comment thirteen months later reading
        `apt-get install freeglut3-dev`. It belongs in the error."""
        said = message(absent('glutInit'))
        assert 'freeglut' in said, said

    @pytest.mark.parametrize(
        'name,library',
        [
            ('gluOrtho2D', 'GLU'),
            ('gluNewQuadric', 'GLU'),
            # Longest prefix first: this one starts with `glu` as well.
            ('glutInit', 'GLUT'),
            ('glutInitDisplayMode', 'GLUT'),
            ('gleExtrusion', 'GLE'),
            ('glBindTexture', 'GL'),
            ('glXCreateContext', 'GL'),
            ('wglGetProcAddress', 'GL'),
        ],
    )
    def test_the_prefix_says_which_library(self, name, library):
        """There is no object left to ask -- the platform answered None for it
        -- and the prefix is the API's own naming rather than a guess."""
        assert baseplatform.library_for_entry_point(name) == library

    def test_a_name_with_no_known_prefix_still_says_what_happened(self):
        """Without claiming to know which library it wanted."""
        said = message(absent('somebodyElsesEntryPoint'))
        assert 'not found' in said
        assert 'GLU' not in said

    def test_it_is_still_a_null_function_error(self):
        """Callers catch this, and the class is what they catch."""
        with pytest.raises(error.NullFunctionError):
            absent('gluOrtho2D')()

    def test_it_still_names_the_check(self):
        """`bool(name)` is what the exception has always pointed at, and what
        a caller who already handles this greps for."""
        said = message(absent('gluOrtho2D'))
        assert 'bool(gluOrtho2D)' in said


class TestAnEntryPointTheLibraryDoesNotExport:
    """A different situation, and it must not be described as the first one.

    The library loaded and a context is current. This entry point is not in
    it, which is a driver too old for it or an extension the machine does not
    have -- there is nothing to install.
    """

    def said(self):
        return baseplatform.undefined_function_message(
            'glNoSuchEntryPointExists', object(), has_context=True
        )

    def test_it_does_not_claim_the_library_is_missing(self):
        assert 'not found on this machine' not in self.said()

    def test_it_does_not_send_the_caller_looking_for_a_package(self):
        assert 'apt' not in self.said() and 'Debian' not in self.said()

    def test_it_names_the_entry_point(self):
        assert 'glNoSuchEntryPointExists' in self.said()

    def test_it_still_names_the_check(self):
        assert 'bool(glNoSuchEntryPointExists)' in self.said()

    def test_the_error_reaches_the_caller(self):
        """End to end through the real call, whichever branch this machine
        takes: it raises, and it names what could not be called."""
        said = message(unexported('glNoSuchEntryPointExists'))
        assert 'glNoSuchEntryPointExists' in said
        assert 'bool(glNoSuchEntryPointExists)' in said

    def test_an_unanswerable_context_question_reads_the_same_way(self):
        """A platform that cannot say whether a context is current must not
        turn that into a claim that one is not."""
        unknown = baseplatform.undefined_function_message(
            'glNoSuchEntryPointExists', object(), has_context=None
        )
        assert unknown == self.said()


class TestACallMadeBeforeThereIsAContext:
    """#115, and the most common way anybody meets this error.

    `glGenVertexArrays` on a 1080ti with a current NVIDIA driver is not a
    driver that lacks it. Above GL 1.1 an entry point's address comes from the
    context, so before one exists every such name is undefined -- and the old
    message described that as the function being undefined, which reads as the
    binding being broken rather than as two lines of the caller's program
    being in the wrong order.

    https://github.com/mcfletch/pyopengl/issues/115
    """

    def said(self):
        return baseplatform.undefined_function_message(
            'glGenVertexArrays', object(), has_context=False
        )

    def test_it_says_there_is_no_context(self):
        assert 'no OpenGL context is current' in self.said()

    def test_it_says_what_to_do_about_it(self):
        assert 'Create a context' in self.said()

    def test_it_does_not_blame_the_driver(self):
        assert 'driver too old' not in self.said()

    def test_it_does_not_claim_a_library_is_missing(self):
        assert 'not found on this machine' not in self.said()

    def test_a_missing_library_is_still_reported_as_one(self):
        """No context *and* no library is still a missing library: installing
        it is what the reader has to do first."""
        said = baseplatform.undefined_function_message(
            'gluOrtho2D', None, has_context=False
        )
        assert 'GLU library was not found' in said

    def test_the_platform_is_asked_on_the_error_path_only(self):
        """Asking the driver costs a call, and this one is already failing."""
        assert baseplatform._context_is_current() in (True, False, None)


class TestTheDeclarationPath:
    """From the declaration a raw module writes to the error a caller sees.

    The cases above build the null function directly. This one goes through
    ``createBaseFunction`` with ``dll=None``, which is the line
    ``OpenGL/raw/GLU/__init__.py`` actually runs on a machine with no GLU:
    ``dll=platform.PLATFORM.GLU`` is evaluated at import and answers None.
    """

    def declared(self, name):
        from OpenGL import platform

        return platform.createBaseFunction(
            name, dll=None, resultType=None, argTypes=(), argNames=()
        )

    def test_a_declaration_against_no_library_is_a_null_function(self):
        assert isinstance(
            self.declared('gluOrtho2D'), baseplatform._NullFunctionPointer
        )

    def test_calling_it_says_which_library_and_where_to_get_it(self):
        said = message(self.declared('gluOrtho2D'))
        assert 'GLU library was not found' in said, said
        assert 'libglu1-mesa' in said, said

    def test_it_is_falsy_so_the_documented_check_still_works(self):
        """`check for bool(...)` is the advice; it has to be true advice."""
        assert not self.declared('gluOrtho2D')


class TestACallWithSeveralPossibleNames:
    """``alternate()`` reports the same three situations.

    Thirty entry points are declared this way -- the framebuffer-object calls
    among them, where the core name and the ``EXT`` name are the same call --
    and none of them resolving says the same thing as one of them not
    resolving. It said something else.
    """

    def alternates(self):
        from OpenGL import extensions
        from OpenGL.platform import PLATFORM

        return extensions.alternate(
            'glBindFramebuffer',
            PLATFORM.nullFunction('glBindFramebuffer', dll=None, resultType=None,
                                  argTypes=(), argNames=()),
            PLATFORM.nullFunction('glBindFramebufferEXT', dll=None,
                                  resultType=None, argTypes=(), argNames=()),
        )

    def test_it_names_the_call_the_program_wrote(self):
        """Not only the alternatives, which are names the caller never used."""
        said = message(self.alternates())
        assert 'glBindFramebuffer' in said

    def test_it_still_lists_what_was_tried(self):
        assert 'glBindFramebufferEXT' in message(self.alternates())

    def test_it_still_names_the_check(self):
        assert 'bool(glBindFramebuffer)' in message(self.alternates())

    def test_it_says_why_rather_than_only_that(self):
        """Either a driver that has none of them or a call made too early --
        the old message offered neither."""
        said = message(self.alternates())
        assert 'no OpenGL context is current' in said or 'driver too old' in said


class TestTheAdviceIsWorthReading:
    @pytest.mark.parametrize('library', sorted(baseplatform.LIBRARY_SOURCES))
    def test_it_names_more_than_one_platform(self, library):
        """A reader has one machine in front of them and it may not be the
        one whose package name we happened to think of."""
        assert baseplatform.LIBRARY_SOURCES[library].count(';') >= 1

    def test_gl_itself_has_no_advice(self):
        """No OpenGL library at all is no graphics driver, which is a
        different conversation from a package that was not installed."""
        assert 'GL' not in baseplatform.LIBRARY_SOURCES


class TestTheWindowsAdviceNamesTheExtra:
    """This is what the GLUT split turns on, rather than the packaging.

    A Windows program calling ``glutInit()`` used to work on ``pip install
    PyOpenGL``, because the builds rode along in every wheel. They are
    ``PyOpenGL-glut-binaries`` now, so that program needs ``PyOpenGL[glut]``
    -- and the tutorials, textbooks and course materials that teach OpenGL
    through GLUT will not be updated. The error is the only thing those
    readers will see, so it has to carry the command.

    See ``plans/BUNDLED-DLLS.md``.
    """

    @pytest.mark.parametrize('library', ['GLUT', 'GLE'])
    def test_it_says_what_to_install(self, library):
        said = baseplatform.LIBRARY_SOURCES[library]
        assert 'PyOpenGL[glut]' in said, said

    @pytest.mark.parametrize('library', ['GLUT', 'GLE'])
    def test_it_does_not_still_point_at_the_bundled_directory(self, library):
        """``OpenGL/DLLS`` no longer exists, and sending a reader to look for
        a directory that cannot be there is worse than saying nothing."""
        assert 'DLLS' not in baseplatform.LIBRARY_SOURCES[library]

    def test_a_reader_who_wanted_gle_is_not_left_guessing(self):
        """One distribution carries both, so the GLE advice names an extra
        spelled ``glut``. That reads as a mistake unless it says why."""
        assert 'GLE' in baseplatform.LIBRARY_SOURCES['GLE']

    @pytest.mark.parametrize('name', ['glutInit', 'gleExtrusion'])
    def test_the_error_a_caller_sees_carries_it(self, name):
        """The wording is only worth holding where it reaches the caller, and
        ``glutInit`` is the call the reader of a tutorial will have made."""
        assert 'PyOpenGL[glut]' in message(absent(name)), name
