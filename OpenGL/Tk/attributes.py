"""What a caller asks a Tk OpenGL context for.

One object, so a request can be written down, passed around and compared, and
so each platform has one thing to translate rather than a signature to keep in
step with two others.  What each platform does with it is
:mod:`OpenGL.Tk.glx` and :mod:`OpenGL.Tk.win32`.

Nothing here touches Tk, a display or a driver, which is the point: a wrong
constant in an attribute list produces "could not create a context" and no
other evidence, so the lists are worth being able to look at without one.
"""

from __future__ import annotations

from typing import Optional, Tuple

__all__ = ['PROFILES', 'ContextAttributes']

#: The profiles a context may be asked for.
#:
#: ``core`` is OpenGL 3.2 and above with the fixed-function pipeline removed --
#: shaders, vertex array objects, and what everything written since 2008 uses.
#: ``compatibility`` is the same era with the old pipeline still present, which
#: is what the fixed-function widgets in :mod:`OpenGL.Tk.togl` need.
#: ``legacy`` asks for no version and no profile at all: the driver is left to
#: choose, through the entry point that predates the choice existing, which is
#: the only thing a driver without ``ARB_create_context`` will answer.
PROFILES = ('core', 'compatibility', 'legacy')

#: The version asked for when a caller names a profile but no version.  The
#: floor for a core profile is 3.2; 3.3 is where the shading language stopped
#: moving in ways that matter and is what shaders are written against.
DEFAULT_VERSION = (3, 3)

#: Bits per colour channel asked for when nothing says otherwise.
DEFAULT_COLOUR_SIZE = 8

#: Depth bits asked for when nothing says otherwise.  A 16-bit depth buffer is
#: visibly short on any scene deeper than a few metres.
DEFAULT_DEPTH_SIZE = 24

#: The first version that has profiles to choose between.  Below it there is no
#: profile mask to send, and a driver handed one refuses the whole request --
#: which is how "core 2.1", a thing that does not exist, comes back as an X
#: ``BadValue`` rather than as a context.
PROFILE_FLOOR = (3, 2)

#: The first version that can be asked to leave out what it has deprecated.
FORWARD_COMPATIBLE_FLOOR = (3, 0)


class ContextAttributes(object):
    """The description of a GL context a widget is to be given

    profile -- one of :data:`PROFILES`
    version -- ``(major, minor)`` to ask for, or ``None`` to leave it to the
        driver.  A ``legacy`` profile forces ``None``, since the entry point
        that creates one takes no version.
    doubleBuffer -- whether to draw into a back buffer and swap
    redSize, greenSize, blueSize -- bits per colour channel
    alphaSize -- bits of destination alpha.  Zero unless asked for: a
        compositor that honours it treats cleared pixels as transparent, so a
        window with an alpha channel shows what is behind it.
    depthSize, stencilSize -- bits of depth and stencil
    samples -- multisample samples per pixel, or 0 for none
    stereo -- whether to ask for a stereo pair of colour buffers
    debug -- whether to ask for a debug context, which is what makes
        ``GL_KHR_debug`` report anything
    forwardCompatible -- whether the context may not offer anything deprecated.
        Defaults to true for a core profile and false otherwise, which is what
        each of those means; naming it outranks the default.
    share -- a context to share display lists, textures and buffers with, or
        None
    """

    __slots__ = (
        'profile', 'version', 'doubleBuffer',
        'redSize', 'greenSize', 'blueSize', 'alphaSize',
        'depthSize', 'stencilSize', 'samples', 'stereo', 'debug',
        'forwardCompatible', 'share',
    )

    def __init__(
        self,
        profile: str = 'core',
        version: Optional[Tuple[int, int]] = DEFAULT_VERSION,
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

    #: The constructor's own parameters, so a widget can take them among its
    #: Tk options and hand the right ones on; see
    #: :meth:`OpenGL.Tk.widget.GLFrame.__init__`.
    KEYWORDS = tuple(name for name in __slots__)

    def __repr__(self) -> str:
        return '%s(profile=%r, version=%r, doubleBuffer=%r, depthSize=%r)' % (
            self.__class__.__name__, self.profile, self.version,
            self.doubleBuffer, self.depthSize,
        )

    def profileApplies(self) -> bool:
        """Whether this request has a profile to name

        A profile is a GL 3.2 idea.  Asked for a version below that, a driver
        refuses the request outright rather than ignoring the part of it that
        means nothing -- so "core 2.1" has to come out as a plain 2.1 context,
        which is what every windowing toolkit gives for it.
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
