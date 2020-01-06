from __future__ import print_function
import os, logging, pprint

log = logging.getLogger(__name__)
if not os.environ.get("PYOPENGL_PLATFORM"):
    os.environ["PYOPENGL_PLATFORM"] = "egl"
if "DISPLAY" in os.environ:
    del os.environ["DISPLAY"]
import logging, contextlib
from functools import wraps

# from OpenGL.GL import *
from OpenGL.EGL import *
from OpenGL.EGL import debug
from OpenGL import arrays
from OpenGL.EGL import gbmdevice
from OpenGL.EGL.MESA import platform_gbm
from OpenGL.EGL.EXT import platform_device, platform_base, device_base

API_MAP = {
    EGL_OPENGL_BIT: EGL_OPENGL_API,
    EGL_OPENGL_ES2_BIT: EGL_OPENGL_ES_API,
    EGL_OPENGL_ES_BIT: EGL_OPENGL_ES_API,
}


def platformDisplay(device):
    """Get platform display from device specifier
    
    device -- EGLDeviceEXT, gbm card* path, or gbm card* ordinal (index)

    returns display, created_device (or None if passed in)
    raises RuntimeError if we can't create the display
    """
    created_device = display = None
    if isinstance(device, (str, int)):
        created_device = device = gbmdevice.open_device(device)
    if eglGetPlatformDisplay:
        display = eglGetPlatformDisplay(
            platform_device.EGL_PLATFORM_DEVICE_EXT
            if isinstance(device, EGLDeviceEXT)
            else platform_gbm.EGL_PLATFORM_GBM_MESA,
            device,
            ctypes.c_void_p(0),
        )
        if display == EGL_NO_DISPLAY:
            raise RuntimeError("Unable to create EGL display on %s" % (display))
    else:
        raise RuntimeError("eglGetPlatformDisplay has no implementation")
    if not created_device:
        try:
            name = get_device_name(device)
            if name is not None:
                log.debug("DRM Name: %s", name)
        except EGLError:
            log.debug("Unable to retrieve the DRM name")
    return display, created_device


def gbmPlatformSurface(display, config, platform_device, width, height):
    """Create a GBM platform surface for display with config on platform_device
    
    returns egl_surface, gbm_surface
    """
    visual = EGLint()
    eglGetConfigAttrib(display, config, EGL_NATIVE_VISUAL_ID, visual)
    platform_surface = gbmdevice.create_surface(
        platform_device,
        width,
        height,
        format=visual.value,
        flags=gbmdevice.GBM_BO_USE_RENDERING,
    )
    if not platform_surface:
        raise RuntimeError("Unable to allocate a gbm surface")
    surface = eglCreatePlatformWindowSurface(display, config, platform_surface, None)
    if surface == EGL_NO_SURFACE:
        log.error("Failed to create the EGL surface on the GBM surface")
        raise RuntimeError("Platform window surface creation failure")
    return surface, platform_surface


def choose_config(display, attributes):
    """utility to choose config for the display based on attributes"""
    num_configs = EGLint()
    configs = (EGLConfig * 1)()
    local_attributes = arrays.GLintArray.asArray(attributes)
    success = eglChooseConfig(display, local_attributes, configs, 1, num_configs)
    if not success:
        raise NoConfig("Unable to complete config filtering", attributes)
    if not num_configs:
        raise NoConfig(
            "No compatible configs found", attributes,
        )
    return configs[0]


@contextlib.contextmanager
def egl_context(
    width=256,
    height=256,
    api=EGL_OPENGL_BIT,
    attributes=(
        EGL_BLUE_SIZE,
        8,
        EGL_RED_SIZE,
        8,
        EGL_GREEN_SIZE,
        8,
        EGL_DEPTH_SIZE,
        24,
        EGL_COLOR_BUFFER_TYPE,
        EGL_RGB_BUFFER,
        # EGL_CONFIG_CAVEAT, EGL_NONE, # Don't allow slow/non-conformant
    ),
    pbuffer=False,
    device=None,
    output="output.ppm",
):
    """Setup a context for rendering"""
    major, minor = EGLint(), EGLint()
    created_device = platform_surface = surface = None
    if device is None:
        display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
        if display == EGL_NO_DISPLAY:
            raise RuntimeError(EGL_NO_DISPLAY, "Could not create default display")
    else:
        display, created_device = platformDisplay(device)
    try:
        # print("Display: %s"%(display.address,))
        try:
            eglInitialize(display, major, minor)
        except EGLError as err:
            log.warning("eglInitilise failure on %s: %s", display, err.err)
            raise NoEGLSupport(display)
        log.debug(
            "Available configs:\n%s",
            debug.format_debug_configs(debug.debug_configs(display)),
        )

        # for config in configs[:num_configs.value]:
        #     log.debug("Config: %s",pprint.pformat(debug.debug_config(display,config)))
        local_attributes = list(attributes[:])
        if pbuffer:
            local_attributes.extend(
                [EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,]
            )
        else:
            local_attributes.extend(
                [EGL_SURFACE_TYPE, EGL_WINDOW_BIT,]
            )
        local_attributes.extend(
            [EGL_CONFORMANT, api, EGL_NONE,]  # end of list
        )
        config = choose_config(display, local_attributes,)
        log.debug(
            "Selected config:\n%s",
            debug.format_debug_configs(debug.debug_configs(display, configs=[config])),
        )
        surface_attributes = [
            EGL_WIDTH,
            width,
            EGL_HEIGHT,
            height,
            EGL_NONE,
        ]
        if pbuffer:
            surface = eglCreatePbufferSurface(display, config, surface_attributes,)
        else:
            surface, platform_surface = gbmPlatformSurface(
                display, config, created_device, width, height
            )
        eglBindAPI(API_MAP[api])
        ctx = eglCreateContext(display, config, EGL_NO_CONTEXT, None)
        if ctx == EGL_NO_CONTEXT:
            raise RuntimeError("Unable to create context")
        eglMakeCurrent(display, surface, surface, ctx)
        yield display, ctx, surface
        if output:
            log.debug("Doing readpixels for writing buffer")
            from OpenGL import arrays

            content = arrays.GLubyteArray.zeros((width, height, 3))
            if api == EGL_OPENGL_BIT:
                from OpenGL.GL import glReadPixels, GL_UNSIGNED_BYTE, GL_RGB
            elif api == EGL_OPENGL_ES3_BIT:
                from OpenGL.GLES3 import glReadPixels, GL_UNSIGNED_BYTE, GL_RGB
            elif api == EGL_OPENGL_ES2_BIT:
                from OpenGL.GLES2 import glReadPixels, GL_UNSIGNED_BYTE, GL_RGB
            elif api == EGL_OPENGL_ES_BIT:
                from OpenGL.GLES1 import glReadPixels, GL_UNSIGNED_BYTE, GL_RGB
            content = glReadPixels(
                0, 0, width, height, GL_RGB, type=GL_UNSIGNED_BYTE, array=content
            )

            debug.write_ppm(content, output)
            # glFinish()
    finally:
        if display:
            eglMakeCurrent(display, None, None, None)
            if surface:
                eglDestroySurface(display, surface)
            eglTerminate(display)
        if platform_surface:
            gbmdevice.gbm.gbm_surface_destroy(platform_surface)
        if created_device:
            gbmdevice.close_device(created_device)


class NoEGLSupport(Exception):
    """Raised if we could not initialise an egl context"""


class NoConfig(Exception):
    """Raised if we did not find any configs"""


def debug_info(setup):
    from OpenGL.GL import (
        glClearColor,
        glClear,
        GL_COLOR_BUFFER_BIT,
        GL_DEPTH_BUFFER_BIT,
        glGetString,
        GL_VENDOR,
        GL_EXTENSIONS,
        GL_VERSION,
        glFinish,
    )

    display, ctx, surface = setup
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    log.info("Vendor: %s", glGetString(GL_VENDOR))
    log.info("Vendor: %s", glGetString(GL_VERSION))
    log.info("Extensions: %s", glGetString(GL_EXTENSIONS))
    glFinish()

def get_device_name(device):
    """Try to get the display's DRM device name

    This is almost certainly not going to work on
    anything other than Linux
    """
    from OpenGL.EGL.EXT.device_query import (
        eglQueryDeviceStringEXT,
    )
    from OpenGL.EGL.EXT.device_drm import (
        EGL_DRM_DEVICE_FILE_EXT,
    )
    if eglQueryDeviceStringEXT:
        name = eglQueryDeviceStringEXT(
            device,
            EGL_DRM_DEVICE_FILE_EXT
        )
        return name.decode('ascii',errors='ignore')
    return None


def main():
    # NOTE: having two different implementations here is
    # likely somewhat broken due to the
    # OpenGL functions having retrieved their
    # function pointers during the first pass and then
    # trying to run them against the second
    for device in sorted(device_base.egl_get_devices(), key=lambda x: x.address):
        log.info("Starting tests with: %s", device)
        try:
            with egl_context(device=device, pbuffer=True) as setup:
                debug_info(setup)
        except (NoEGLSupport, NoConfig) as err:
            log.info("Cannot configure: %s", err)
        except (EGLError, RuntimeError):
            log.exception("Failed during: %s", device)
    for device in gbmdevice.enumerate_devices():
        log.info("Starting tests with: %s", device)
        try:
            with egl_context(device=device, pbuffer=False) as setup:
                debug_info(setup)
        except (NoEGLSupport, NoConfig) as err:
            log.info("Cannot configure: %s", err)
        except (EGLError, RuntimeError):
            log.exception("Failed during: %s", device)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
