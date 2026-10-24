"""The Togl widget, and the examination widgets built on it.

Togl is a Tcl C extension that must be installed separately (Debian packages
it as ``libtogl2``).  :class:`Togl` is the only class in this package that
needs it.  :class:`~OpenGL.Tk.widget.GLFrame` does not.  :class:`Togl` is
provided for code that uses it directly.  Togl is loaded by the first call to
:func:`loadTogl`, not when this module is imported.

:class:`RawOpengl` and :class:`Opengl` are ``GLFrame`` subclasses and do not
need Togl.  Both draw with the fixed-function pipeline (``glMatrixMode``,
``gluPerspective``, ``glLightfv``), so both request a compatibility profile.
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
from OpenGL.raw.GL._types import GLfloat
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.widget import GLFrame
from OpenGL._scalar import as_int

log = logging.getLogger(__name__)

#: Every value ``GL_MATRIX_MODE`` can return.  Any other value means no context
#: was current: ``glGetIntegerv`` then leaves its output untouched and returns
#: 0, which is not a mode.  Restoring 0 would raise from the ``finally`` in
#: :meth:`RawOpengl.render`, after the frame is drawn and before it is swapped,
#: and the frame would be lost.
MATRIX_MODES = frozenset((GL_MODELVIEW, GL_PROJECTION, GL_TEXTURE, GL_COLOR))

__all__ = [
    'TOGL_NORMAL', 'TOGL_OPTIONS', 'TOGL_OVERLAY', 'Opengl', 'RawOpengl',
    'Togl', 'attributesFromToglOptions', 'glDistFromLine', 'glRotateScene',
    'glTranslateScene', 'loadTogl', 'toglLibraryPath',
]

# Keith Junius <junius@chem.rug.nl> provided many changes to Togl
TOGL_NORMAL = 1
TOGL_OVERLAY = 2

#: The context attributes the fixed-function widgets below request.  The core
#: profile removed every call they draw with.
LEGACY_ATTRIBUTES = dict(profile='compatibility', version=None, depthSize=24)

#: Togl's widget options, mapped to context attributes.  Scripts written for
#: the Togl widget, including this package's examples, use calls such as
#: ``Opengl(master, double=1, depth=1)``, so these options keep their Togl
#: meaning.  Each value is the attribute the option sets.  For options Togl
#: spells as a flag where a size is needed, the value is an
#: ``(attribute, value-when-true)`` pair.
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

#: Togl options for features a window-system context does not have, or that
#: Tk itself controls.  They are accepted, logged and ignored.  A script that
#: passes ``privatecmap=0`` already gets that behaviour.
TOGL_OPTIONS_IGNORED = (
    'accum', 'accumredsize', 'accumgreensize', 'accumbluesize',
    'accumalphasize', 'auxbuffers', 'ident', 'indirect', 'overlay',
    'pixelformat', 'privatecmap', 'rgba', 'sharecontext', 'sharelist',
)


def attributesFromToglOptions(options):
    """Split Togl's widget options out of a widget's keyword arguments

    Returns ``(attributes, remaining, animate)``: the context attributes to
    request, the options to pass to Tk, and the animation interval (Togl's
    ``time`` option).  ``options`` is not modified.

    This function does not use Tk or a display, so it can be tested without
    one.
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
    """The directory in this package for a Togl built for this interpreter

    ``src/togl.py`` in the source distribution downloads a binary Togl into
    it.  Togl 2.0 and above use Tcl stubs, so the Tk version does not matter.
    A 64-bit Python needs a 64-bit build, so the name has a ``-64`` suffix.
    """
    suffix = '-64' if sys.maxsize > 2 ** 32 else ''
    try:
        return os.path.join(os.path.dirname(__file__),
                            'togl-' + sys.platform + suffix)
    except NameError:                   # pragma: no cover - no __file__
        return ''


def loadTogl(master=None):
    """Load the Togl Tcl package into ``master``'s interpreter

    Returns the widget whose interpreter Togl was loaded into.  Raises
    ``TclError`` if Togl is not installed, naming the package that provides
    it.

    :class:`Togl` calls this when it is created.  Importing :mod:`OpenGL.Tk`
    therefore needs neither a display nor Togl.
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

    Needs the Togl Tcl extension, which :func:`loadTogl` loads when the first
    instance is created.  :class:`~OpenGL.Tk.widget.GLFrame` needs no Tcl
    extension.
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

    A :class:`~OpenGL.Tk.widget.GLFrame` that saves and restores the
    projection matrix around each frame, as its subclasses expect.  The matrix
    stack needs a compatibility profile context.
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
        """Draw one frame, restoring the projection matrix afterwards"""
        # Process Tk's idle work before making the context current.  Idle
        # work maps and resizes widgets, and mapping a sibling widget makes
        # the sibling's context current.  A makeCurrent before this line
        # would not hold after it, and the state read below would be zero.
        # The symptom is glMatrixMode(0) from the finally, in a process with
        # a second widget.
        self.update_idletasks()
        if not self.makeCurrent():
            return False
        # The mode is an enum, so use the integer getter.  The double getter
        # returns 5888.0, and restoring the mode with a float raises
        # ctypes.ArgumentError from the finally below.  The frame is then
        # lost, because the buffers are swapped after it.
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
        """Draw one frame; :meth:`render` under the Togl widget's name"""
        self.render()

    def tkMap(self, *dummy):
        """Draw one frame; :meth:`render` under the Togl widget's name"""
        self.render()


class Opengl(RawOpengl):
    """\
Tkinter bindings for an Opengl widget.
Mike Hartshorn
Department of Chemistry
University of York, UK
http://www.yorvic.york.ac.uk/~mjh/

A model viewer with mouse bindings: button 1 translates, button 2 rotates and
button 3 zooms.  Set ``redraw`` to a callable taking the widget, or subclass
and override it.
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
        # A ctypes array rather than a tuple.  A tuple has no data pointer,
        # so with ERROR_ON_COPY set (the caller's request that PyOpenGL make
        # no implicit copies) the call would raise inside this library.
        light_position = (GLfloat * 4)(1.0, 1.0, 1.0, 0.0)
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def initgl(self):
        """Set up lighting once the context exists"""
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
        """Do nothing; :meth:`render` sets the viewport and camera per frame"""

    def tkPrint(self, file):
        """Turn the current scene into PostScript via the feedback buffer."""
        self.activate()
