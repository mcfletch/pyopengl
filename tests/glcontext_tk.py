#! /usr/bin/env python3
"""Tkinter windowing backend for :class:`glcontext.ContextTestCase`.

Implements the ``_create_context`` / ``_swap`` / ``_destroy_context`` hooks on
:class:`OpenGL.Tk.GLFrame`, so the suite can be run against the widget this
package ships -- which is the only way the widget is held to the same
behaviour as everything else here.

Desktop OpenGL only: a Tk context is made through the window system's own API
(GLX, WGL), and neither of those creates an ES context.  A test that asks for
one skips rather than being given a desktop context under the name.
"""

from __future__ import print_function

import tkinter

from OpenGL.Tk import ContextAttributes, GLFrame, TkContextError

_ES_APIS = ('gles', 'es')

#: How the suite spells a profile, and how :mod:`OpenGL.Tk.attributes` does.
_PROFILES = {
    'core': 'core',
    'compatibility': 'compatibility',
    'compat': 'compatibility',
    'any': 'legacy',
}


class TkBackend(object):
    """Mixin supplying a context in a Tk widget"""

    #: identifies the backend to API bases that need to know.
    backend_name = 'tk'

    _root = None
    _frame = None

    def _create_context(self):
        api = getattr(self, 'api', 'gl').lower()
        if api in _ES_APIS:
            self.skipTest(
                'OpenGL.Tk makes desktop GL contexts; GLX and WGL have no ES '
                'equivalent to make one through')
        profile = _PROFILES[getattr(self, 'profile', 'compatibility').lower()]
        try:
            self._root = tkinter.Tk()
        except tkinter.TclError as err:
            self.skipTest('Tk could not open a display: %s' % (err,))
        self._root.title(type(self).__name__)
        if not self.visible:
            # Withdrawn *after* the context exists: a window that was never
            # mapped has no native handle to make one against.  See
            # _showOrHide.
            pass
        attributes = ContextAttributes(
            profile=profile,
            version=None if profile == 'legacy' else tuple(self.gl_version),
            redSize=self.red_size,
            greenSize=self.green_size,
            blueSize=self.blue_size,
            alphaSize=self.alpha_size,
            depthSize=self.depth_size,
            stencilSize=self.stencil_size,
        )
        self._frame = GLFrame(self._root, attributes=attributes,
                              width=self.width, height=self.height)
        self._frame.pack(fill='both', expand=True)
        try:
            self._frame.waitForMap()
        except TkContextError as err:
            self._destroy_context()
            self.skipTest(
                'Could not create a %s %s %s context in a Tk widget: %s'
                % (api, profile, self.gl_version, err))
        self._showOrHide()
        self._frame.makeCurrent()

    def _showOrHide(self):
        """Take the window off the screen where the test does not want it seen

        The context exists by now, which is the point: a Tk window that has
        never been mapped has no native window for one to be made against, so
        hiding it is something done afterwards rather than instead.
        """
        if not self.visible:
            self._root.withdraw()
            self._root.update()

    def _swap(self):
        if self._frame is not None:
            self._frame.swapBuffers()

    def _make_current(self):
        if self._frame is None:
            raise RuntimeError('this backend has no context to make current')
        self._frame.makeCurrent()

    def _destroy_context(self):
        if self._frame is not None:
            self._frame.destroyContext()
            self._frame = None
        if self._root is not None:
            try:
                self._root.destroy()
            except tkinter.TclError:
                pass
            self._root = None
