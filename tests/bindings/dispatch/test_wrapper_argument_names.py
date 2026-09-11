"""A wrapper says which arguments a Python caller passes, however it was built.

Which converters a wrapper installs depends on the configuration: with
``ERROR_ON_COPY`` an array argument is passed through as it is, so nothing is
installed to convert it.  The call is the same either way, and whatever reads
the call off the wrapper -- the stub generator, the documentation -- has to
get the same answer from :meth:`OpenGL.wrapper.Wrapper.pyArgNames` whichever
converters there are.
"""

from OpenGL.wrapper import Wrapper


class Operation:
    """Stands in for a ctypes function: a name, and its C argument names."""

    __name__ = 'glOperation'

    def __init__(self, *argNames):
        self.argNames = list(argNames)


def wrapped():
    return Wrapper(Operation('target', 'n', 'data'))


def test_with_no_converters_a_caller_passes_the_c_arguments():
    assert wrapped().pyArgNames() == ['target', 'n', 'data']


def test_a_converted_argument_is_still_passed():
    wrapper = wrapped().setPyConverter('data', None)
    assert wrapper.pyArgNames() == ['target', 'n', 'data']


def test_a_removed_argument_is_not():
    """``glDeleteTextures`` reads ``n`` off the array; the caller never gives it."""
    wrapper = wrapped().setPyConverter('n')
    assert wrapper.pyArgNames() == ['target', 'data']


def test_the_answer_is_the_caller_s_to_keep():
    wrapper = wrapped().setPyConverter('n')
    wrapper.pyArgNames().append('extra')
    assert wrapper.pyArgNames() == ['target', 'data']


def test_an_argument_s_index_is_its_place_in_that_list():
    wrapper = wrapped()
    assert wrapper.pyArgIndex('data') == 2
    wrapper.setPyConverter('n')
    assert wrapper.pyArgIndex('data') == 1
