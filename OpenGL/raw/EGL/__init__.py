# mypy: ignore-errors
# The names in this package arrive from the declaration tables at import
# time, so a checker reading it sees calls to things it cannot find.  The
# typed surface is the .pyi stub beside the package.
"""Raw EGL declarations

Every name here is one an EGL library provides, so there is nothing to declare
where the platform has none: win32 and darwin offer no EGL interface at all and
so carry no attribute for it, and the platforms that go looking leave it None
when nothing is installed.  Neither is an error until something asks for the
bindings, which is here.  It is an ImportError because that is what it is, and
because ``try: from OpenGL import EGL`` is how a program asks whether this
machine has EGL.
"""
from OpenGL import platform as _p

if getattr(_p.PLATFORM, 'EGL', None) is None:
    raise ImportError(
        'PyOpenGL found no EGL library to bind to on this platform. EGL ships '
        'with the graphics driver: install one (libegl1 or libglvnd on Linux) '
        'to use OpenGL.EGL'
    )
