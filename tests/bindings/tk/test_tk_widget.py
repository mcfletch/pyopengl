"""A Tk widget with a GL context of its own, against a real window server.

What the widget promises: importing it does nothing, a context appears when the
window does, ``initgl`` runs once and ``redraw`` runs per frame, the context is
the profile that was asked for, and it goes when the widget does.

The import test runs anywhere; the rest need somewhere to put a window, since a
Tk window is what there is to make a context on.  Which is a different question
on each platform -- ``DISPLAY`` names one only on Linux -- so it is put through
:func:`backends.has_window_server`, and these cases run on Windows against WGL
and on X11 against GLX rather than skipping wherever the variable is unset.

See `plans/TK-WIDGET.md`.
"""

import os
import subprocess
import sys

from arraycompat import one
import paths
import pytest
from backends import has_window_server

pytest.importorskip('tkinter')

needs_display = pytest.mark.skipif(
    not has_window_server(), reason='no window server to open a Tk window on')


def assert_the_old_pipeline_is_there():
    """The current context has fixed function in it, and does not say it is core.

    Not ``GL_CONTEXT_PROFILE_MASK & GL_CONTEXT_COMPATIBILITY_PROFILE_BIT``: a
    context created without profile attributes declares no profile at all, and
    NVIDIA answers 0 there where Mesa answers the compatibility bit.  Both are
    within the specification, so the mask is held only to *not* naming the core
    profile -- which a core context always does name, and which the case above
    asserts of one.

    What a compatibility request is actually asking for is the fixed-function
    pipeline, so that is asked directly: ``glMatrixMode`` exists in no core
    profile, and a driver that has taken it away says so.
    """
    from OpenGL.GL import (
        GL_CONTEXT_CORE_PROFILE_BIT, GL_CONTEXT_PROFILE_MASK, GL_MODELVIEW,
        GL_NO_ERROR, glGetError, glGetIntegerv, glMatrixMode,
    )

    mask = one(glGetIntegerv(GL_CONTEXT_PROFILE_MASK))
    assert not mask & GL_CONTEXT_CORE_PROFILE_BIT, (
        'asked for compatibility and the context says it is core (mask 0x%x)'
        % (mask,)
    )
    while glGetError() != GL_NO_ERROR:
        pass
    glMatrixMode(GL_MODELVIEW)
    assert glGetError() == GL_NO_ERROR, 'glMatrixMode is not available here'


class TestImportingItDoesNothing:
    """It used to create a root window, need a display and load a Tcl package,
    all at import.  A library that opens a window when it is imported cannot be
    imported to ask what it offers."""

    def _run(self, script, environ=None):
        environment = dict(os.environ)
        environment.update(environ or {})
        return subprocess.run([sys.executable, '-c', script],
                              capture_output=True, text=True,
                              env=environment, check=False)

    def test_it_imports_with_no_display(self):
        result = self._run('import OpenGL.Tk; print(OpenGL.Tk.GLFrame)',
                           {'DISPLAY': ''})
        assert result.returncode == 0, result.stderr
        assert 'GLFrame' in result.stdout

    def test_it_makes_no_root_window(self):
        result = self._run(
            'import tkinter, OpenGL.Tk\n'
            'print(tkinter._default_root)\n', {'DISPLAY': ''})
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == 'None'

    def test_it_registers_no_atexit_hook(self):
        """One that destroyed `tkinter._default_root`, whoever made it and
        whatever else was using it."""
        here = paths.ROOT
        for name in ('__init__.py', 'widget.py', 'togl.py'):
            with open(os.path.join(here, 'OpenGL', 'Tk', name),
                      encoding='utf-8') as handle:
                assert 'atexit' not in handle.read(), name

    def test_the_star_import_still_gives_the_tkinter_names(self):
        """`from OpenGL.Tk import *` has always meant tkinter's names too."""
        result = self._run(
            'from OpenGL.Tk import *\n'
            'print(Tk.__name__, Frame.__name__, GLFrame.__name__)\n',
            {'DISPLAY': ''})
        assert result.returncode == 0, result.stderr
        assert result.stdout.split() == ['Tk', 'Frame', 'GLFrame']


@pytest.fixture
def root():
    """A Tk root that is destroyed however the test ends

    Skipped where ``OpenGL.Tk`` has no context implementation for the
    windowing system Tk is using: the widget cannot make a context there, and
    the cases below are about one that has.  What it promises on such a
    platform instead -- a ``TkContextError`` naming what does work -- is
    :class:`TestAWindowingSystemWithNoImplementation`, which runs everywhere.

    Asked of Tk rather than of ``sys.platform``, for the reason the module
    docstring gives: an X11 build of Tk on macOS has X windows and is served.
    """
    import tkinter

    from OpenGL.Tk.context import IMPLEMENTATIONS, windowingSystem

    made = tkinter.Tk()
    made.geometry('200x150')
    system = windowingSystem(made)
    if system not in IMPLEMENTATIONS:
        made.destroy()
        pytest.skip(
            'OpenGL.Tk has no context implementation for Tk on %s; see '
            'plans/TK-WIDGET.md' % (system,)
        )
    try:
        yield made
    finally:
        try:
            made.destroy()
        except tkinter.TclError:
            pass


@pytest.fixture
def scene(root):
    """A mapped GLFrame that counts what it was asked to do"""
    from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor
    from OpenGL.Tk import GLFrame

    class Scene(GLFrame):
        initialised = 0
        drawn = 0

        def initgl(self):
            self.initialised += 1
            glClearColor(0.25, 0.5, 0.75, 1.0)

        def redraw(self):
            self.drawn += 1
            glClear(GL_COLOR_BUFFER_BIT)

    made = Scene(root, width=160, height=120)
    made.pack(fill='both', expand=True)
    made.waitForMap()
    return made


class TestAWindowingSystemWithNoImplementation:
    """What a platform `OpenGL.Tk` does not serve is promised instead.

    Aqua is the one: a context is attached to an NSView there, through
    Objective-C, rather than made against a window id, and `plans/TK-WIDGET.md`
    has it as still to land.  So the promise is a `TkContextError` that says
    so and names what does work -- not a `NullFunctionError` from somewhere
    inside a context that was never made.

    Asked with a stub rather than on Aqua, so the promise is held to from
    wherever the suite runs; `tk windowingsystem` is the whole of what
    `createContext` reads to decide.
    """

    class Widget:
        """As much of a Tk widget as choosing an implementation reads."""

        def __init__(self, system):
            self.system = system
            self.tk = self

        def call(self, *arguments):
            assert arguments == ('tk', 'windowingsystem'), arguments
            return self.system

    def test_aqua_says_so_and_says_what_does_work(self):
        from OpenGL.Tk.context import createContext
        from OpenGL.Tk.errors import TkContextError

        with pytest.raises(TkContextError) as raised:
            createContext(self.Widget('aqua'))
        message = str(raised.value)
        assert 'Aqua' in message, message
        # The two that do serve it, so the reader has somewhere to go.
        assert 'togl' in message.lower() and 'pyopengltk' in message, message

    def test_and_so_does_one_nobody_has_heard_of(self):
        """A Tk built for something neither this nor the message knows."""
        from OpenGL.Tk.context import createContext
        from OpenGL.Tk.errors import TkContextError

        with pytest.raises(TkContextError) as raised:
            createContext(self.Widget('haiku'))
        assert 'haiku' in str(raised.value), raised.value


@needs_display
class TestTheContext:
    def test_a_mapped_widget_has_one(self, scene):
        assert scene.context is not None

    def test_it_is_the_profile_that_was_asked_for(self, scene):
        from OpenGL.GL import (
            GL_CONTEXT_CORE_PROFILE_BIT, GL_CONTEXT_PROFILE_MASK,
            glGetIntegerv,
        )

        scene.makeCurrent()
        assert one(glGetIntegerv(GL_CONTEXT_PROFILE_MASK)) \
            & GL_CONTEXT_CORE_PROFILE_BIT

    def test_a_compatibility_request_gets_the_old_pipeline(self, root):
        """Which is what the fixed-function widgets need."""
        from OpenGL.Tk import GLFrame

        made = GLFrame(root, width=64, height=64, profile='compatibility',
                       version=None)
        made.pack()
        made.waitForMap()
        made.makeCurrent()
        assert_the_old_pipeline_is_there()

    def test_a_version_the_driver_has_is_given(self, root):
        from OpenGL.GL import GL_MAJOR_VERSION, glGetIntegerv
        from OpenGL.Tk import GLFrame

        made = GLFrame(root, width=64, height=64, version=(3, 3))
        made.pack()
        made.waitForMap()
        made.makeCurrent()
        assert one(glGetIntegerv(GL_MAJOR_VERSION)) >= 3

    def test_an_impossible_request_is_an_error_rather_than_an_exit(self, root):
        """Xlib's default error handler prints and calls exit(); a library
        that leaves it in place ends the application instead of answering."""
        from OpenGL.Tk import GLFrame, TkContextError

        made = GLFrame(root, width=64, height=64, version=(9, 9))
        made.pack()
        with pytest.raises(TkContextError):
            made.waitForMap()

    def test_the_widget_still_works_after_a_refused_request(self, root):
        """A frame is a frame; only the GL half failed."""
        from OpenGL.Tk import GLFrame, TkContextError

        made = GLFrame(root, width=64, height=64, version=(9, 9))
        made.pack()
        with pytest.raises(TkContextError):
            made.waitForMap()
        assert made.winfo_exists()
        assert made.makeCurrent.__self__ is made


@needs_display
class TestDrawing:
    def test_initgl_runs_once(self, scene):
        scene.render()
        scene.render()
        assert scene.initialised == 1

    def test_redraw_runs_per_frame(self, scene):
        before = scene.drawn
        scene.render()
        assert scene.drawn == before + 1

    def test_what_was_drawn_is_in_the_buffer(self, scene):
        """The clear colour the fixture set, read back while it is still there.

        Read after ``render()`` instead, this would be asking for something no
        driver promises: ``render`` ends in ``swapBuffers``, and what a swap
        leaves in the back buffer is undefined.  A driver that flips rather
        than copies leaves whatever was on screen -- here, zeros on the first
        frame and the frame before on every one after, which is the same colour
        and so reads as a pass for the wrong reason.  So the frame is drawn the
        way ``render`` draws it and read before the swap.

        Within one count per channel, because the conversion from float to
        eight bits is the implementation's: 0.5 is 127.5 of 255, exactly
        between two values, and Mesa rounds it up where NVIDIA rounds it down.
        A driver is required to be near, not exact -- so asking for exact is
        asking one driver's arithmetic of every driver.
        """
        from OpenGL.GL import GL_RGB, GL_UNSIGNED_BYTE, glReadPixels

        assert scene.makeCurrent(), 'the widget is mapped, so it has a context'
        scene.redraw()
        pixel = list(bytes(glReadPixels(2, 2, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)))
        assert len(pixel) == 3, pixel
        for channel, (found, wanted) in enumerate(zip(pixel, (64, 128, 191))):
            assert abs(found - wanted) <= 1, (
                'channel %d read back %d, not %d' % (channel, found, wanted)
            )

    def test_a_resize_does_not_run_initgl_again(self, scene):
        """It would rebuild every texture and shader each time somebody
        dragged a corner."""
        scene.configure(width=200, height=100)
        scene.update()
        assert scene.initialised == 1

    def test_a_resize_follows_with_the_viewport(self, root):
        from OpenGL.GL import GL_VIEWPORT, glGetIntegerv
        from OpenGL.Tk import GLFrame

        made = GLFrame(root, width=64, height=64)
        made.pack()                     # packed to its own size, not the root's
        made.waitForMap()
        made.configure(width=120, height=90)
        made.update()
        made.makeCurrent()
        assert [int(value) for value in glGetIntegerv(GL_VIEWPORT)][2:] == [120, 90]

    def test_rendering_before_the_window_exists_says_so(self, root):
        from OpenGL.Tk import GLFrame

        made = GLFrame(root, width=64, height=64)
        assert made.render() is False


@needs_display
class TestTheContextsLife:
    def test_destroying_the_widget_takes_the_context(self, scene):
        scene.destroy()
        scene.update()
        assert scene.context is None

    def test_letting_it_go_twice_is_letting_it_go_once(self, scene):
        scene.destroyContext()
        scene.destroyContext()
        assert scene.context is None

    def test_a_second_widget_gets_a_context_of_its_own(self, root, scene):
        from OpenGL.Tk import GLFrame

        other = GLFrame(root, width=64, height=64)
        other.pack()
        other.waitForMap()
        assert other.context is not scene.context
        assert other.context.handle != scene.context.handle


@needs_display
class TestTheAnimation:
    def _pump(self, scene, passes=10):
        """Let Tk's timers come due; `after` with no callback is its sleep"""
        for _ in range(passes):
            scene.after(5)
            scene.update()

    def test_it_renders_without_being_asked(self, scene):
        before = scene.drawn
        scene.startAnimation(1)
        try:
            self._pump(scene)
        finally:
            scene.stopAnimation()
        assert scene.drawn > before

    def test_stopping_it_stops_the_rendering(self, scene):
        scene.startAnimation(1)
        self._pump(scene, 2)
        scene.stopAnimation()
        self._pump(scene, 2)
        settled = scene.drawn
        self._pump(scene)
        assert scene.drawn == settled


@needs_display
class TestTheOldWidgets:
    """`RawOpengl` and `Opengl` keep working, and no longer need Togl."""

    def test_the_examination_widget_renders(self, root):
        from OpenGL.Tk import Opengl

        drawn = []
        made = Opengl(root, width=120, height=90, double=1)
        made.redraw = lambda widget: drawn.append(widget)
        made.pack()
        made.waitForMap()
        made.render()
        assert drawn, 'the widget never called its redraw'

    def test_rendering_puts_the_matrix_mode_back(self, root):
        """And does not raise doing it.

        The mode is an enum, and it was read with the double getter -- which
        answers 5888.0, a float the enum parameter refuses.  That came out of
        the finally that restores it, and the buffers are swapped after that
        block, so the frame was lost with it.  A Tk callback prints such an
        exception and carries on, which is why nothing here noticed.
        """
        from OpenGL.GL import GL_MATRIX_MODE, glGetIntegerv
        from OpenGL.Tk import RawOpengl

        # RawOpengl's render is the one that saves and restores the mode;
        # Opengl overrides it with its own.
        made = RawOpengl(root, width=120, height=90, double=1)
        made.pack()
        made.waitForMap()
        made.makeCurrent()
        before = one(glGetIntegerv(GL_MATRIX_MODE))
        made.render()
        made.makeCurrent()
        assert one(glGetIntegerv(GL_MATRIX_MODE)) == before

    def test_it_gets_a_compatibility_context(self, root):
        """It draws with glMatrixMode and gluPerspective, so it needs them."""
        from OpenGL.Tk import RawOpengl

        made = RawOpengl(root, width=64, height=64)
        made.pack()
        made.waitForMap()
        made.makeCurrent()
        assert_the_old_pipeline_is_there()

    def test_it_needs_no_togl(self, root):
        """Which is the whole point: Togl is a Tcl extension nobody has."""
        from OpenGL.Tk import RawOpengl

        made = RawOpengl(root, width=64, height=64)
        made.pack()
        made.waitForMap()
        assert made.context is not None
        assert 'Togl' not in root.tk.call('info', 'commands')

    @pytest.mark.parametrize('options, wanted', [
        ({'double': 1}, ('doubleBuffer', True)),
        ({'double': 0}, ('doubleBuffer', False)),
        ({'depth': 1}, ('depthSize', 24)),
        ({'depth': 0}, ('depthSize', 0)),
        ({'depthsize': 16}, ('depthSize', 16)),
        ({'stencil': 1}, ('stencilSize', 8)),
        ({'alpha': 1}, ('alphaSize', 8)),
        ({'stereo': 1}, ('stereo', True)),
    ])
    def test_the_togl_options_still_mean_what_they_meant(self, options, wanted):
        """`Opengl(master, double=1, depth=1)` is the idiom in every example
        this package has ever shipped."""
        from OpenGL.Tk.togl import attributesFromToglOptions

        attributes, remaining, _ = attributesFromToglOptions(options)
        assert getattr(attributes, wanted[0]) == wanted[1]
        assert remaining == {}

    def test_a_tk_option_is_left_for_tk(self):
        from OpenGL.Tk.togl import attributesFromToglOptions

        remaining = attributesFromToglOptions(
            {'width': 120, 'double': 1, 'cursor': 'crosshair'})[1]
        assert remaining == {'width': 120, 'cursor': 'crosshair'}

    def test_an_option_with_nothing_behind_it_is_ignored_not_refused(self):
        """`privatecmap` and friends describe a choice a context made through
        the window system does not have."""
        from OpenGL.Tk.togl import attributesFromToglOptions

        remaining = attributesFromToglOptions(
            {'privatecmap': 0, 'rgba': 1, 'accum': 1, 'ident': 'view'})[1]
        assert remaining == {}

    def test_togls_timer_becomes_the_animation_interval(self):
        from OpenGL.Tk.togl import attributesFromToglOptions

        _, remaining, animate = attributesFromToglOptions({'time': 20})
        assert animate == 20
        assert remaining == {}
