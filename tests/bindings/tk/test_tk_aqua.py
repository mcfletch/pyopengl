"""What the Aqua context decides, and what it does on a Mac.

Everything the context *decides* is a plain function of plain values, so the
first classes run anywhere: which CGL profile a request becomes, where the view
goes over the widget, which window is the toplevel's, and how a message is
sent.  The last class needs Tk on Aqua and a window server, and is skipped
everywhere else saying so.

See `plans/TK-WIDGET.md`.
"""

import ctypes
import sys

import pytest

from OpenGL.Tk import aqua, cocoa
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.errors import TkContextError


class TestWhichProfileARequestBecomes:
    @pytest.mark.parametrize('version', [(3, 2), (3, 3), (4, 0)])
    def test_a_core_request_below_four_one_is_the_3_2_profile(self, version):
        assert aqua.cglProfile(
            ContextAttributes(profile='core', version=version)) == 'core3'

    def test_four_one_is_the_gl4_profile(self):
        assert aqua.cglProfile(
            ContextAttributes(profile='core', version=(4, 1))) == 'core4'

    def test_the_default_request_is_a_core_one(self):
        assert aqua.cglProfile(ContextAttributes()) == 'core3'

    @pytest.mark.parametrize('profile', ['legacy', 'compatibility'])
    def test_fixed_function_is_the_legacy_profile(self, profile):
        assert aqua.cglProfile(
            ContextAttributes(profile=profile, version=None)) == 'legacy'

    def test_a_core_request_for_two_one_is_a_plain_two_one(self):
        """`ContextAttributes.profileApplies`: every toolkit gives that."""
        assert aqua.cglProfile(
            ContextAttributes(profile='core', version=(2, 1))) == 'legacy'

    def test_a_version_macos_does_not_have_is_refused_by_number(self):
        with pytest.raises(TkContextError) as raised:
            aqua.cglProfile(ContextAttributes(profile='core', version=(4, 6)))
        assert '4.1' in str(raised.value) and '4.6' in str(raised.value)

    def test_nothing_is_asked_of_the_driver_for_version_nine(self):
        with pytest.raises(TkContextError):
            aqua.cglProfile(ContextAttributes(version=(9, 9)))

    def test_a_compatibility_profile_above_two_one_says_what_to_ask_for(self):
        """`GLFrame(profile='compatibility')` is 3.3 by default, and a person
        writing fixed-function code on a Mac needs to be told the way out."""
        with pytest.raises(TkContextError) as raised:
            aqua.cglProfile(ContextAttributes(profile='compatibility'))
        message = str(raised.value)
        assert 'compatibility' in message, message
        assert 'legacy' in message and 'version=None' in message, message


class TestTheSizesAskedOf:
    def test_the_three_channels_count_as_one_size(self):
        sizes = aqua.pixelFormatSizes(
            ContextAttributes(redSize=8, greenSize=8, blueSize=8))
        assert sizes['color_size'] == 24

    def test_the_rest_are_passed_through(self):
        sizes = aqua.pixelFormatSizes(ContextAttributes(
            alphaSize=8, depthSize=16, stencilSize=8, samples=4,
            doubleBuffer=False, stereo=True))
        assert (sizes['alpha_size'], sizes['depth_size'],
                sizes['stencil_size'], sizes['samples']) == (8, 16, 8, 4)
        assert sizes['double_buffer'] is False and sizes['stereo'] is True

    def test_they_are_what_cgl_builds_an_attribute_list_from(self):
        """So a name here that CGL does not take is found without a Mac."""
        from OpenGL import CGL

        listed = CGL.pixel_format_attributes(
            profile='core3', **aqua.pixelFormatSizes(ContextAttributes()))
        assert listed[-1] == 0
        assert CGL.kCGLPFADoubleBuffer in listed


class TestTheSwapIntervalOnAqua:
    """Windowed contexts are composited and synchronised to the display by the
    window server, and an interval of one on top of that waits for a refresh
    that a machine without a display never delivers.  So the interval is zero
    unless the request names one."""

    def test_the_default_is_not_to_wait(self):
        assert aqua.swapIntervalFor(ContextAttributes()) == 0

    @pytest.mark.parametrize('interval', [0, 1, 2])
    def test_a_request_outranks_the_default(self, interval):
        assert aqua.swapIntervalFor(
            ContextAttributes(swapInterval=interval)) == interval


class TestWhereTheViewGoes:
    class Widget:
        def __init__(self, x, y, master=None):
            self._x, self._y, self.master = x, y, master

        def winfo_x(self):
            return self._x

        def winfo_y(self):
            return self._y

    def test_the_offsets_of_every_parent_up_to_the_toplevel_are_added(self):
        top = self.Widget(999, 999)          # its own place is not in itself
        frame = self.Widget(10, 20, top)
        glframe = self.Widget(5, 7, frame)
        assert aqua.widgetOffset(glframe, top) == (15, 27)

    def test_a_widget_that_is_the_toplevel_has_none(self):
        top = self.Widget(30, 40)
        assert aqua.widgetOffset(top, top) == (0, 0)

    def test_a_flipped_host_counts_down_as_tk_does(self):
        assert aqua.viewFrame((10, 20), (100, 50), 400, True) \
            == (10.0, 20.0, 100.0, 50.0)

    def test_an_ordinary_host_counts_up_from_the_bottom(self):
        """A widget 20 down and 50 high in a 400-high window has its lower edge
        330 up from the bottom."""
        assert aqua.viewFrame((10, 20), (100, 50), 400, False) \
            == (10.0, 330.0, 100.0, 50.0)

    def test_a_widget_that_fills_the_host_fills_it_either_way(self):
        assert aqua.viewFrame((0, 0), (200, 400), 400, False) \
            == aqua.viewFrame((0, 0), (200, 400), 400, True) \
            == (0.0, 0.0, 200.0, 400.0)


class TestWhichWindowIsTheToplevel:
    def test_the_only_window_is_taken_without_asking(self):
        def never(candidate):
            raise AssertionError('asked about %r' % (candidate,))

        assert aqua.chooseWindow(['only'], never) == 'only'

    def test_with_several_the_one_that_matches_is(self):
        assert aqua.chooseWindow(['a', 'b', 'c'], lambda w: w == 'b') == 'b'

    def test_with_several_and_none_matching_there_is_no_answer(self):
        assert aqua.chooseWindow(['a', 'b'], lambda w: False) is None

    def test_with_several_matching_there_is_no_answer(self):
        """Taking the first would draw into somebody else's window."""
        assert aqua.chooseWindow(['a', 'b'], lambda w: True) is None

    def test_with_none_there_is_no_answer(self):
        assert aqua.chooseWindow([], lambda w: True) is None


class FakeObjc:
    """Stands in for libobjc with a message sender of this process's own

    `objc_msgSend` is a function taking (receiver, selector, ...) whose real
    signature the caller supplies, so a ctypes callback of the shape the test
    expects is a faithful stand-in, and what `Runtime.send` builds a prototype
    of is exercised for real.
    """

    class Function:
        def __init__(self, behaviour):
            self.behaviour = behaviour
            self.argtypes = self.restype = None

        def __call__(self, *arguments):
            return self.behaviour(*arguments)

    def __init__(self, msgSend):
        self.names = {}
        self.objc_msgSend = msgSend
        self.objc_getClass = self.Function(lambda name: 0x1000)
        self.sel_registerName = self.Function(self.register)
        for name in ('object_getClass', 'class_getName',
                     'class_respondsToSelector', 'objc_autoreleasePoolPush',
                     'objc_autoreleasePoolPop'):
            setattr(self, name, self.Function(lambda *a: 0))

    def register(self, name):
        return self.names.setdefault(name, 0x2000 + len(self.names))


class TestSendingAMessage:
    def runtime(self, callback_type, behaviour):
        self.callback = callback_type(behaviour)       # kept alive by the test
        return cocoa.Runtime(FakeObjc(self.callback))

    def test_the_receiver_the_selector_and_the_arguments_arrive_in_order(self):
        seen = []

        def msgSend(receiver, selector, first, second):
            seen.append((receiver, selector, first, second))
            return 0

        rt = self.runtime(
            ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_long, ctypes.c_double),
            msgSend)
        rt.send(0x10, 'setThing:other:', 7, 2.5,
                argtypes=(ctypes.c_long, ctypes.c_double))
        assert seen == [(0x10, rt.selector('setThing:other:'), 7, 2.5)]

    def test_an_object_comes_back_as_an_integer_and_nil_as_none(self):
        answers = iter([0x4000, 0])
        rt = self.runtime(
            ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p),
            lambda receiver, selector: next(answers))
        assert rt.send(1, 'thing') == 0x4000
        assert rt.send(1, 'thing') is None

    def test_a_struct_goes_by_value(self):
        seen = []

        def msgSend(receiver, selector, rect):
            seen.append((rect.x, rect.y, rect.width, rect.height))

        rt = self.runtime(
            ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                             cocoa.CGRect),
            msgSend)
        rt.send(1, 'setFrame:', cocoa.CGRect(1, 2, 3, 4),
                argtypes=(cocoa.CGRect,), restype=None)
        assert seen == [(1.0, 2.0, 3.0, 4.0)]

    def test_a_message_and_its_types_have_to_agree_in_number(self):
        rt = self.runtime(
            ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p),
            lambda receiver, selector: None)
        with pytest.raises(TypeError, match='setThing:'):
            rt.send(1, 'setThing:', 5, restype=None)

    def test_a_selector_is_registered_once(self):
        rt = self.runtime(
            ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p),
            lambda receiver, selector: None)
        assert rt.selector('thing') == rt.selector('thing')
        assert len(rt._objc.names) == 1

    def test_a_class_nobody_loaded_is_an_error_naming_it(self):
        rt = self.runtime(
            ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p),
            lambda receiver, selector: None)
        rt._objc.objc_getClass = FakeObjc.Function(lambda name: 0)
        with pytest.raises(cocoa.CocoaError, match='NSNothing'):
            rt.cls('NSNothing')


@pytest.mark.skipif(sys.platform == 'darwin',
                    reason='this is the answer where there is no Mac')
def test_the_runtime_says_where_it_is_not_available():
    with pytest.raises(cocoa.CocoaError, match='macOS'):
        cocoa.runtime()


# ---------------------------------------------------------------------------
# On a Mac
# ---------------------------------------------------------------------------

def _aqua_root():
    """A Tk root on Aqua, or a skip saying why there is not one"""
    import tkinter

    from OpenGL.Tk.context import windowingSystem
    from backends import has_window_server

    if sys.platform != 'darwin':
        pytest.skip('Tk on Aqua is a macOS thing')
    if not has_window_server():
        pytest.skip('no window server to open a Tk window on')
    try:
        made = tkinter.Tk()
    except tkinter.TclError as error:
        pytest.skip('Tk could not open a window here: %s' % (error,))
    if windowingSystem(made) != 'aqua':
        made.destroy()
        pytest.skip('this Tk is not the Aqua one')
    made.geometry('300x200')
    return made


@pytest.fixture
def mac():
    import gc
    import tkinter

    made = _aqua_root()
    try:
        yield made
    finally:
        try:
            made.destroy()
        except tkinter.TclError:
            pass
        del made
        gc.collect()


def _glframe(master, **options):
    from OpenGL.Tk import GLFrame

    made = GLFrame(master, width=120, height=90, **options)
    made.pack()
    made.waitForMap()
    return made


class TestOnAqua:
    def test_the_context_is_an_aqua_one(self, mac):
        made = _glframe(mac)
        assert isinstance(made.context, aqua.AquaContext)

    def test_it_says_which_renderer_and_profile_it_got(self, mac):
        context = _glframe(mac).context
        assert context.renderer in ('accelerated', 'any', 'software')
        assert context.profile == 'core3'
        assert context.describe()

    def test_the_view_is_in_the_toplevels_content_view(self, mac):
        context = _glframe(mac).context
        objc = context.objc
        assert objc.send(context._view, 'superview') == context._host

    def test_the_host_is_the_content_view_of_a_window_with_a_title(self, mac):
        """Found by the toplevel's title, so a second toplevel has its own."""
        first = _glframe(mac)
        import tkinter

        other = tkinter.Toplevel(mac)
        other.geometry('200x150')
        try:
            second = _glframe(other)
            assert first.context._host != second.context._host
        finally:
            other.destroy()

    def test_the_title_is_put_back(self, mac):
        mac.title('kept')
        _glframe(mac)
        assert mac.title() == 'kept'

    def test_an_unmapped_widget_hides_its_view(self, mac):
        made = _glframe(mac)
        context = made.context
        made.pack_forget()
        mac.update()
        assert context.objc.send(context._view, 'isHidden',
                                 restype=cocoa.BOOL) == 1
        made.pack()
        mac.update()
        assert context.objc.send(context._view, 'isHidden',
                                 restype=cocoa.BOOL) == 0

    def test_what_is_drawn_reads_back(self, mac):
        from OpenGL.GL import (
            GL_COLOR_BUFFER_BIT, GL_RGB, GL_UNSIGNED_BYTE, glClear,
            glClearColor, glReadPixels,
        )

        made = _glframe(mac)
        assert made.makeCurrent()
        glClearColor(1.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        pixel = list(bytes(glReadPixels(2, 2, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)))
        assert pixel[0] > 250 and pixel[1] < 5 and pixel[2] < 5, pixel

    def test_the_swap_interval_can_be_set(self, mac):
        assert _glframe(mac).setSwapInterval(0) in (True, False)

    def test_the_legacy_context_has_the_old_pipeline(self, mac):
        from OpenGL.GL import GL_MODELVIEW, GL_NO_ERROR, glGetError, glMatrixMode

        made = _glframe(mac, profile='legacy')
        assert made.context.profile == 'legacy'
        made.makeCurrent()
        while glGetError() != GL_NO_ERROR:
            pass
        glMatrixMode(GL_MODELVIEW)
        assert glGetError() == GL_NO_ERROR

    def test_destroying_the_widget_removes_the_view(self, mac):
        made = _glframe(mac)
        context = made.context
        objc, host = context.objc, context._host
        before = len(objc.items(objc.send(host, 'subviews')))
        made.destroy()
        mac.update()
        assert len(objc.items(objc.send(host, 'subviews'))) == before - 1
        assert context.handle is None
