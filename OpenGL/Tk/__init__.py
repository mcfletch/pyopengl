"""OpenGL in a Tkinter widget.

:class:`~OpenGL.Tk.widget.GLFrame` is an ordinary ``tkinter.Frame`` that owns a
GL context on its own native window.  It needs no Tcl extension: Tk hands out
the platform's window handle and the context is made against it through the
window system's own API.

    from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor
    from OpenGL.Tk import GLFrame
    import tkinter

    class Scene(GLFrame):
        def initgl(self):
            glClearColor(0.2, 0.3, 0.3, 1.0)
        def redraw(self):
            glClear(GL_COLOR_BUFFER_BIT)

    root = tkinter.Tk()
    Scene(root, width=640, height=480).pack(fill='both', expand=True)
    root.mainloop()

What the context is asked for -- profile, version, buffer sizes, multisampling
-- is :class:`~OpenGL.Tk.attributes.ContextAttributes`, given as keywords to the
widget or as a ready-made object.  The default is a core profile, so a Tk
application can use shaders and vertex array objects.

X11 and Windows are implemented; Tk on Aqua raises
:class:`~OpenGL.Tk.errors.TkContextError` saying what it needs, and
:mod:`OpenGL.Tk.togl` is the Togl-based widget for anybody who has Togl.  See
``plans/TK-WIDGET.md``.

Importing this module opens no window, needs no display and loads no Tcl
package: it is a question with an answer rather than an action.  The tkinter
names come with it, as they always have, so ``from OpenGL.Tk import *`` still
gives ``Tk``, ``Frame`` and the rest.
"""

from tkinter import *
from tkinter import _default_root                     # type: ignore[attr-defined]

from OpenGL.Tk.attributes import PROFILES, ContextAttributes
from OpenGL.Tk.context import createContext, windowingSystem
from OpenGL.Tk.errors import TkContextError
from OpenGL.Tk.togl import (
    TOGL_NORMAL, TOGL_OVERLAY, Opengl, RawOpengl, Togl, glDistFromLine,
    glRotateScene, glTranslateScene, loadTogl,
)
from OpenGL.Tk.widget import GLFrame

import tkinter as _tkinter

#: This module's own names, and tkinter's with them.  ``from OpenGL.Tk import
#: *`` has always given both -- a script that used it wrote ``Tk()`` and
#: ``Frame()`` without importing tkinter itself -- so listing only the new
#: names here would break every one of those scripts.
__all__ = list(getattr(_tkinter, '__all__', ())) + [
    'ContextAttributes',
    'GLFrame',
    'Opengl',
    'PROFILES',
    'RawOpengl',
    'TOGL_NORMAL',
    'TOGL_OVERLAY',
    'TkContextError',
    'Togl',
    'createContext',
    'glDistFromLine',
    'glRotateScene',
    'glTranslateScene',
    'loadTogl',
    'windowingSystem',
]
