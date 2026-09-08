#! /usr/bin/env python
"""Whether a windowless OpenGL context can be made on this Windows machine.

Run it to find out whether ``TEST_WINDOWING=wgl`` has anything to render on --
the first thing to ask when the suite skips every GL case on Windows::

    python tests/check_wgl_offscreen.py

It exits non-zero when no context can be created, so a CI job can use it as a
gate: a suite with no GL target skips its way to green having drawn nothing,
which reads the same as a pass.

**A machine with no GL driver installed still has an OpenGL.** Windows falls
back to its own GDI Generic implementation, which is OpenGL 1.1 and offers
neither ``WGL_ARB_pbuffer`` nor ``WGL_ARB_create_context`` -- so it can serve
no windowless context at all, and the extensions it lacks are named below
rather than left to be inferred from a run in which everything skipped.
"""

import os
import sys

#: The checkout this script is part of, ahead of whatever else is on the path.
#:
#: A script's ``sys.path`` starts at its own directory rather than at the one
#: it was run from, so an installation reached through a finder -- what an
#: editable install is -- can be shadowed here by a directory named ``OpenGL``
#: that holds no ``__init__.py``.  The suite does not meet that, being run as
#: ``python -m pytest`` from the checkout, which puts the checkout on the path
#: for it.  This says the same thing for itself.
#:
#: Named only where it is a checkout, so that running this beside an installed
#: PyOpenGL still asks about the installed one.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(_ROOT, 'OpenGL', '__init__.py')):
    sys.path.insert(0, _ROOT)

from OpenGL.WGL import offscreen


#: The profiles a run might ask for, and the GL version each names.  'legacy'
#: is what a request below GL 3.2 gets, the profile mask having arrived there.
PROFILES = (
    ('legacy', (1, 1)),
    ('compatibility', (3, 3)),
    ('core', (3, 3)),
)


def main():
    if sys.platform not in ('win32', 'cygwin'):
        print('WGL is Windows only; this platform is %s' % (sys.platform,))
        return 1

    try:
        extensions = offscreen.wgl_extensions()
    except Exception as err:                   # no GL library, no bootstrap
        print('no WGL here: %s' % (err,))
        return 1
    print('%d WGL extensions' % (len(extensions),))

    missing = offscreen.available('core')
    if missing:
        # Named rather than counted: which of the three is absent says what
        # kind of machine this is -- the GDI Generic fallback has none of them,
        # a driver too old for core profile has only the last.
        print('no windowless GL: %s missing' % (', '.join(sorted(missing)),))
        return 1

    from OpenGL.GL import GL_RENDERER, GL_VENDOR, GL_VERSION, glGetString

    made = 0
    for profile, version in PROFILES:
        try:
            context = offscreen.OffscreenContext(
                width=64, height=64, profile=profile, version=version,
            )
        except Exception as err:               # a driver-specific refusal
            print('%-13s unavailable: %s' % (profile, err))
            continue
        try:
            context.make_current()
            print('%-13s %s | %s | %s' % (
                profile,
                glGetString(GL_VENDOR).decode(),
                glGetString(GL_RENDERER).decode(),
                glGetString(GL_VERSION).decode(),
            ))
            made += 1
        finally:
            context.release()
    # The suite asks for core and for compatibility, so a machine that can
    # serve neither has nothing for it to run on however many extensions it
    # advertised.
    return 0 if made else 1


if __name__ == '__main__':
    sys.exit(main())
