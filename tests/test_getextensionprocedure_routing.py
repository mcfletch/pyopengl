"""getExtensionProcedure routes a name to the interface that owns it.

Regression test for the EGL device-enumeration bug: GLVND's
glXGetProcAddressARB returns a non-null but wrong pointer for an ``egl*`` name,
so resolving an EGL extension (e.g. eglQueryDevicesEXT) through GLX -- which is
what happened whenever no GL context was current -- bound a bogus pointer whose
call silently returned EGL_FALSE. An ``egl*`` name must resolve through
eglGetProcAddress and a ``glX*`` name through glXGetProcAddressARB, regardless
of which context (if any) is current.
"""

from OpenGL.platform.unix import UnixPlatform


class _Recorder:
    """Stand-in get-proc-address that records its calls and returns a tag."""

    def __init__(self, tag):
        self.tag = tag
        self.calls = []

    def __call__(self, name):
        self.calls.append(name)
        return self.tag


def _platform(egl, glx, active_api):
    plat = UnixPlatform()
    # lazy_property is a non-data descriptor, so these instance attributes
    # shadow the real library resolvers -- no libGL/libEGL is loaded.
    plat.eglGetProcAddress = egl
    plat.glXGetProcAddressARB = glx
    plat._active_api = active_api
    plat.GetCurrentContext = lambda: None  # never probe a real context
    return plat


def test_egl_name_resolves_via_egl_without_context():
    egl, glx = _Recorder('egl'), _Recorder('glx')
    plat = _platform(egl, glx, active_api=None)
    assert plat.getExtensionProcedure(b'eglQueryDevicesEXT') == 'egl'
    assert egl.calls == [b'eglQueryDevicesEXT']
    assert glx.calls == []


def test_glx_name_resolves_via_glx_even_under_egl_context():
    egl, glx = _Recorder('egl'), _Recorder('glx')
    plat = _platform(egl, glx, active_api='egl')
    assert plat.getExtensionProcedure(b'glXCreateContextAttribsARB') == 'glx'
    assert glx.calls == [b'glXCreateContextAttribsARB']
    assert egl.calls == []


def test_core_gl_name_follows_active_api():
    egl, glx = _Recorder('egl'), _Recorder('glx')
    assert _platform(egl, glx, 'egl').getExtensionProcedure(b'glGenBuffers') == 'egl'
    egl2, glx2 = _Recorder('egl'), _Recorder('glx')
    assert _platform(egl2, glx2, 'glx').getExtensionProcedure(b'glGenBuffers') == 'glx'


def test_egl_name_as_str_is_routed_by_prefix():
    """as_8_bit yields bytes in practice, but a str name must route too."""
    egl, glx = _Recorder('egl'), _Recorder('glx')
    plat = _platform(egl, glx, active_api=None)
    assert plat.getExtensionProcedure('eglQueryDevicesEXT') == 'egl'
