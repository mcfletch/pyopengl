from os_egl import egl_context
from OpenGL import EGL
from OpenGL.EGL.EXT import device_query, device_enumeration
from OpenGL.GL import GLint

def main():
    with egl_context(output=None) as context:
        display,context,surface = context
        print("Vendor: %s"%(EGL.eglQueryString(display, EGL.EGL_VENDOR)))
        print("Version: %s"%(EGL.eglQueryString(display, EGL.EGL_VERSION)))
        print("Extensions: %s"%(EGL.eglQueryString(display, EGL.EGL_EXTENSIONS),))
        print("Client Extensions: %s"%(EGL.eglQueryString(display, EGL.EGL_CLIENT_APIS),))
        if device_enumeration.eglQueryDevicesEXT:
            devices = (device_query.EGLDeviceEXT * 5)()
            count = GLint()
            device_enumeration.eglQueryDevicesEXT(
                5,
                devices,
                count,
            )
            for device in devices[:int(count)]:
                print(device)
        else:
            print('No device_query extension available')

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    main()