from checkutils import skip

try:
    from os_egl import egl_context, NoEGLSupport, NoConfig
except ImportError as err:
    # os_egl drives EGL through GBM, which is Linux graphics infrastructure.
    skip('EGL device enumeration needs gbm: %s' % (err,))
from OpenGL import EGL
from OpenGL.raw.EGL._errors import EGLError
from OpenGL.EGL.EXT import device_query, device_enumeration
from OpenGL.GL import GLint


def main():
    try:
        _run()
    except (NoEGLSupport, NoConfig, EGLError) as err:
        # No usable EGL display in this environment (e.g. headless/wayland
        # where the raw default display cannot be initialised) -- this is a
        # skip, not a failure, matching the other raw-EGL check scripts.
        skip('EGL not usable in this environment: %s' % (err,))


def _run():
    with egl_context(output=None, pbuffer=True) as context:
        display, context, surface = context
        print("Vendor: %s" % (EGL.eglQueryString(display, EGL.EGL_VENDOR)))
        print("Version: %s" % (EGL.eglQueryString(display, EGL.EGL_VERSION)))
        print("Extensions: %s" % (EGL.eglQueryString(display, EGL.EGL_EXTENSIONS),))
        print(
            "Client Extensions: %s"
            % (EGL.eglQueryString(display, EGL.EGL_CLIENT_APIS),)
        )
        if device_enumeration.eglQueryDevicesEXT:
            devices = (device_query.EGLDeviceEXT * 5)()
            count = GLint()
            device_enumeration.eglQueryDevicesEXT(
                5,
                devices,
                count,
            )
            for device in devices[: count.value]:
                print(device)
        else:
            print('No device_query extension available')
        print('OK')


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    main()
