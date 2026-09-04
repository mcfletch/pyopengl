#! /usr/bin/env python
"""Whether a headless OpenGL context can be made on this Mac, and by which renderer.

Run it to find out whether ``TEST_WINDOWING=cgl`` has anything to render on --
the first thing to ask when the suite skips every GL case on macOS::

    python tests/check_cgl_context.py

It exits non-zero when no context can be created, so a CI job can use it as a
gate: a suite with no GL target skips its way to green having drawn nothing,
which reads the same as a pass.

``TEST_CGL_RENDERER`` pins the renderer kind (``accelerated`` / ``any`` /
``software``); unset, an accelerated renderer is preferred and the CPU one is
taken where there is no other -- which is what a virtual machine or a session
with no window server has.
"""

import os
import sys

from OpenGL.CGL import (
    CGLError,
    OffscreenTarget,
    choose_pixel_format,
    headless_context,
    library,
)


def main():
    renderer = os.environ.get('TEST_CGL_RENDERER', '').strip().lower() or None
    try:
        library()
    except CGLError as err:
        print('no CGL here: %s' % (err,))
        return 1

    try:
        pixel_format, kind = choose_pixel_format(profile='legacy', renderer=renderer)
    except CGLError as err:
        print('no pixel format: %s' % (err,))
        return 1
    library().CGLDestroyPixelFormat(pixel_format)
    print('renderer kind: %s' % (kind,))

    from OpenGL.GL import GL_RENDERER, GL_VENDOR, GL_VERSION, glGetString

    for profile in ('legacy', 'core3', 'core4'):
        try:
            with headless_context(profile=profile, renderer=renderer):
                target = OffscreenTarget(64, 64)
                try:
                    print('%-7s %s | %s | %s' % (
                        profile,
                        glGetString(GL_VENDOR).decode(),
                        glGetString(GL_RENDERER).decode(),
                        glGetString(GL_VERSION).decode(),
                    ))
                finally:
                    target.release()
        except CGLError as err:
            print('%-7s unavailable: %s' % (profile, err))
        except Exception as err:                       # a driver-specific refusal
            print('%-7s unavailable: %s' % (profile, err))
    return 0


if __name__ == '__main__':
    sys.exit(main())
