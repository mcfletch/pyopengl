#! /usr/bin/env python3
"""OSMesa's own entry points, against a real ``libOSMesa``.

OSMesa is Mesa's off-screen interface and a PyOpenGL platform in its own
right: the caller allocates the framebuffer, OSMesa rasterises into it, and
there is no window system, no drawable and no device node anywhere in the
arrangement.  ``tests/glcontext_osmesa.py`` drives the *rendering* through it;
this is the dozen entry points beside that, which nothing else calls.

**Run in a child, one per case.**  ``PYOPENGL_PLATFORM`` decides which library
every entry point is loaded from and is settled at the first import, so these
cannot run in a pytest process that chose something else -- and requiring the
whole run to have chosen OSMesa would mean they were exercised on one CI row
and skipped everywhere else.  A child costs a fraction of a second, which buys
a case per entry point and a crash that takes down only its own.

Skipped where ``libOSMesa`` is not installed, which is most machines: the
library is packaged apart from Mesa's GLX and EGL drivers (``libosmesa6`` on
Debian and Ubuntu).  Asked of ``ctypes.util.find_library`` rather than by
importing, since importing is what needs the platform already chosen.
"""

import ctypes.util
import json
import textwrap

import pytest

from childenv import run_in_child

pytestmark = pytest.mark.skipif(
    ctypes.util.find_library('OSMesa') is None,
    reason='no libOSMesa installed (libosmesa6 on Debian and Ubuntu)',
)

#: Every child starts here: the raw module, an RGBA buffer of a known size,
#: and a `report` dict it fills in and the epilogue prints.  Nothing is made
#: current -- a case that wants a current context says so, because several of
#: these are about what happens before or without one.
PREAMBLE = '''
import ctypes, json
from OpenGL import arrays
from OpenGL.raw.osmesa import mesa
from OpenGL.raw.GL.VERSION.GL_1_1 import *
from OpenGL.raw.GL.VERSION.GL_3_0 import (
    GL_MAJOR_VERSION, GL_MINOR_VERSION)

WIDTH, HEIGHT = 64, 48
report = {}

def buffer_for(width=WIDTH, height=HEIGHT, channels=4):
    return arrays.GLubyteArray.zeros((height, width, channels))

def as_image(buffer, width=WIDTH, height=HEIGHT, channels=4):
    raw = bytes(bytearray(buffer))
    return [
        [list(raw[(y * width + x) * channels:(y * width + x) * channels + channels])
         for x in range(width)]
        for y in range(height)
    ]
'''

EPILOGUE = '''
print(json.dumps(report))
'''


def osmesa(body):
    """Run `body` under the OSMesa platform; return the `report` it filled in.

    A child that raised has its traceback as the failure message, which is
    what a case here wants: the exception is the finding.
    """
    completed = run_in_child(
        PREAMBLE + textwrap.dedent(body) + EPILOGUE,
        check=False,
        PYOPENGL_PLATFORM='osmesa',
    )
    if completed.returncode != 0:
        pytest.fail(
            'the child exited %s\n--- stderr ---\n%s'
            % (completed.returncode, completed.stderr[-3000:]))
    if not completed.stdout.strip():
        pytest.fail('the child printed nothing\n--- stderr ---\n%s'
                    % (completed.stderr[-2000:],))
    return json.loads(completed.stdout.strip().splitlines()[-1])


# -- what the declarations say about themselves ------------------------------


class TestTheDeclarationsAgreeWithThemselves:
    """Each entry point names as many arguments as it declares types for.

    ctypes is lenient in a way that hides this: a function with no
    ``argtypes`` accepts any arguments at all, and one with fewer types than
    names still takes a positional call of the right length.  So a wrong
    declaration goes unnoticed until somebody calls by keyword, reads the
    signature, or passes the argument the declaration forgot -- and then it is
    a ``ctypes.ArgumentError`` about an argument position that does not
    correspond to anything in the documented signature.

    This module is hand-written and in no registry, so nothing generates these
    declarations and nothing else checks them.
    """

    def test_every_entry_point_names_as_many_arguments_as_it_types(self):
        report = osmesa("""
            report['found'] = {}
            for name in sorted(mesa.__all__):
                entry = getattr(mesa, name, None)
                names = getattr(entry, 'argNames', None)
                types = getattr(entry, 'argtypes', None)
                if names is None or types is None:
                    continue
                report['found'][name] = [list(names), len(types)]
        """)
        wrong = {
            name: (names, count)
            for name, (names, count) in report['found'].items()
            if len(names) != count
        }
        assert report['found'], 'no entry points were inspected'
        assert not wrong, '\n'.join(
            '%s names %d argument(s) %r but declares %d type(s)'
            % (name, len(names), names, count)
            for name, (names, count) in sorted(wrong.items()))


# -- making a context, three ways -------------------------------------------


class TestTheThreeConstructors:
    """OSMesa grew a constructor per era, and all three still ship."""

    def test_create_context_makes_one(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            report['made'] = bool(context)
            if context:
                mesa.OSMesaDestroyContext(context)
        ''')
        assert report['made']

    def test_create_context_ext_takes_its_buffer_sizes(self):
        """The middle constructor: depth, stencil and accum as arguments."""
        report = osmesa('''
            context = mesa.OSMesaCreateContextExt(
                mesa.OSMESA_RGBA, 24, 8, 0, None)
            report['made'] = bool(context)
            if context:
                buffer = buffer_for()
                mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                       WIDTH, HEIGHT)
                report['depth_bits'] = int(glGetIntegerv(GL_DEPTH_BITS))
                report['stencil_bits'] = int(glGetIntegerv(GL_STENCIL_BITS))
                glFinish()
                mesa.OSMesaDestroyContext(context)
        ''')
        assert report['made'], 'OSMesaCreateContextExt made no context'
        assert report['depth_bits'] >= 24, report
        assert report['stencil_bits'] >= 8, report

    def test_create_context_attribs_honours_the_profile_and_version(self):
        report = osmesa('''
            attributes = [
                mesa.OSMESA_FORMAT, mesa.OSMESA_RGBA,
                mesa.OSMESA_DEPTH_BITS, 24,
                mesa.OSMESA_STENCIL_BITS, 8,
                mesa.OSMESA_ACCUM_BITS, 0,
                mesa.OSMESA_PROFILE, mesa.OSMESA_CORE_PROFILE,
                mesa.OSMESA_CONTEXT_MAJOR_VERSION, 3,
                mesa.OSMESA_CONTEXT_MINOR_VERSION, 3,
                0,
            ]
            attributes = (ctypes.c_int * len(attributes))(
                *[int(one) for one in attributes])
            context = mesa.OSMesaCreateContextAttribs(attributes, None)
            report['made'] = bool(context)
            if context:
                buffer = buffer_for()
                mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                       WIDTH, HEIGHT)
                report['version'] = glGetString(GL_VERSION).decode()
                report['major'] = int(glGetIntegerv(GL_MAJOR_VERSION))
                report['minor'] = int(glGetIntegerv(GL_MINOR_VERSION))
                glFinish()
                mesa.OSMesaDestroyContext(context)
        ''')
        assert report['made'], 'OSMesaCreateContextAttribs made no context'
        assert (report['major'], report['minor']) >= (3, 3), report
        assert 'Core Profile' in report['version'], report['version']


# -- becoming current, and saying which context is ---------------------------


class TestBecomingCurrent:
    def test_make_current_takes_the_callers_buffer(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            report['accepted'] = bool(mesa.OSMesaMakeCurrent(
                context, buffer, GL_UNSIGNED_BYTE, WIDTH, HEIGHT))
            report['renderer'] = glGetString(GL_RENDERER).decode()
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['accepted']
        assert report['renderer'], 'a current context reported no renderer'

    def test_nothing_is_current_before_a_make_current(self):
        report = osmesa('''
            report['before'] = bool(mesa.OSMesaGetCurrentContext())
        ''')
        assert report['before'] is False

    def test_get_current_context_answers_the_one_made_current(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            current = mesa.OSMesaGetCurrentContext()
            report['is_current'] = bool(current)
            report['same'] = (
                ctypes.cast(current, ctypes.c_void_p).value
                == ctypes.cast(context, ctypes.c_void_p).value)
            report['hashable'] = hash(current) == hash(context)
            report['equal'] = current == context
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['is_current']
        assert report['same'], 'a different context came back'
        assert report['hashable'], 'two handles for one context hash apart'
        assert report['equal'], 'two handles for one context compare unequal'

    def test_a_destroyed_context_is_no_longer_current(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            glFinish()
            mesa.OSMesaDestroyContext(context)
            report['after'] = bool(mesa.OSMesaGetCurrentContext())
        ''')
        assert report['after'] is False


# -- what the context says about itself --------------------------------------


class TestTheStateQueries:
    """``OSMesaGetIntegerv`` is the only way to read what the context is.

    There is no ``glGet`` for the buffer's width, its row length or whether it
    is stored bottom-up: those belong to OSMesa rather than to the GL, and a
    program that reads its framebuffer back has to ask for them here.
    """

    def test_it_reports_the_size_it_was_made_current_with(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            report['width'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_WIDTH)
            report['height'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_HEIGHT)
            report['format'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_FORMAT)
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['width'] == 64, report
        assert report['height'] == 48, report
        assert report['format'] == 6408, report      # OSMESA_RGBA

    def test_it_reports_the_maximum_it_will_serve(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            report['max_width'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_MAX_WIDTH)
            report['max_height'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_MAX_HEIGHT)
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['max_width'] >= 64, report
        assert report['max_height'] >= 48, report


# -- the knobs that change what a readback means -----------------------------


class TestPixelStore:
    """``OSMesaPixelStore`` sets row length and which way up the buffer is.

    Both change where a pixel lands in the caller's array without changing
    anything the GL reports, so a program that gets them wrong reads a
    correct frame out of the wrong addresses.
    """

    def test_y_up_is_readable_and_settable(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            report['default'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_Y_UP)
            mesa.OSMesaPixelStore(mesa.OSMESA_Y_UP, 0)
            report['after_off'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_Y_UP)
            mesa.OSMesaPixelStore(mesa.OSMESA_Y_UP, 1)
            report['after_on'] = mesa.OSMesaGetIntegerv(mesa.OSMESA_Y_UP)
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['after_off'] == 0, report
        assert report['after_on'] == 1, report

    def test_it_names_its_arguments_as_the_api_does(self):
        """``argNames`` is the signature a reader and the stubs see.

        A raw entry point is a ctypes function and takes no keywords, so a
        wrong name here breaks nothing that runs -- which is why these had
        been ``(ctx, buffer, type, width, height)``, copied from
        ``OSMesaMakeCurrent``, for a call that takes a pname and a value.
        """
        report = osmesa("""
            report['names'] = list(mesa.OSMesaPixelStore.argNames)
        """)
        assert report['names'] == ['pname', 'value'], report['names']

    def test_y_up_decides_which_row_the_bottom_of_the_frame_is_in(self):
        """The behaviour, not the getter: draw a band across the bottom of
        the viewport and see which end of the array it lands in."""
        report = osmesa('''
            def band_row(y_up):
                context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
                buffer = buffer_for()
                mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                       WIDTH, HEIGHT)
                mesa.OSMesaPixelStore(mesa.OSMESA_Y_UP, y_up)
                glClearColor(0, 0, 0, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                # The bottom eighth of the viewport, in GL's coordinates.
                glEnable(GL_SCISSOR_TEST)
                glScissor(0, 0, WIDTH, HEIGHT // 8)
                glClearColor(0, 1, 0, 1)
                glClear(GL_COLOR_BUFFER_BIT)
                glDisable(GL_SCISSOR_TEST)
                glFinish()
                image = as_image(buffer)
                lit = [y for y, row in enumerate(image) if row[WIDTH // 2][1] > 128]
                mesa.OSMesaDestroyContext(context)
                return lit

            report['y_up_1'] = band_row(1)
            report['y_up_0'] = band_row(0)
        ''')
        up, down = report['y_up_1'], report['y_up_0']
        assert up, 'nothing was drawn with Y_UP=1'
        assert down, 'nothing was drawn with Y_UP=0'
        assert max(up) < 48 // 2, (
            'with Y_UP=1 the GL-bottom band should be at the start of the '
            'array, and it is in rows %r' % (up,))
        assert min(down) > 48 // 2, (
            'with Y_UP=0 the GL-bottom band should be at the end of the '
            'array, and it is in rows %r' % (down,))


# -- reaching the buffers Mesa is drawing into -------------------------------


class TestTheBuffersComeBack:
    def test_the_colour_buffer_is_the_one_we_gave_it(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            glClearColor(0, 0, 1, 1)
            glClear(GL_COLOR_BUFFER_BIT)
            glFinish()
            width, height, format, pointer = mesa.OSMesaGetColorBuffer(context)
            report['width'] = width
            report['height'] = height
            report['format'] = format
            report['same_address'] = (
                pointer.value
                == ctypes.cast(arrays.ArrayDatatype.dataPointer(buffer),
                               ctypes.c_void_p).value)
            # Read the first pixel through the pointer OSMesa handed back.
            first = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ubyte))
            report['first_pixel'] = [int(first[i]) for i in range(4)]
            mesa.OSMesaDestroyContext(context)
        ''')
        assert (report['width'], report['height']) == (64, 48), report
        assert report['format'] == 6408, report
        assert report['same_address'], (
            'OSMesa answered with a different buffer from the one it was '
            'made current with')
        assert report['first_pixel'] == [0, 0, 255, 255], report

    def test_the_depth_buffer_is_reachable_and_described(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContextExt(
                mesa.OSMESA_RGBA, 24, 8, 0, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            glClearDepth(1.0)
            glClear(GL_DEPTH_BUFFER_BIT)
            glFinish()
            width, height, per_value, pointer = mesa.OSMesaGetDepthBuffer(context)
            report['width'] = width
            report['height'] = height
            report['bytes_per_value'] = per_value
            report['have_pointer'] = bool(pointer)
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['have_pointer'], 'no depth buffer came back'
        assert (report['width'], report['height']) == (64, 48), report
        assert report['bytes_per_value'] in (2, 4), report


# -- the two that were declared but never called -----------------------------


class TestColourClamping:
    """``OSMesaColorClamp`` decides whether values outside 0..1 survive."""

    def test_it_can_be_switched_both_ways(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            for enable in (1, 0, 1):
                mesa.OSMesaColorClamp(enable)
            # Still renders afterwards, which is what says the calls landed
            # somewhere harmless rather than upsetting the context.
            glClearColor(1, 0, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT)
            glFinish()
            report['pixel'] = as_image(buffer)[HEIGHT // 2][WIDTH // 2]
            report['gl_error'] = int(glGetError())
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['pixel'] == [255, 0, 0, 255], report
        assert report['gl_error'] == 0, report


class TestPostprocess:
    """``OSMesaPostprocess`` asks the Gallium driver for a filter.

    Its own documentation says it does nothing once a context has been made
    current, and a driver need not offer any filter at all -- so what is held
    here is that the call reaches the library and leaves a usable context,
    not that a filter was applied.
    """

    def test_it_is_callable_before_the_context_is_current(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            mesa.OSMesaPostprocess(context, b'pp_jimenezmlaa', 0)
            buffer = buffer_for()
            report['still_current'] = bool(mesa.OSMesaMakeCurrent(
                context, buffer, GL_UNSIGNED_BYTE, WIDTH, HEIGHT))
            glClearColor(0, 1, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT)
            glFinish()
            report['pixel'] = as_image(buffer)[HEIGHT // 2][WIDTH // 2]
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['still_current'], 'the context would not go current'
        assert report['pixel'] == [0, 255, 0, 255], report


class TestWhenTheQueryHasNothingToAnswerWith:
    """``OSMesaGetColorBuffer`` and ``OSMesaGetDepthBuffer`` can say no.

    Both return a GLboolean and PyOpenGL turns a false one into
    ``(0, 0, 0, None)``, so a caller reads the absence from the pointer rather
    than from an exception.  Worth holding because the failing branch is the
    one a program meets on a context it has not finished setting up, and it is
    a `None` a caller may dereference.
    """

    def test_no_depth_buffer_is_answered_with_none(self):
        report = osmesa('''
            context = mesa.OSMesaCreateContextExt(
                mesa.OSMESA_RGBA, 0, 0, 0, None)
            buffer = buffer_for()
            mesa.OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                   WIDTH, HEIGHT)
            report['depth_bits'] = int(glGetIntegerv(GL_DEPTH_BITS))
            report['answer'] = list(mesa.OSMesaGetDepthBuffer(context)[:3])
            report['pointer_is_none'] = (
                mesa.OSMesaGetDepthBuffer(context)[3] is None)
            glFinish()
            mesa.OSMesaDestroyContext(context)
        ''')
        if report['depth_bits']:
            pytest.skip('this Mesa gave a depth buffer to a 0-bit request')
        assert report['answer'] == [0, 0, 0], report
        assert report['pointer_is_none'], report

    def test_a_colour_buffer_before_make_current_is_answered_with_none(self):
        """The buffer belongs to the make-current, so there is none before."""
        report = osmesa('''
            context = mesa.OSMesaCreateContext(mesa.OSMESA_RGBA, None)
            report['answer'] = list(mesa.OSMesaGetColorBuffer(context)[:3])
            report['pointer_is_none'] = (
                mesa.OSMesaGetColorBuffer(context)[3] is None)
            mesa.OSMesaDestroyContext(context)
        ''')
        assert report['answer'] == [0, 0, 0], report
        assert report['pointer_is_none'], report
