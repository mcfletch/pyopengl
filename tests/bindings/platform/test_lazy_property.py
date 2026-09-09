"""``lazy_property``: a platform attribute that costs a library load to answer.

The platform objects describe libraries -- ``GL``, ``GLUT``, the driver's
current-context function -- and finding one means loading it.  Doing that for
every attribute when the module is imported would load libraries a program
never asks about, so each is worked out when it is first read and cached on the
instance from then on.

That leaves the class itself, where there is no instance to work anything out
for.  Reading the attribute there has to answer with the descriptor, which is
what every other descriptor in Python does: it is how ``help()``, ``inspect``
and a documentation build ask a class what it has without owning one of them.
"""

import pytest

from OpenGL.platform.baseplatform import BasePlatform, lazy_property


class Subject:
    """A class with one lazy attribute and a count of what it cost."""

    loads = 0

    @lazy_property
    def library(self):
        """What was found, once."""
        Subject.loads += 1
        return 'the library'


class TestReadingItFromAnInstance:
    def setup_method(self):
        Subject.loads = 0

    def test_it_answers_what_the_getter_returned(self):
        assert Subject().library == 'the library'

    def test_and_only_asks_once(self):
        subject = Subject()
        assert [subject.library, subject.library, subject.library]
        assert Subject.loads == 1

    def test_by_caching_on_the_instance_it_was_read_from(self):
        """Not on the class: two platform objects may find different things."""
        subject = Subject()
        assert subject.library
        assert subject.__dict__['library'] == 'the library'
        assert 'library' not in vars(Subject) or isinstance(
            vars(Subject)['library'], lazy_property
        )


class TestReadingItFromTheClass:
    def setup_method(self):
        Subject.loads = 0

    def test_it_answers_with_the_descriptor(self):
        assert isinstance(Subject.library, lazy_property)

    def test_and_does_not_run_the_getter(self):
        """There is no instance to run it against, and no library to load."""
        Subject.library  # noqa: B018 - reaching for it is the whole case
        assert Subject.loads == 0

    def test_the_docstring_comes_with_it(self):
        """What help() and a documentation build read off the class."""
        assert Subject.library.__doc__ == 'What was found, once.'

    @pytest.mark.parametrize('name', ['CurrentContextIsValid', 'OpenGL'])
    def test_the_base_platform_can_be_asked_what_it_has(self, name):
        assert isinstance(getattr(BasePlatform, name), lazy_property)

    def test_and_so_can_the_platform_this_machine_installed(self):
        """Which is where the libraries are named, and where this bites: the
        getter run against ``None`` raises from inside whichever load it is --
        on macOS, ``GetCurrentContext`` reaching for ``None.CGL``."""
        import OpenGL.platform

        installed = type(OpenGL.platform.PLATFORM)
        lazy = [
            name
            for name, value in vars(installed).items()
            if isinstance(value, lazy_property)
        ]
        assert lazy, 'no lazy attributes on %s to ask about' % (installed.__name__,)
        for name in lazy:
            assert isinstance(getattr(installed, name), lazy_property), name
