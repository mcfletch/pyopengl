#! /usr/bin/env python3
"""Headless EGL-device backend for :class:`glcontext.ContextTestCase`.

Creates contexts directly on an EGL device (the GPU) with a pbuffer surface and
no window system at all -- the right path for containers / CI where the on-screen
compositor is software-rendered (llvmpipe) but the real GPU is reachable via the
``EGL_EXT_platform_device`` extension.  It serves both desktop OpenGL and
OpenGL-ES, honouring ``api`` / ``profile`` / ``gl_version`` / the
colour-depth-stencil sizes; a context the driver will not provide skips the test.

Selected with ``TEST_WINDOWING=egl``.  ``conftest.py`` forces
``PYOPENGL_PLATFORM=egl`` for that case so the GL entry points load through EGL.
A GPU is used where there is one; ``LIBGL_ALWAYS_SOFTWARE=1`` asks for the
software device instead, which is how a run reproduces what a CI runner with no
GPU renders.  ``TEST_EGL_DEVICE=<index>`` pins one device outright.

There is no window, so this backend is always headless: ``visible`` is forced
False and the inter-test dwell is skipped.
"""

from __future__ import print_function

import os
import logging

from OpenGL.EGL import (
    EGLint,
    EGLConfig,
    EGL_NONE,
    EGL_NO_CONTEXT,
    EGL_NO_SURFACE,
    EGL_NO_DISPLAY,
    EGL_HEIGHT,
    EGL_WIDTH,
    EGL_SURFACE_TYPE,
    EGL_PBUFFER_BIT,
    EGL_RENDERABLE_TYPE,
    EGL_OPENGL_BIT,
    EGL_OPENGL_ES2_BIT,
    EGL_OPENGL_ES3_BIT,
    EGL_OPENGL_API,
    EGL_OPENGL_ES_API,
    EGL_RED_SIZE,
    EGL_GREEN_SIZE,
    EGL_BLUE_SIZE,
    EGL_ALPHA_SIZE,
    EGL_DEPTH_SIZE,
    EGL_STENCIL_SIZE,
    EGL_CONTEXT_MAJOR_VERSION,
    EGL_CONTEXT_MINOR_VERSION,
    EGL_CONTEXT_OPENGL_PROFILE_MASK,
    EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,
    EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT,
    EGL_CONTEXT_OPENGL_DEBUG,
    EGL_TRUE,
    eglInitialize,
    eglChooseConfig,
    eglBindAPI,
    eglCreateContext,
    eglCreatePbufferSurface,
    eglMakeCurrent,
    eglDestroyContext,
    eglDestroySurface,
    eglQueryString,
    EGL_VENDOR,
)
from OpenGL.raw.EGL._errors import EGLError
from OpenGL.EGL.EXT.platform_base import eglGetPlatformDisplayEXT
from OpenGL.EGL.EXT.platform_device import EGL_PLATFORM_DEVICE_EXT
from OpenGL.EGL.devices import devices as enumerate_devices

log = logging.getLogger(__name__)

_ES_APIS = ('gles', 'es')

#: Values Mesa reads as "no" in a boolean environment variable.  An unset
#: variable and an empty one agree, which is what an unexported shell variable
#: expands to.
_FALSE_VALUES = frozenset(('', '0', 'false', 'no', 'n', 'f', 'off'))

#: ``GALLIUM_DRIVER`` values that name a CPU rasteriser.
_SOFTWARE_DRIVERS = frozenset(('llvmpipe', 'softpipe', 'swr', 'swrast', 'lavapipe'))

#: cached (display) once initialised -- the device display is reused per test.
_display = None


class NoSuitableDevice(RuntimeError):
    """No EGL device can serve what the environment asked for."""


def software_forced(env=None):
    """Whether the environment asks for CPU rasterisation.

    ``LIBGL_ALWAYS_SOFTWARE`` is read the way Mesa itself reads it, because the
    point of asking is to predict what Mesa will do with the display this
    backend hands it.  ``GALLIUM_DRIVER`` naming a CPU rasteriser counts as the
    same request: it does not reach the device path by itself, so a run that
    pinned llvmpipe that way and was given the GPU would be measuring something
    it did not ask for.
    """
    env = os.environ if env is None else env
    if env.get('LIBGL_ALWAYS_SOFTWARE', '').strip().lower() not in _FALSE_VALUES:
        return True
    return env.get('GALLIUM_DRIVER', '').strip().lower() in _SOFTWARE_DRIVERS


def pick_device(found, env=None):
    """Choose which of ``found`` to render on, or say why none will do.

    A GPU is preferred, since that is what the suite is usually here to
    exercise.  ``LIBGL_ALWAYS_SOFTWARE`` reverses that and selects the software
    device: the two settings must agree, because Mesa will not force software
    rasterisation onto a display built on a hardware device and crashes in
    ``eglInitialize`` rather than refusing it.  ``TEST_EGL_DEVICE`` pins an
    index, and is held to the same agreement for the same reason.
    """
    env = os.environ if env is None else env
    software = software_forced(env)
    pinned = env.get('TEST_EGL_DEVICE')

    if pinned is not None:
        try:
            device = found[int(pinned)]
        except (ValueError, IndexError):
            raise NoSuitableDevice(
                'TEST_EGL_DEVICE=%r does not name one of the %d EGL devices'
                % (pinned, len(found))
            ) from None
        if software and not device.software:
            raise NoSuitableDevice(
                'TEST_EGL_DEVICE=%s names %r, but LIBGL_ALWAYS_SOFTWARE asks for '
                'software rendering, and Mesa crashes rather than forcing it onto '
                'a hardware device.  Drop one of the two settings.' % (pinned, device)
            )
        return device

    if not found:
        raise NoSuitableDevice('EGL reports no devices to render on')

    wanted = [device for device in found if device.software == software]
    if wanted:
        return wanted[0]
    if software:
        raise NoSuitableDevice(
            'LIBGL_ALWAYS_SOFTWARE asks for software rendering and EGL reports no '
            'software device (%s).  Mesa crashes rather than forcing it onto a '
            'hardware device, so unset the variable to use one of these.'
            % ', '.join(repr(device) for device in found)
        )
    # Only software devices: that is the whole offer, and nothing contradicts it.
    return found[0]


def _ensure_display():
    global _display
    if _display is None:
        device = pick_device(enumerate_devices())
        display = eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, device.handle, None)
        if display == EGL_NO_DISPLAY:
            raise RuntimeError('eglGetPlatformDisplayEXT returned EGL_NO_DISPLAY')
        major, minor = EGLint(), EGLint()
        if not eglInitialize(display, major, minor):
            raise RuntimeError('eglInitialize failed for the EGL device display')
        vendor = eglQueryString(display, EGL_VENDOR)
        log.info(
            'EGL device backend: %r, EGL %d.%d, vendor=%r',
            device, major.value, minor.value, vendor,
        )
        _display = display
    return _display


def _attrib_array(pairs):
    flat = []
    for key, value in pairs:
        flat.extend((key, value))
    flat.append(EGL_NONE)
    return (EGLint * len(flat))(*flat)


class EGLDeviceBackend(object):
    """Mixin supplying headless EGL-device context creation (desktop GL or ES)."""

    backend_name = 'egl'

    #: there is no window, so this backend is always headless.
    visible = False

    _egl_context = None
    _egl_surface = None

    def _create_context(self):
        display = _ensure_display()
        api = getattr(self, 'api', 'gl').lower()
        major, minor = self.gl_version

        if api in _ES_APIS:
            eglBindAPI(EGL_OPENGL_ES_API)
            renderable = EGL_OPENGL_ES3_BIT if major >= 3 else EGL_OPENGL_ES2_BIT
        else:
            eglBindAPI(EGL_OPENGL_API)
            renderable = EGL_OPENGL_BIT

        config_attrs = _attrib_array([
            (EGL_SURFACE_TYPE, EGL_PBUFFER_BIT),
            (EGL_RENDERABLE_TYPE, renderable),
            (EGL_RED_SIZE, self.red_size),
            (EGL_GREEN_SIZE, self.green_size),
            (EGL_BLUE_SIZE, self.blue_size),
            (EGL_ALPHA_SIZE, self.alpha_size),
            (EGL_DEPTH_SIZE, self.depth_size),
            (EGL_STENCIL_SIZE, self.stencil_size),
        ])
        config = (EGLConfig * 1)()
        num_config = EGLint()
        if not eglChooseConfig(display, config_attrs, config, 1, num_config) or num_config.value < 1:
            self.skipTest(
                'No EGL pbuffer config for %s %d.%d with the requested buffer sizes'
                % (api, major, minor)
            )

        context_pairs = [
            (EGL_CONTEXT_MAJOR_VERSION, major),
            (EGL_CONTEXT_MINOR_VERSION, minor),
        ]
        # GL profiles only exist for desktop GL >= 3.2.
        if api not in _ES_APIS and (major, minor) >= (3, 2):
            profile = getattr(self, 'profile', 'compatibility').lower()
            context_pairs.append((
                EGL_CONTEXT_OPENGL_PROFILE_MASK,
                EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT
                if profile == 'core'
                else EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT,
            ))
        if getattr(self, 'debug_context', False):
            context_pairs.append((EGL_CONTEXT_OPENGL_DEBUG, EGL_TRUE))
        context_attrs = _attrib_array(context_pairs)

        # A request the driver will not serve is EGL_BAD_MATCH or
        # EGL_BAD_ATTRIBUTE, which PyOpenGL's error checking raises rather than
        # returning -- so the EGL_NO_CONTEXT check below never sees it.  Both
        # mean the same thing here: this machine has no such context, which is
        # a skip and not a failure.
        try:
            context = eglCreateContext(
                display, config[0], EGL_NO_CONTEXT, context_attrs)
        except EGLError as err:
            context = EGL_NO_CONTEXT
            reason = str(err.err)
        else:
            reason = 'the driver returned EGL_NO_CONTEXT'
        if context == EGL_NO_CONTEXT:
            self.skipTest(
                'No EGL %s %d.%d context on this device: %s'
                % (api, major, minor, reason)
            )

        surface = eglCreatePbufferSurface(
            display, config[0],
            _attrib_array([(EGL_WIDTH, self.width), (EGL_HEIGHT, self.height)]),
        )
        if surface == EGL_NO_SURFACE:
            eglDestroyContext(display, context)
            self.skipTest('Could not create a %dx%d EGL pbuffer' % (self.width, self.height))

        if not eglMakeCurrent(display, surface, surface, context):
            eglDestroySurface(display, surface)
            eglDestroyContext(display, context)
            self.skipTest('eglMakeCurrent failed for the EGL device context')

        self._egl_context = context
        self._egl_surface = surface

    def _swap(self):
        # Offscreen pbuffer: nothing to present.  Tests read back with
        # glReadPixels, which implicitly finishes the pipeline.
        pass

    def _make_current(self):
        if self._egl_context is None:
            raise RuntimeError('this backend has no context to make current')
        display = _ensure_display()
        if not eglMakeCurrent(
            display, self._egl_surface, self._egl_surface, self._egl_context
        ):
            raise RuntimeError('eglMakeCurrent failed for this context')

    def _destroy_context(self):
        display = _display
        if display is None:
            return
        eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)
        if self._egl_surface is not None:
            eglDestroySurface(display, self._egl_surface)
            self._egl_surface = None
        if self._egl_context is not None:
            eglDestroyContext(display, self._egl_context)
            self._egl_context = None
