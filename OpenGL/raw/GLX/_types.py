# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL import platform as _p, constant, extensions
from ctypes import *
from OpenGL.raw.GL._types import *
from OpenGL._bytes import as_8_bit
c_void = None
void = None 
Bool = c_uint

def displayName():
    """The X display to connect to, as ``XOpenDisplay`` wants it

    Bytes, because the parameter is a ``char *``: handed a ``str`` with no
    ``argtypes`` set, ctypes passes ``wchar_t *``, X reads a display name out
    of the wrong encoding and the connection fails -- which is reported as an
    X server with GLX version 0.0 and no extensions at all.

    ``None`` where nothing names one, which X reads as "whatever this session
    is using".  That is not the same as an empty name, which it refuses.
    """
    import os

    name = os.environ.get('DISPLAY', '').strip()
    return name.encode('utf-8') if name else None


def _x11():
    """The Xlib entry points this module calls, with their signatures set"""
    from OpenGL.raw.GLX import _types
    from OpenGL.platform import ctypesloader
    import ctypes

    library = ctypesloader.loadLibrary(ctypes.cdll, 'X11')
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]
    library.XOpenDisplay.restype = ctypes.POINTER(_types.Display)
    library.XCloseDisplay.argtypes = [ctypes.POINTER(_types.Display)]
    library.XDefaultScreen.argtypes = [ctypes.POINTER(_types.Display)]
    library.XDefaultScreen.restype = ctypes.c_int
    return library


class _GLXQuerier( extensions.ExtensionQuerier ):
    """What GLX's version and extension list are asked through

    Every GLX extension entry point is resolved through this: the gate in
    ``OpenGL._dispatch.support`` asks ``checkExtension('GLX_...')``, which ends
    up here.  So an answer of "no extensions" makes every GLX extension read as
    absent -- which is not a small thing, since ``GLX_ARB_create_context`` is
    how a context is asked for a version or a profile.

    It answers **without a current context**, by opening a display connection
    of its own, because it has to: the extension that creates a context cannot
    be gated on already having one.
    """
    prefix = as_8_bit('GLX_')
    assumed_version = [1,1]
    version_prefix = as_8_bit('GLX_VERSION_GLX_')

    def display( self ):
        """A display connection for the length of the ``with`` block

        Closed on the way out.  Each query used to open one and drop it, so a
        program that probed a few extensions leaked a file descriptor apiece.
        """
        import contextlib

        @contextlib.contextmanager
        def opened():
            library = _x11()
            connection = library.XOpenDisplay(displayName())
            try:
                yield connection
            finally:
                if connection:
                    library.XCloseDisplay(connection)

        return opened()

    def getDisplay( self ):
        """A display connection the caller then owns and must close

        :meth:`display` is the form that closes it; this stays for callers
        that already had it.
        """
        return _x11().XOpenDisplay(displayName())

    def getScreen( self, display ):
        return _x11().XDefaultScreen( display )

    def pullVersion( self ):
        from OpenGL.GLX import glXQueryVersion
        import ctypes
        if not glXQueryVersion:
            return [1,1]
        with self.display() as connection:
            if not connection:
                return [1,1]        # no server to ask; assume the base version
            major,minor = ctypes.c_int(),ctypes.c_int()
            if not glXQueryVersion(connection, major, minor):
                return [1,1]        # the server has no GLX at all
            return [major.value,minor.value]

    def pullExtensions( self ):
        if self.getVersion() >= [1,2]:
            from OpenGL.GLX import glXQueryExtensionsString

            if not glXQueryExtensionsString:
                return []
            with self.display() as connection:
                if not connection:
                    return []
                reported = glXQueryExtensionsString(
                    connection, self.getScreen( connection ))
                # A ctypes c_char_p result is already a copy, but the split
                # happens here anyway: the string belongs to the connection.
                return reported.split() if reported else []
        return []
GLXQuerier=_GLXQuerier()


class struct___GLXcontextRec(Structure):
    __slots__ = [
    ]
struct___GLXcontextRec._fields_ = [
    ('_opaque_struct', c_int)
]

class struct___GLXcontextRec(Structure):
    __slots__ = [
    ]
struct___GLXcontextRec._fields_ = [
    ('_opaque_struct', c_int)
]

GLXContext = POINTER(struct___GLXcontextRec) 	# /usr/include/GL/glx.h:178
XID = c_ulong 	# /usr/include/X11/X.h:66
GLXPixmap = XID 	# /usr/include/GL/glx.h:179
GLXDrawable = XID 	# /usr/include/GL/glx.h:180
class struct___GLXFBConfigRec(Structure):
    __slots__ = [
    ]
struct___GLXFBConfigRec._fields_ = [
    ('_opaque_struct', c_int)
]

class struct___GLXFBConfigRec(Structure):
    __slots__ = [
    ]
struct___GLXFBConfigRec._fields_ = [
    ('_opaque_struct', c_int)
]

GLXFBConfig = POINTER(struct___GLXFBConfigRec) 	# /usr/include/GL/glx.h:182
GLXFBConfigID = XID 	# /usr/include/GL/glx.h:183
GLXContextID = XID 	# /usr/include/GL/glx.h:184
GLXWindow = XID 	# /usr/include/GL/glx.h:185
GLXPbuffer = XID 	# /usr/include/GL/glx.h:186
GLXPbufferSGIX = XID
GLXVideoSourceSGIX = XID

class struct_anon_103(Structure):
    __slots__ = [
        'visual',
        'visualid',
        'screen',
        'depth',
        'class',
        'red_mask',
        'green_mask',
        'blue_mask',
        'colormap_size',
        'bits_per_rgb',
    ]
class struct_anon_18(Structure):
    __slots__ = [
        'ext_data',
        'visualid',
        'class',
        'red_mask',
        'green_mask',
        'blue_mask',
        'bits_per_rgb',
        'map_entries',
    ]
class struct__XExtData(Structure):
    __slots__ = [
        'number',
        'next',
        'free_private',
        'private_data',
    ]
XPointer = c_char_p 	# /usr/include/X11/Xlib.h:84
struct__XExtData._fields_ = [
    ('number', c_int),
    ('next', POINTER(struct__XExtData)),
    ('free_private', POINTER(CFUNCTYPE(c_int, POINTER(struct__XExtData)))),
    ('private_data', XPointer),
]

XExtData = struct__XExtData 	# /usr/include/X11/Xlib.h:163
VisualID = c_ulong 	# /usr/include/X11/X.h:76
struct_anon_18._fields_ = [
    ('ext_data', POINTER(XExtData)),
    ('visualid', VisualID),
    ('class', c_int),
    ('red_mask', c_ulong),
    ('green_mask', c_ulong),
    ('blue_mask', c_ulong),
    ('bits_per_rgb', c_int),
    ('map_entries', c_int),
]

Visual = struct_anon_18 	# /usr/include/X11/Xlib.h:246
struct_anon_103._fields_ = [
    ('visual', POINTER(Visual)),
    ('visualid', VisualID),
    ('screen', c_int),
    ('depth', c_int),
    ('class', c_int),
    ('red_mask', c_ulong),
    ('green_mask', c_ulong),
    ('blue_mask', c_ulong),
    ('colormap_size', c_int),
    ('bits_per_rgb', c_int),
]

XVisualInfo = struct_anon_103 	# /usr/include/X11/Xutil.h:294
class struct__XDisplay(Structure):
    __slots__ = [
    ]
struct__XDisplay._fields_ = [
    ('_opaque_struct', c_int)
]

class struct__XDisplay(Structure):
    __slots__ = [
    ]
struct__XDisplay._fields_ = [
    ('_opaque_struct', c_int)
]

Display = struct__XDisplay 	# /usr/include/X11/Xlib.h:495

Pixmap = XID 	# /usr/include/X11/X.h:102
Font = XID 	# /usr/include/X11/X.h:100
Window = XID 	# /usr/include/X11/X.h:96
GLX_ARB_get_proc_address = constant.Constant( 'GLX_ARB_get_proc_address', 1 )
__GLXextFuncPtr = CFUNCTYPE(None) 	# /usr/include/GL/glx.h:330

# EXT_texture_from_pixmap (/usr/include/GL/glx.h:436)
class struct_anon_111(Structure):
    __slots__ = [
        'event_type',
        'draw_type',
        'serial',
        'send_event',
        'display',
        'drawable',
        'buffer_mask',
        'aux_buffer',
        'x',
        'y',
        'width',
        'height',
        'count',
    ]
struct_anon_111._fields_ = [
    ('event_type', c_int),
    ('draw_type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('drawable', GLXDrawable),
    ('buffer_mask', c_uint),
    ('aux_buffer', c_uint),
    ('x', c_int),
    ('y', c_int),
    ('width', c_int),
    ('height', c_int),
    ('count', c_int),
]

GLXPbufferClobberEvent = struct_anon_111 	# /usr/include/GL/glx.h:502
class struct_anon_112(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'drawable',
        'event_type',
        'ust',
        'msc',
        'sbc',
    ]
struct_anon_112._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('drawable', GLXDrawable),
    ('event_type', c_int),
    ('ust', c_int64),
    ('msc', c_int64),
    ('sbc', c_int64),
]

GLXBufferSwapComplete = struct_anon_112 	# /usr/include/GL/glx.h:514
class struct___GLXEvent(Union):
    __slots__ = [
        'glxpbufferclobber',
        'glxbufferswapcomplete',
        'pad',
    ]
struct___GLXEvent._fields_ = [
    ('glxpbufferclobber', GLXPbufferClobberEvent),
    ('glxbufferswapcomplete', GLXBufferSwapComplete),
    ('pad', c_long * 24),
]

GLXEvent = struct___GLXEvent 	# /usr/include/GL/glx.h:520

class GLXHyperpipeConfigSGIX( Structure ):
    _fields_ = [
        ('pipeName', c_char * 80),
        ('channel',c_int),
        ('participationType',c_uint),
        ('timeSlice',c_int),
    ]


#: ``GLX_SGIX_hyperpipe``'s other structure, alongside the configuration one
#: above.  Both name a pipe in the same 80-byte field; the specification writes
#: that length as ``GLX_HYPERPIPE_PIPE_NAME_LENGTH_SGIX`` and gives it as 80.
class GLXHyperpipeNetworkSGIX( Structure ):
    _fields_ = [
        ('pipeName', c_char * 80),
        ('networkId', c_int),
    ]

#: ``GLX_SGIX_fbconfig``'s framebuffer configuration.  The same opaque record
#: the core ``GLXFBConfig`` points at -- the extension is what the core
#: mechanism was promoted from, so the two name one thing.
GLXFBConfigSGIX = POINTER(struct___GLXFBConfigRec)

#: ``GLX_NV_video_capture``'s device handle: an X resource id, as the other
#: GLX handles that are not pointers are.
GLXVideoCaptureDeviceNV = XID
