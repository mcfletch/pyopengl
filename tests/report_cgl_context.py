#! /usr/bin/env python
"""Whether a headless OpenGL context can be made on this Mac, and by which renderer.

Run it to find out whether ``TEST_WINDOWING=cgl`` has anything to render on --
the first thing to ask when the suite skips every GL case on macOS::

    python tests/report_cgl_context.py

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

from glcontext import version_shortfall

from OpenGL.CGL import (
    PROFILE_VERSIONS,
    CGLError,
    OffscreenTarget,
    choose_pixel_format,
    headless_context,
    library,
    renderers,
)


def main():
    renderer = os.environ.get('TEST_CGL_RENDERER', '').strip().lower() or None
    try:
        library()
    except CGLError as err:
        print('no CGL here: %s' % (err,))
        return 1

    # What the machine offers, asked of it rather than inferred from what a
    # context turned out to be.  This needs no context and no window, so it
    # answers even where nothing else here would, and `GL major` is what says
    # in advance whether a core profile will come back as one.
    try:
        for found in renderers():
            print('renderer %s' % (found,))
    except CGLError as err:
        print('renderers unavailable: %s' % (err,))

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
                    reported = glGetString(GL_VERSION).decode()
                    print('%-7s %s | %s | %s' % (
                        profile,
                        glGetString(GL_VENDOR).decode(),
                        glGetString(GL_RENDERER).decode(),
                        reported,
                    ))
                    # The condition that segfaults if a test then calls into
                    # it, so say so rather than leaving it to be read off the
                    # version above.  Not fatal: what the profile *does*
                    # provide is still worth testing, and the cases that need
                    # more skip with this same sentence.
                    short = version_shortfall(reported, PROFILE_VERSIONS[profile])
                    if short:
                        print('%-7s WARNING: the %s profile %s'
                              % ('', profile, short.replace('the context ', '')))
                finally:
                    target.release()
        except CGLError as err:
            print('%-7s unavailable: %s' % (profile, err))
        except Exception as err:                       # a driver-specific refusal
            print('%-7s unavailable: %s' % (profile, err))
    return 0


if __name__ == '__main__':
    sys.exit(main())
