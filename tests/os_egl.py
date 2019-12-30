from __future__ import print_function
import os, logging, pprint, ipdb

log = logging.getLogger(__name__)
if not os.environ.get("PYOPENGL_PLATFORM"):
    os.environ["PYOPENGL_PLATFORM"] = "egl"
if "DISPLAY" in os.environ:
    del os.environ["DISPLAY"]
import logging, contextlib
from functools import wraps
from OpenGL.GL import *
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


def write_ppm(buf, filename):
    f = open(filename, "w")
    if f:
        h, w, c = buf.shape
        print("P3", file=f)
        print("# ascii ppm file created by os_egl", file=f)
        print("%i %i" % (w, h), file=f)
        print("255", file=f)
        for y in range(h - 1, -1, -1):
            for x in range(w):
                pixel = buf[y, x]
                l = " %3d %3d %3d" % (pixel[0], pixel[1], pixel[2])
                f.write(l)
            f.write("\n")


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
    return display, created_device


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
    major, minor = GLint(), GLint()
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
        except GLError as err:
            err.err = debug.eglErrorName(err.err)
            log.warning("eglInitilise failure on %s: %s", display, err.err)
            raise NoEGLSupport(display)
        num_configs = GLint()
        configs = (EGLConfig * 1)()
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
        log.debug("Attributes: %s", local_attributes)
        local_attributes = arrays.GLintArray.asArray(local_attributes)
        try:
            success = eglChooseConfig(
                display, local_attributes, configs, 1, num_configs
            )
            if not success:
                raise RuntimeError("Unable to complete config filtering")
            if not num_configs:
                configs = (EGLConfig * 10)()
                eglGetConfigs(display, configs, 10, num_configs)
                if num_configs.value:
                    for config in configs[: num_configs.value]:
                        log.warning(
                            "Unused config: %s",
                            pprint.pformat(debug.debug_config(display, config)),
                        )
                raise RuntimeError(
                    "No compatible configs found on %s" % (device or "default")
                )
            # for config in configs[:num_configs.value]:
            #     log.debug("Config: %s",pprint.pformat(debug.debug_config(display,config)))
            config = configs[0]
            log.debug(
                "Selecting config: %s",
                pprint.pformat(debug.debug_config(display, config)),
            )
            surface_attributes = [
                EGL_WIDTH,
                width,
                EGL_HEIGHT,
                height,
                EGL_NONE,
            ]
            if pbuffer:
                surface = eglCreatePbufferSurface(
                    display, configs[0], surface_attributes,
                )
            else:
                visual = EGLint()
                eglGetConfigAttrib(display, configs[0], EGL_NATIVE_VISUAL_ID, visual)
                log.debug("Native visual id %s", visual.value)
                platform_surface = gbmdevice.create_surface(
                    created_device,
                    width,
                    height,
                    format=visual.value,
                    flags=gbmdevice.GBM_BO_USE_RENDERING,
                )
                log.debug("Native surface created on %s", device)
                if not platform_surface:
                    raise RuntimeError("Unable to allocate a gbm surface")
                log.debug("Creating GBM platform window surface")
                surface = eglCreatePlatformWindowSurface(
                    display, configs[0], platform_surface, None
                )
                if surface == EGL_NO_SURFACE:
                    raise RuntimeError("Platform window surface creation failure")
        except GLError as err:
            err.err = debug.eglErrorName(err.err)
            raise
        log.debug("Binding api %s", api)
        eglBindAPI(API_MAP[api])
        ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
        if ctx == EGL_NO_CONTEXT:
            raise RuntimeError("Unable to create context")
        eglMakeCurrent(display, surface, surface, ctx)
        log.debug("Yielding to caller")
        yield display, ctx, surface
        log.debug("Doing context cleanup")
        if not pbuffer:
            # This crashes on my intel i915 device, as do glFlush and glFinish
            eglSwapBuffers(display, surface)
        else:
            glFinish()
        if output:
            log.debug("Doing readpixels for writing buffer")
            content = glReadPixelsub(0, 0, width, height, GL_RGB, outputType=None,)
            write_ppm(content, output)
            # glFinish()
    finally:
        if display:
            log.debug("Unsetting current")
            eglMakeCurrent(display, None, None, None)
            if surface:
                eglDestroySurface(display, surface)
            log.debug("Terminating display")
            eglTerminate(display)
        if platform_surface:
            log.debug("Cleaning up gbm surface")
            gbmdevice.gbm.gbm_surface_destroy(platform_surface)
        if created_device:
            log.debug("Closing gbm device")
            gbmdevice.close_device(created_device)


class NoEGLSupport(Exception):
    """Raised if we could not initialise an egl context"""


def debug_info(setup):
    display, ctx, surface = setup
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    log.info("Vendor: %s", glGetString(GL_VENDOR))
    log.info("Extensions: %s", glGetString(GL_EXTENSIONS))
    glFinish()


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
        except (NoEGLSupport):
            pass
        except (GLError, RuntimeError):
            log.exception("Failed during: %s", device)
    for device in gbmdevice.enumerate_devices():
        log.info("Starting tests with: %s", device)
        try:
            with egl_context(device=device, pbuffer=False) as setup:
                debug_info(setup)
        except (NoEGLSupport):
            pass
        except (GLError, RuntimeError):
            log.exception("Failed during: %s", device)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
