"""Calls that can block must let other Python threads run.

The ctypes implementation reaches the driver through a ``CDLL`` function
pointer, which releases the GIL for the duration of the foreign call.  A
generated stub calls a raw function pointer, so unless it says otherwise the
GIL is held for the whole call -- and a 36 ms ``glReadPixels`` then stops every
other thread in the process for 36 ms.

Releasing costs 15-25 ns, against 57 ns for ``glBindTexture``, so it is not
something to do on every call by reflex.  It is done for the calls that can
actually block: the driver waiting on the GPU, a shader compile, a buffer
mapping, a swap under vsync.
"""

import os

import paths
import pytest

from cdispatch import blocking, emit_c, extract

PACKAGE = paths.PACKAGE
REGISTRY = paths.REGISTRY

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def commands():
    return extract.extract_tree(PACKAGE)


class TestWhichCallsBlock:
    @pytest.mark.parametrize(
        'name',
        [
            'glFinish',
            'glFlush',
            'glClientWaitSync',
            'glReadPixels',
            'glGetTexImage',
            'glMapBuffer',
            'glMapBufferRange',
            'glUnmapBuffer',
            'glCompileShader',
            'glLinkProgram',
        ],
    )
    def test_a_call_that_waits_on_the_driver_releases(self, name):
        assert blocking.blocks(name), name

    @pytest.mark.parametrize(
        'name', ['glBindTexture', 'glUniform1f', 'glVertex3f', 'glEnable']
    )
    def test_a_call_that_cannot_block_does_not_pay_for_it(self, name):
        assert not blocking.blocks(name), name

    def test_the_swap_calls_of_every_windowing_api(self):
        for name in ('eglSwapBuffers', 'glXSwapBuffers', 'wglSwapBuffers'):
            assert blocking.blocks(name), name

    def test_the_set_is_small(self, commands):
        """If this were most of the tree the trade would not be worth making."""
        marked = [key for key in commands if blocking.blocks(key[1])]
        assert 0 < len(marked) < len(commands) // 8


class TestEmission:
    def test_a_blocking_stub_calls_the_releasing_macro(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glFinish')])
        assert 'PYGL_CALL_V_BLOCKING' in text

    def test_a_blocking_stub_with_a_result_releases_too(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glClientWaitSync')])
        assert 'PYGL_CALL_R_BLOCKING' in text

    def test_an_ordinary_stub_does_not(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glBindTexture')])
        assert 'BLOCKING' not in text


# Module scope rather than a fixture inside the class below: pytest asks for a
# `classmethod` there, and a `classmethod` object carries no `__name__` before
# Python 3.10, which is inside this package's supported range.
@pytest.fixture(scope='module')
def header():
    with open(os.path.join(paths.ROOT, 'accelerate', 'src', 'c', 'pygl.h'),
              encoding='utf-8') as handle:
        return handle.read()


class TestTheMacro:
    """The release has to wrap the driver call and nothing else: calling into
    CPython with the GIL released is a crash rather than a slow program."""

    @pytest.mark.parametrize(
        'macro', ['PYGL_CALL_V_BLOCKING', 'PYGL_CALL_R_BLOCKING']
    )
    def test_it_releases_and_reacquires(self, header, macro):
        body = header.split('#define %s' % (macro,), 1)[1].split('#define', 1)[0]
        assert 'Py_BEGIN_ALLOW_THREADS' in body
        assert 'Py_END_ALLOW_THREADS' in body

    @pytest.mark.parametrize(
        'macro', ['PYGL_CALL_V_BLOCKING', 'PYGL_CALL_R_BLOCKING']
    )
    def test_nothing_python_sits_inside_the_released_region(self, header, macro):
        body = header.split('#define %s' % (macro,), 1)[1].split('#define', 1)[0]
        inside = body.split('Py_BEGIN_ALLOW_THREADS', 1)[1].split(
            'Py_END_ALLOW_THREADS', 1
        )[0]
        for forbidden in ('PyObject', 'PyErr', 'PyLong', 'PyMem', 'pygl_'):
            assert forbidden not in inside, (macro, forbidden, inside)
