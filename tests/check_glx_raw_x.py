# requires: glx
"""What GLX reports about the display, asked through raw Xlib.

The display, the screen and the framebuffer configurations come from libX11
directly rather than through a toolkit, which is the arrangement a program
embedding PyOpenGL in an existing X application has.  What it checks is that
the GLX bindings accept those handles and answer with them: a version, an
extension string, and the attributes of each framebuffer configuration.
"""

from __future__ import print_function

import checkutils

import os
import sys

from OpenGL.GL import *
from OpenGL.GLX import *
from OpenGL.GLX.EXT.texture_from_pixmap import *

import os

attributes = [
    #    GLX_BIND_TO_TEXTURE_RGBA_EXT, 1,
    #    GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
    #    GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
    GLX_DOUBLEBUFFER,
    1,
    #    GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
    GL_NONE,
]

# from OpenGL import platform
import ctypes
from OpenGL.platform import ctypesloader

X11 = ctypesloader.loadLibrary(ctypes.cdll, 'X11')
XDefaultScreen = X11.XDefaultScreen
XDefaultScreen.argtypes = [ctypes.POINTER(Display)]
XOpenDisplay = X11.XOpenDisplay
# The display name is a char*, and ctypes hands an un-annotated `str` to a
# function as a wchar_t* -- which XOpenDisplay reads as a name nothing answers
# to, so every display looks closed.
XOpenDisplay.argtypes = [ctypes.c_char_p]
XOpenDisplay.restype = ctypes.POINTER(Display)
XDefaultScreenOfDisplay = X11.XDefaultScreenOfDisplay
XDefaultScreenOfDisplay.argtypes = [ctypes.POINTER(Display)]


def main():
    name = os.environ.get('DISPLAY')
    dsp = XOpenDisplay(name.encode('ascii') if name else None)
    if not dsp:
        # Everything below dereferences this pointer, so a display that would
        # not open is nothing to test with rather than something to test.
        checkutils.skip(
            'X would not open the display %r' % (name,)
        )
    screen = XDefaultScreenOfDisplay(dsp)
    print('X Display %s Screen %s' % (dsp, screen))
    major, minor = GLint(), GLint()
    glXQueryVersion(dsp, major, minor)
    version = (major.value, minor.value)
    print('glX Version: %s.%s' % version)
    if version >= (1, 1):
        print(glXQueryExtensionsString(dsp, screen))
        if version >= (1, 2):
            d = glXGetCurrentDisplay()
            if d:
                print('Current display', d)
            else:
                print('GLX could not find the current display')
        else:
            d = dsp
    if version >= (1, 3):
        elements = GLint(0)
        configs = glXChooseFBConfig(
            dsp, screen, (GLint * len(attributes))(*attributes), elements
        )
        print('%s configs found' % (elements.value))
        for config in range(elements.value):
            print('Config: %s %s' % (config, configs[config][0]))
            samples = ctypes.c_int()
            for attribute in (
                'GLX_FBCONFIG_ID',
                'GLX_BUFFER_SIZE',
                'GLX_LEVEL',
                'GLX_DOUBLEBUFFER',
                'GLX_STEREO',
                'GLX_SAMPLES',
                'GLX_SAMPLE_BUFFERS',
                'GLX_DRAWABLE_TYPE',
            ):
                glXGetFBConfigAttrib(
                    dsp, configs[config], globals()[attribute], samples
                )
                print('%s -> %s' % (attribute, samples.value))
            print()
    from OpenGL.raw.GLX import _types

    print('Extension List', _types.GLXQuerier.getExtensions())
    print('OK')


if __name__ == "__main__":
    checkutils.run_check(main)
