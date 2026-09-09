"""The Togl widget, and the examination widgets built on it.

**Togl is a Tcl C extension that has to be installed separately** -- Debian
calls it ``libtogl2`` -- and it is the only thing in this package that needs
anything outside Python.  :class:`~OpenGL.Tk.widget.GLFrame` needs none of it;
this is here for code that already used :class:`Togl` directly, and it loads
Togl the first time :func:`loadTogl` is called rather than when the module is
imported.

:class:`RawOpengl` and :class:`Opengl` keep their names, their constructors and
their methods, and no longer need Togl at all: they are ``GLFrame`` subclasses
now.  Both draw with the fixed-function pipeline -- ``glMatrixMode``,
``gluPerspective``, ``glLightfv`` -- so both ask for a compatibility profile,
which is what those calls need.
"""

from __future__ import annotations

import logging
import math
import os
import sys
import tkinter
from tkinter import Misc, TclError, Widget

from OpenGL.GL import (
    GL_COLOR, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_LESS,
    GL_LIGHT0, GL_LIGHTING, GL_MATRIX_MODE, GL_MODELVIEW, GL_MODELVIEW_MATRIX,
    GL_POSITION, GL_PROJECTION, GL_TEXTURE, glClear, glClearColor, glDepthFunc,
    glEnable,
    glFlush, glGetDoublev, glGetIntegerv, glLightfv, glLoadIdentity,
    glMatrixMode,
    glMultMatrixd, glPopMatrix, glPushMatrix, glRotatef, glTranslatef,
    glViewport,
)
from OpenGL.GLU import gluLookAt, gluPerspective, gluProject, gluUnProject
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.widget import GLFrame
from OpenGL._scalar import as_int

log = logging.getLogger(__name__)

#: Every value ``GL_MATRIX_MODE`` can answer.  A read that comes back with
#: something else did not reach a context: ``glGetIntegerv`` leaves its output
#: untouched and answers 0 when none is current, and 0 is not a mode.  Putting
#: that back raises out of the ``finally`` in :meth:`RawOpengl.render`, after
#: the frame is drawn and before it is swapped, so the frame goes with it.
MATRIX_MODES = frozenset((GL_MODELVIEW, GL_PROJECTION, GL_TEXTURE, GL_COLOR))

__all__ = [
    'TOGL_NORMAL', 'TOGL_OPTIONS', 'TOGL_OVERLAY', 'Opengl', 'RawOpengl',
    'Togl', 'attributesFromToglOptions', 'glDistFromLine', 'glRotateScene',
    'glTranslateScene', 'loadTogl', 'toglLibraryPath',
]

# Keith Junius <junius@chem.rug.nl> provided many changes to Togl
TOGL_NORMAL = 1
TOGL_OVERLAY = 2

#: What the fixed-function widgets below ask their context for.  Everything
#: they draw with was removed in the core profile.
LEGACY_ATTRIBUTES = dict(profile='compatibility', version=None, depthSize=24)

#: Togl's own widget options, and what each says about the context.  A script
#: written for the Togl widget says ``Opengl(master, double=1, depth=1)``, and
#: that is the idiom in every example this package has ever shipped, so the
#: names go on meaning what they meant.  A value is either the attribute the
#: option sets, or a ``(attribute, value-when-true)`` pair for the ones Togl
#: spells as a flag where a size is what is wanted.
TOGL_OPTIONS = {
    'double': 'doubleBuffer',
    'depth': ('depthSize', 24),
    'depthsize': 'depthSize',
    'stencil': ('stencilSize', 8),
    'stencilsize': 'stencilSize',
    'alpha': ('alphaSize', 8),
    'alphasize': 'alphaSize',
    'redsize': 'redSize',
    'greensize': 'greenSize',
    'bluesize': 'blueSize',
    'stereo': 'stereo',
}

#: Togl options that describe something a context made this way does not have,
#: or that Tk itself settles.  Accepted and ignored, with a line in the log,
#: rather than refused: a script that says ``privatecmap=0`` is asking for what
#: it already gets.
TOGL_OPTIONS_IGNORED = (
    'accum', 'accumredsize', 'accumgreensize', 'accumbluesize',
    'accumalphasize', 'auxbuffers', 'ident', 'indirect', 'overlay',
    'pixelformat', 'privatecmap', 'rgba', 'sharecontext', 'sharelist',
)


def attributesFromToglOptions(options):
    """Split Togl's widget options out of a widget's keyword arguments

    Answers ``(attributes, remaining, animate)``: the context to ask for, the
    options that are Tk's to deal with, and the animation interval Togl spells
    ``time``.  ``options`` is left alone.

    Nothing here touches Tk or a display, so what a given call amounts to can
    be looked at without one.
    """
    remaining = dict(options)
    asked = dict(LEGACY_ATTRIBUTES)
    for name in list(remaining):
        if name in ContextAttributes.KEYWORDS:
            asked[name] = remaining.pop(name)
            continue
        translation = TOGL_OPTIONS.get(name)
        if translation is not None:
            value = remaining.pop(name)
            if isinstance(translation, tuple):
                attribute, whenTrue = translation
                asked[attribute] = whenTrue if value else 0
            else:
                asked[translation] = value
        elif name in TOGL_OPTIONS_IGNORED:
            log.debug('ignoring the Togl option %s=%r: a context made through '
                      'the window system has no such choice to make',
                      name, remaining.pop(name))
    animate = int(remaining.pop('time', 0) or 0)
    return ContextAttributes(**asked), remaining, animate


def glTranslateScene(s, x, y, mousex, mousey):
    glMatrixMode(GL_MODELVIEW)
    mat = glGetDoublev(GL_MODELVIEW_MATRIX)
    glLoadIdentity()
    glTranslatef(s * (x - mousex), s * (mousey - y), 0.0)
    glMultMatrixd(mat)


def glRotateScene(s, xcenter, ycenter, zcenter, x, y, mousex, mousey):
    glMatrixMode(GL_MODELVIEW)
    mat = glGetDoublev(GL_MODELVIEW_MATRIX)
    glLoadIdentity()
    glTranslatef(xcenter, ycenter, zcenter)
    glRotatef(s * (y - mousey), 1., 0., 0.)
    glRotatef(s * (x - mousex), 0., 1., 0.)
    glTranslatef(-xcenter, -ycenter, -zcenter)
    glMultMatrixd(mat)


def sub(x, y):
    return list(map(lambda a, b: a - b, x, y))


def dot(x, y):
    t = 0
    for i in range(len(x)):
        t = t + x[i] * y[i]
    return t


def glDistFromLine(x, p1, p2):
    f = list(map(lambda x, y: x - y, p2, p1))
    g = list(map(lambda x, y: x - y, x, p1))
    return dot(g, g) - dot(f, g) ** 2 / dot(f, f)


def v3distsq(a, b):
    d = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    return d[0] * d[0] + d[1] * d[1] + d[2] * d[2]


def toglLibraryPath():
    """Where a Togl built for this interpreter would be, in this package

    ``src/togl.py`` in the source distribution downloads a binary Togl into it.
    Togl 2.0 and above use Tcl stubs, so the Tk version does not matter, but a
    64-bit Python needs a 64-bit build -- hence the suffix.
    """
    suffix = '-64' if sys.maxsize > 2 ** 32 else ''
    try:
        return os.path.join(os.path.dirname(__file__),
                            'togl-' + sys.platform + suffix)
    except NameError:                   # pragma: no cover - no __file__
        return ''


def loadTogl(master=None):
    """Load the Togl Tcl package into ``master``'s interpreter

    Answers the interpreter it was loaded into.  Raises ``TclError`` where
    Togl is not installed, saying which package provides it.

    Called on demand -- by :class:`Togl` -- rather than when this module is
    imported, so that importing :mod:`OpenGL.Tk` neither needs a display nor
    needs Togl.
    """
    if master is None:
        master = tkinter._default_root
    if master is None:
        master = tkinter.Tk()
    path = toglLibraryPath()
    if path and os.path.isdir(path):
        master.tk.call('lappend', 'auto_path', path)
    else:
        log.debug('no bundled Togl in %s; relying on the system one', path)
    try:
        master.tk.call('package', 'require', 'Togl')
        master.tk.eval('load {} Togl')
    except TclError as err:
        raise TclError(
            'Could not load the Togl Tcl package (%s). On Debian and Ubuntu '
            'it is `libtogl2`. OpenGL.Tk.GLFrame needs no Tcl extension and '
            'is what to use instead.' % (err,)
        ) from err
    return master


class Togl(Widget):
    """
    Togl Widget
    Keith Junius
    Department of Biophysical Chemistry
    University of Groningen, The Netherlands
    Very basic widget which provides access to Togl functions.

    Needs the Togl Tcl extension, which :func:`loadTogl` loads the first time
    one of these is made.  :class:`~OpenGL.Tk.widget.GLFrame` is the widget
    that needs nothing outside Python.
    """

    def __init__(self, master=None, cnf=None, **kw):
        # `None` rather than `{}`: a mutable default is one object shared
        # by every widget that does not pass its own.
        cnf = {} if cnf is None else cnf
        loadTogl(master or tkinter._default_root)
        Widget.__init__(self, master, 'togl', cnf, kw)

    def render(self):
        return

    def swapbuffers(self):
        self.tk.call(self._w, 'swapbuffers')

    def makecurrent(self):
        self.tk.call(self._w, 'makecurrent')

    def alloccolor(self, red, green, blue):
        return self.tk.getint(self.tk.call(self._w, 'alloccolor', red, green, blue))

    def freecolor(self, index):
        self.tk.call(self._w, 'freecolor', index)

    def setcolor(self, index, red, green, blue):
        self.tk.call(self._w, 'setcolor', index, red, green, blue)

    def loadbitmapfont(self, fontname):
        return self.tk.getint(self.tk.call(self._w, 'loadbitmapfont', fontname))

    def unloadbitmapfont(self, fontbase):
        self.tk.call(self._w, 'unloadbitmapfont', fontbase)

    def uselayer(self, layer):
        self.tk.call(self._w, 'uselayer', layer)

    def showoverlay(self):
        self.tk.call(self._w, 'showoverlay')

    def hideoverlay(self):
        self.tk.call(self._w, 'hideoverlay')

    def existsoverlay(self):
        return self.tk.getboolean(self.tk.call(self._w, 'existsoverlay'))

    def getoverlaytransparentvalue(self):
        return self.tk.getint(self.tk.call(self._w, 'getoverlaytransparentvalue'))

    def ismappedoverlay(self):
        return self.tk.getboolean(self.tk.call(self._w, 'ismappedoverlay'))

    def alloccoloroverlay(self, red, green, blue):
        return self.tk.getint(self.tk.call(self._w, 'alloccoloroverlay', red, green, blue))

    def freecoloroverlay(self, index):
        self.tk.call(self._w, 'freecoloroverlay', index)


class RawOpengl(GLFrame, Misc):
    """Widget without any sophisticated bindings by Tom Schwaller

    A :class:`~OpenGL.Tk.widget.GLFrame` that protects the projection matrix
    around each frame, which is what its subclasses expect.  The context is a
    compatibility profile, since there is a matrix stack in that sentence.
    """

    def __init__(self, master=None, cnf=None, **kw):
        # `None` rather than `{}`: a mutable default is one object shared
        # by every widget that does not pass its own.
        cnf = {} if cnf is None else cnf
        merged = dict(cnf or {})
        merged.update(kw)
        attributes, options, animate = attributesFromToglOptions(merged)
        GLFrame.__init__(self, master, attributes=attributes, **options)
        if animate:
            self.animate = animate

    def render(self):
        """Draw one frame with the projection matrix left as it was found"""
        # Tk settles first, and the context is taken after it. Pending idle
        # work maps and resizes widgets, and doing that for a *sibling* widget
        # makes the sibling's context current -- so a `makeCurrent` before this
        # line no longer holds after it, and the state read below then comes
        # back zero. `glMatrixMode(0)` out of the `finally` is what that looks
        # like, and only in a process where a second widget exists.
        self.update_idletasks()
        if not self.makeCurrent():
            return False
        # An enum, so the integer getter: the double one answers 5888.0,
        # and restoring the mode with a float is a ctypes.ArgumentError
        # out of the finally below -- which loses the frame, since the
        # buffers are swapped after it.
        mode = as_int(glGetIntegerv(GL_MATRIX_MODE))
        try:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            try:
                self.redraw()
                glFlush()
            finally:
                glPopMatrix()
        finally:
            if mode in MATRIX_MODES:
                glMatrixMode(mode)
            else:
                log.debug(
                    'GL_MATRIX_MODE answered %r, which is not a matrix mode, '
                    'so there is nothing to put back', mode)
        self.swapBuffers()
        return True

    def tkExpose(self, *dummy):
        """Draw one frame, under the name the Togl-based widget used"""
        self.render()

    def tkMap(self, *dummy):
        """Draw one frame, under the name the Togl-based widget used"""
        self.render()


class Opengl(RawOpengl):
    """\
Tkinter bindings for an Opengl widget.
Mike Hartshorn
Department of Chemistry
University of York, UK
http://www.yorvic.york.ac.uk/~mjh/

A viewer with the mouse bindings a model is examined by: button 1 translates,
button 2 rotates and button 3 zooms.  Set ``redraw`` to a callable taking the
widget, or subclass and override it.
"""

    def __init__(self, master=None, cnf=None, **kw):
        """\
        Create an opengl widget.
        Arrange for redraws when the window is exposed or when
        it changes size."""
        # `None` rather than `{}`: a mutable default is one object shared
        # by every widget that does not pass its own.
        cnf = {} if cnf is None else cnf

        RawOpengl.__init__(self, master, cnf, **kw)
        self.initialised = 0

        # Current coordinates of the mouse.
        self.xmouse = 0
        self.ymouse = 0

        # Where we are centering.
        self.xcenter = 0.0
        self.ycenter = 0.0
        self.zcenter = 0.0

        # The _back color
        self.r_back = 1.
        self.g_back = 0.
        self.b_back = 1.

        # Where the eye is
        self.distance = 10.0

        # Field of view in y direction
        self.fovy = 30.0

        # Position of clipping planes.
        self.near = 0.1
        self.far = 1000.0

        # Is the widget allowed to autospin?
        self.autospin_allowed = 0

        # Is the widget currently autospinning?
        self.autospin = 0

        # Basic bindings for the virtual trackball
        self.bind('<Shift-Button-1>', self.tkHandlePick)
        self.bind('<Button-1>', self.tkRecordMouse)
        self.bind('<B1-Motion>', self.tkTranslate)
        self.bind('<Button-2>', self.StartRotate)
        self.bind('<B2-Motion>', self.tkRotate)
        self.bind('<ButtonRelease-2>', self.tkAutoSpin)
        self.bind('<Button-3>', self.tkRecordMouse)
        self.bind('<B3-Motion>', self.tkScale)

    def help(self):
        """Help for the widget."""
        from tkinter import dialog

        d = dialog.Dialog(None, {'title': 'Viewer help',
                                 'text': 'Button-1: Translate\n'
                                         'Button-2: Rotate\n'
                                         'Button-3: Zoom\n'
                                         'Reset: Resets transformation to identity\n',
                                 'bitmap': 'questhead',
                                 'default': 0,
                                 'strings': ('Done', 'Ok')})
        assert d

    def activate(self):
        """Cause this Opengl widget to be the current destination for drawing."""
        self.makeCurrent()

    # This should almost certainly be part of some derived class.
    # But I have put it here for convenience.
    def basic_lighting(self):
        """\
        Set up some basic lighting (single infinite light source).

        Also switch on the depth buffer."""

        self.activate()
        light_position = (1, 1, 1, 0)
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def initgl(self):
        """Light the scene the first time there is a context to light it in"""
        self.basic_lighting()
        self.initialised = 1

    def set_background(self, r, g, b):
        """Change the background colour of the widget."""
        self.r_back = r
        self.g_back = g
        self.b_back = b
        self.tkRedraw()

    def set_centerpoint(self, x, y, z):
        """Set the new center point for the model.
        This is where we are looking."""
        self.xcenter = x
        self.ycenter = y
        self.zcenter = z
        self.tkRedraw()

    def set_eyepoint(self, distance):
        """Set how far the eye is from the position we are looking."""
        self.distance = distance
        self.tkRedraw()

    def reset(self):
        """Reset rotation matrix for this widget."""
        self.activate()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.tkRedraw()

    def tkHandlePick(self, event):
        """Handle a pick on the scene."""
        if hasattr(self, 'pick'):
            # here we need to use glu.UnProject

            # Tk and X have their origin top left,
            # while Opengl has its origin bottom left.
            # So we need to subtract y from the window height to get
            # the proper pick position for Opengl
            self.activate()
            realy = self.winfo_height() - event.y

            p1 = gluUnProject(event.x, realy, 0.)
            p2 = gluUnProject(event.x, realy, 1.)

            if self.pick(self, p1, p2):
                """If the pick method returns true we redraw the scene."""
                self.tkRedraw()

    def tkRecordMouse(self, event):
        """Record the current mouse position."""
        self.xmouse = event.x
        self.ymouse = event.y

    def StartRotate(self, event):
        # Switch off any autospinning if it was happening
        self.autospin = 0
        self.tkRecordMouse(event)

    def tkScale(self, event):
        """Scale the scene.  Achieved by moving the eye position.

        Dragging up zooms in, while dragging down zooms out
        """
        scale = 1 - 0.01 * (event.y - self.ymouse)
        # do some sanity checks, scale no more than
        # 1:1000 on any given click+drag
        if scale < 0.001:
            scale = 0.001
        elif scale > 1000:
            scale = 1000
        self.distance = self.distance * scale
        self.tkRedraw()
        self.tkRecordMouse(event)

    def do_AutoSpin(self):
        self.activate()

        glRotateScene(0.5, self.xcenter, self.ycenter, self.zcenter, self.yspin, self.xspin, 0, 0)
        self.tkRedraw()

        if self.autospin:
            self.after(10, self.do_AutoSpin)

    def tkAutoSpin(self, event):
        """Perform autospin of scene."""
        self.after(4)
        self.update_idletasks()

        # This could be done with one call to pointerxy but I'm not sure
        # it would any quicker as we would have to split up the resulting
        # string and then conv
        x = self.tk.getint(self.tk.call('winfo', 'pointerx', self._w))
        y = self.tk.getint(self.tk.call('winfo', 'pointery', self._w))

        if self.autospin_allowed:
            if x != event.x_root and y != event.y_root:
                self.autospin = 1

        self.yspin = x - event.x_root
        self.xspin = y - event.y_root

        self.after(10, self.do_AutoSpin)

    def tkRotate(self, event):
        """Perform rotation of scene."""
        self.activate()
        glRotateScene(0.5, self.xcenter, self.ycenter, self.zcenter, event.x, event.y, self.xmouse, self.ymouse)
        self.tkRedraw()
        self.tkRecordMouse(event)

    def tkTranslate(self, event):
        """Perform translation of scene."""
        self.activate()

        # Scale mouse translations to object viewplane so object tracks with mouse
        win_height = max(1, self.winfo_height())
        obj_c = (self.xcenter, self.ycenter, self.zcenter)
        win = gluProject(obj_c[0], obj_c[1], obj_c[2])
        obj = gluUnProject(win[0], win[1] + 0.5 * win_height, win[2])
        dist = math.sqrt(v3distsq(obj, obj_c))
        scale = abs(dist / (0.5 * win_height))

        glTranslateScene(scale, event.x, event.y, self.xmouse, self.ymouse)
        self.tkRedraw()
        self.tkRecordMouse(event)

    def render(self):
        """Draw the scene: clear, set up the camera, and call ``redraw``"""
        if not self.makeCurrent():
            return False
        glPushMatrix()                  # Protect our matrix
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        glViewport(0, 0, w, h)

        # Clear the background and depth buffer.
        glClearColor(self.r_back, self.g_back, self.b_back, 0.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fovy, float(w) / float(max(1, h)), self.near, self.far)

        gluLookAt(self.xcenter, self.ycenter, self.zcenter + self.distance,
                  self.xcenter, self.ycenter, self.zcenter,
                  0., 1., 0.)
        glMatrixMode(GL_MODELVIEW)

        # Call objects redraw method.
        self.redraw(self)
        glFlush()                       # Tidy up
        glPopMatrix()                   # Restore the matrix

        self.swapBuffers()
        return True

    def redraw(self, *args, **named):
        """Prevent access errors if user doesn't set redraw fast enough"""

    def reshape(self, width, height):
        """The camera is rebuilt per frame, so a resize needs nothing here"""

    def tkPrint(self, file):
        """Turn the current scene into PostScript via the feedback buffer."""
        self.activate()
