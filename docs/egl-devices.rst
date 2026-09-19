EGL devices
===========

``OpenGL.EGL.devices`` reports the EGL devices a system offers: which exist, what each advertises, what its driver calls itself, and whether it rasterises on the CPU. That is what a program needs before it can render without a display server — ``EGL_EXT_device_enumeration`` lets a program render on a device it names, which is how offscreen and headless rendering is done on EGL.

Getting from "the extension exists" to "this handle is the one I want" takes three separate extensions and a pair of string queries, so this module does it once.

::

   from OpenGL.EGL import devices

   for device in devices.devices():
       print(device.index, device.driver, device.software)

What it reports
---------------

``devices(query=...)``
   Every device, in the order EGL reports them, as a tuple of ``DeviceInfo``. Empty where the system cannot enumerate devices at all — no ``EGL_EXT_device_enumeration``, or none behind it. A caller that needs a display in that case falls back to ``eglGetDisplay`` with ``EGL_DEFAULT_DISPLAY``. ``query`` is the enumeration step, exposed so it can be replaced in tests.
``DeviceInfo.handle``
   The ``EGLDeviceEXT`` itself, which is what ``eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)`` takes. It is the device's identity: two ``DeviceInfo`` compare equal when they hold the same handle, whatever index each was enumerated at.
``DeviceInfo.index``
   Where it appeared in this enumeration. Useful for naming a device to a user or in an environment variable; not an identity, since another enumeration may number them differently.
``DeviceInfo.extensions``
   What the device says it supports, as a tuple. Empty where it does not answer the query, which is a device that does not implement the optional extension the query comes from rather than an error.
``DeviceInfo.driver``
   What the driver calls itself — ``EGL_DRIVER_NAME_EXT``. ``''`` where the device does not answer.
``DeviceInfo.software``
   Whether this device rasterises on the CPU. See below.

Which device is software
------------------------

The question is decided in two steps, in this order:

#. ``EGL_MESA_device_software`` among the device's extensions. Where it is present it is definitive, which is why it is checked first.
#. Otherwise the driver name, matched case-insensitively as a substring against ``SOFTWARE_DRIVER_NAMES``: ``llvmpipe``, ``swrast``, ``softpipe``, ``swr``, ``lavapipe``. Substrings because drivers append versions and build details to the name.

A device that answers neither is reported as hardware. That is the safer answer: treating a real GPU as software costs performance, while the reverse can mean selecting a device that cannot do the work.

The question is not cosmetic. Asking Mesa for a display on a *hardware* device while ``LIBGL_ALWAYS_SOFTWARE`` demands software rendering is a contradiction it warns about and then crashes on, inside ``driCreateNewScreen3``. A caller that can ask which devices are software avoids it; one that cannot, and takes device 0, dumps core on any machine that has both a GPU and a software rasteriser.

Choosing is the caller's
------------------------

This module reports fact. *Choosing* between the devices is policy and stays with the caller, because a renderer wanting speed and a test wanting reproducibility disagree about which device is right.

A policy has one hard constraint, which is the crash above: where the environment demands software rendering, the device chosen has to be a software one. So read that first and let it decide which kind to look for, rather than preferring hardware and hoping.

::

   import os

   from OpenGL.EGL import devices
   from OpenGL.EGL.EXT.platform_base import eglGetPlatformDisplayEXT
   from OpenGL.EGL.EXT.platform_device import EGL_PLATFORM_DEVICE_EXT

   available = devices.devices()
   # Mesa reads the variable as set-or-not, so read it the same way.
   software = os.environ.get('LIBGL_ALWAYS_SOFTWARE', '').lower() not in (
       '', '0', 'false', 'no', 'off'
   )
   wanted = [device for device in available if device.software == software]
   if not wanted and software:
       raise RuntimeError(
           'software rendering was demanded and there is no software device: %s'
           % (available,)
       )
   chosen = (wanted or available)[0]

   display = eglGetPlatformDisplayEXT(
       EGL_PLATFORM_DEVICE_EXT, chosen.handle, None
   )

The fallback runs one way only. Wanting a GPU and finding a CPU rasteriser is slow, so it renders; wanting software and finding a GPU is the pair that dumps core, so it stops.

`OpenGLContext <https://github.com/mcfletch/openglcontext>`__'s offscreen backend is a worked example of the policy half: it honours ``LIBGL_ALWAYS_SOFTWARE`` and ``GALLIUM_DRIVER``, takes an explicit device index from an environment variable where a run has to be pinned to one GPU of several, and refuses the contradiction rather than serving it. PyOpenGL's own headless test backend (``tests/glcontext_egl.py``) is the same policy at a smaller size.

Where this works
----------------

EGL is the GL binding on Linux and Android. Windows has no EGL of its own — an installed ANGLE or Mesa provides one — and macOS has none at all. ``devices()`` answers with an empty tuple wherever the enumeration extension is absent, so the empty answer is the signal to fall back.

Having no EGL *library* is a step earlier than that, and it is common: EGL ships with the graphics driver, so a machine with none installed — a virtual machine, a container, a build runner — has nothing for the bindings to call, as macOS and a Windows without ANGLE have nothing. Importing raises ``ImportError`` there, naming what is missing. That import is how a program asks whether this machine has EGL at all:

::

   try:
       from OpenGL.EGL import devices
   except ImportError:
       devices = None      # no EGL here: render through GLX, WGL or CGL instead
