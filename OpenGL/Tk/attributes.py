"""The attributes requested for a Tk OpenGL context.

A request is a single object, so it can be stored, passed around and compared.
Each platform translates that one object into its own attribute list; see
:mod:`OpenGL.Tk.glx` and :mod:`OpenGL.Tk.win32`.

This module does not use Tk, a display or a driver.  A wrong constant in an
attribute list only produces "could not create a context", so the lists can be
built and inspected here without a display.
"""

from __future__ import annotations

from typing import Optional

__all__ = ['PROFILES', 'ContextAttributes']

#: The profiles a context may be asked for.
#:
#: ``core`` is OpenGL 3.2 and above with the fixed-function pipeline removed.
#: It provides shaders and vertex array objects.
#: ``compatibility`` is OpenGL 3.2 and above with the fixed-function pipeline
#: still present.  The fixed-function widgets in :mod:`OpenGL.Tk.togl` need it.
#: ``legacy`` requests no version and no profile, so the driver chooses.  It uses
#: the older context-creation entry point, which is the only one available on a
#: driver without ``ARB_create_context``.
PROFILES = ('core', 'compatibility', 'legacy')

#: The version requested when a caller names a profile but no version.  The
#: minimum for a core profile is 3.2.  Most shaders are written against GLSL
#: 3.30, so 3.3 is the default.
DEFAULT_VERSION = (3, 3)

#: Bits per colour channel asked for when nothing says otherwise.
DEFAULT_COLOUR_SIZE = 8

#: Depth bits asked for when nothing says otherwise.  A 16-bit depth buffer is
#: visibly short on any scene deeper than a few metres.
DEFAULT_DEPTH_SIZE = 24

#: The first version that has profiles.  Below it there is no profile mask to
#: send, and a driver given one refuses the whole request.  Sent with a
#: profile mask, a request for "core 2.1" fails with an X ``BadValue`` error.
PROFILE_FLOOR = (3, 2)

#: The first version that can be asked to leave out what it has deprecated.
FORWARD_COMPATIBLE_FLOOR = (3, 0)


class ContextAttributes(object):
    """The description of a GL context a widget is to be given

    profile - one of :data:`PROFILES`
    version - ``(major, minor)`` to request, or ``None`` to let the driver
        choose.  A ``legacy`` profile forces ``None``, because the entry point
        that creates one takes no version.
    doubleBuffer - whether to draw into a back buffer and swap
    redSize, greenSize, blueSize - bits per colour channel
    alphaSize - bits of destination alpha, default zero.  Some compositors
        treat cleared pixels in a window with an alpha channel as transparent
        and show what is behind the window.
    depthSize, stencilSize - bits of depth and stencil
    samples - multisample samples per pixel, or 0 for none
    stereo - whether to request a stereo pair of colour buffers
    debug - whether to request a debug context.  ``GL_KHR_debug`` reports
        messages only in a debug context.
    forwardCompatible - whether the context omits deprecated functionality.
        Defaults to true for a core profile and false otherwise.  An explicit
        value overrides the default.
    share - a context to share display lists, textures and buffers with, or
        None
    swapInterval - display refreshes a buffer swap waits for, or None to use
        the platform default.  Zero swaps immediately, for benchmarks and for
        machines with no display, where a swap waiting for a refresh never
        returns.  Applied before the first frame is drawn;
        :meth:`~OpenGL.Tk.widget.GLFrame.setSwapInterval` changes it later.
    """

    __slots__ = (
        'profile', 'version', 'doubleBuffer',
        'redSize', 'greenSize', 'blueSize', 'alphaSize',
        'depthSize', 'stencilSize', 'samples', 'stereo', 'debug',
        'forwardCompatible', 'share', 'swapInterval',
    )

    def __init__(
        self,
        profile: str = 'core',
        version: Optional[tuple[int, int]] = DEFAULT_VERSION,
        doubleBuffer: bool = True,
        redSize: int = DEFAULT_COLOUR_SIZE,
        greenSize: int = DEFAULT_COLOUR_SIZE,
        blueSize: int = DEFAULT_COLOUR_SIZE,
        alphaSize: int = 0,
        depthSize: int = DEFAULT_DEPTH_SIZE,
        stencilSize: int = 0,
        samples: int = 0,
        stereo: bool = False,
        debug: bool = False,
        forwardCompatible: Optional[bool] = None,
        share: object = None,
        swapInterval: Optional[int] = None,
    ) -> None:
        if profile not in PROFILES:
            raise ValueError(
                'Unrecognised profile %r; expected one of %s'
                % (profile, ', '.join(PROFILES))
            )
        self.profile = profile
        self.version = None if profile == 'legacy' else (
            tuple(version) if version else None)
        self.doubleBuffer = bool(doubleBuffer)
        self.redSize = int(redSize)
        self.greenSize = int(greenSize)
        self.blueSize = int(blueSize)
        self.alphaSize = int(alphaSize)
        self.depthSize = int(depthSize)
        self.stencilSize = int(stencilSize)
        self.samples = int(samples)
        self.stereo = bool(stereo)
        self.debug = bool(debug)
        self.forwardCompatible = (
            profile == 'core' if forwardCompatible is None
            else bool(forwardCompatible))
        self.share = share
        self.swapInterval = None if swapInterval is None else int(swapInterval)

    #: The constructor's parameter names.  A widget uses them to separate these
    #: keywords from its Tk options; see
    #: :meth:`OpenGL.Tk.widget.GLFrame.__init__`.
    KEYWORDS = tuple(name for name in __slots__)

    def __repr__(self) -> str:
        return '%s(profile=%r, version=%r, doubleBuffer=%r, depthSize=%r)' % (
            self.__class__.__name__, self.profile, self.version,
            self.doubleBuffer, self.depthSize,
        )

    def profileApplies(self) -> bool:
        """Whether this request has a profile to name

        Profiles exist from GL 3.2.  A driver refuses a request that names a
        profile for an earlier version.  A request for "core 2.1" is therefore
        sent as a plain 2.1 request, as other windowing toolkits do.
        """
        if self.profile == 'legacy':
            return False
        return self.version is not None and tuple(self.version) >= PROFILE_FLOOR

    def forwardCompatibleApplies(self) -> bool:
        """Whether this request can ask to leave the deprecated parts out"""
        if not self.forwardCompatible:
            return False
        return (self.version is not None
                and tuple(self.version) >= FORWARD_COMPATIBLE_FLOOR)

    def describe(self) -> str:
        """A one-line description, for a log line or a failure message"""
        version = ('%d.%d' % self.version) if self.version else 'any version'
        return 'OpenGL %s %s profile, %s buffered, %d-bit depth' % (
            version, self.profile,
            'double' if self.doubleBuffer else 'single', self.depthSize,
        )
