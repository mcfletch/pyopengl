#! /usr/bin/env python
"""Whether a Tk widget can get a GL context on this Mac, and what it looks like.

Run it to find out whether the Tk widget suite has anything to run on -- the
first thing to ask when it skips every windowed case on macOS::

    python tests/report_tk_aqua.py [screenshot.png]

It exits non-zero when any step fails, so a CI job can use it as a gate: a
suite whose Tk cannot open a window skips its way to green having drawn
nothing, which reads the same as a pass.

The steps, each printed as it is taken:

* which interpreter and which Tk it is linked with, and the windowing system Tk
  reports;
* whether the process is in a GUI login session;
* the windows the process has, by class and title, before and after the widget;
* a context for each profile, with the renderer and version it got;
* a clear colour drawn and read back, then presented;
* with a file name, a screenshot of the screen taken with ``screencapture``,
  so the picture of what a viewer would see can be looked at.

Tk is asked to open a window in a child process first, since a Mac with no
window server can answer by aborting the process rather than raising.
"""

import os
import subprocess
import sys

#: Seconds without finishing after which the probe dumps where it is and exits.
HANG_AFTER = 90

PROBE = (
    'import tkinter\n'
    'root = tkinter.Tk()\n'
    'print(root.tk.call("tk", "windowingsystem"))\n'
    'root.destroy()\n'
)


def say(text=''):
    print(text, flush=True)


def tk_in_a_child():
    """Tk's windowing system as a child process sees it, or None with the reason"""
    try:
        done = subprocess.run(
            [sys.executable, '-c', PROBE], capture_output=True, text=True,
            timeout=60, check=False)
    except subprocess.TimeoutExpired:
        say('Tk did not open a window within 60 s')
        return None
    if done.returncode != 0:
        say('Tk could not open a window (exit %d):' % (done.returncode,))
        say((done.stderr or done.stdout).strip()[-2000:])
        return None
    return done.stdout.strip()


def windows(objc):
    """``(class of content view, title)`` for each NSWindow the process has"""
    found = []
    with objc.pool():
        application = objc.send(objc.cls('NSApplication'), 'sharedApplication')
        for window in objc.items(objc.send(application, 'windows')):
            view = objc.send(window, 'contentView')
            found.append((objc.className(view) if view else None,
                          objc.text(objc.send(window, 'title'))))
    return found


def main():
    import faulthandler
    import logging
    import tkinter

    # A call into the window system that never returns shows as nothing at all
    # in a CI log until the job is killed, so a stall is turned into the Python
    # stack it stopped in, and the log lines before it say how far it got.
    faulthandler.dump_traceback_later(HANG_AFTER, exit=True)
    logging.basicConfig(
        level=logging.DEBUG, stream=sys.stdout,
        format='%(relativeCreated)7d %(name)s: %(message)s')
    logging.getLogger('OpenGL.Tk').setLevel(logging.DEBUG)

    say('python  %s' % (sys.version.split()[0],))
    say('exe     %s' % (sys.executable,))
    say('Tk      %s' % (tkinter.TkVersion,))

    from OpenGL.Tk import GLFrame, TkContextError, cocoa
    from OpenGL.Tk.context import windowingSystem

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from backends import macos_gui_session
    from stalls import sample_if_stalled

    say('session %s' % (macos_gui_session(),))

    system = tk_in_a_child()
    if system is None:
        return 1
    say('Tk windowing system (child process): %s' % (system,))
    if system != 'aqua':
        say('this is not the Aqua Tk, so there is nothing for this to report')
        return 1

    from OpenGL.GL import (
        GL_COLOR_BUFFER_BIT, GL_RENDERER, GL_RGB, GL_UNSIGNED_BYTE, GL_VENDOR,
        GL_VERSION, glClear, glClearColor, glGetString, glReadPixels,
    )

    objc = cocoa.runtime()
    root = tkinter.Tk()
    root.geometry('320x240+100+100')
    root.title('report_tk_aqua')
    say('Tk windowing system (this process): %s' % (windowingSystem(root),))
    root.update()
    say('windows before the widget: %s' % (windows(objc),))

    failed = False
    for profile, version in (('legacy', None), ('core', (3, 3)),
                             ('core', (4, 1))):
        label = '%s %s' % (profile, version or '')
        say("-- %s" % (label,))
        frame = GLFrame(root, width=200, height=150, profile=profile,
                        version=version)
        frame.pack()
        try:
            with sample_if_stalled(20):
                frame.waitForMap()
        except TkContextError as error:
            say('%-14s unavailable: %s' % (label, error))
            failed = failed or profile == 'legacy'
            frame.destroy()
            root.update()
            continue
        context = frame.context
        frame.makeCurrent()
        say('%-14s %s | %s | %s' % (
            label,
            glGetString(GL_VENDOR).decode(),
            glGetString(GL_RENDERER).decode(),
            glGetString(GL_VERSION).decode()))
        say('%-14s %s' % ('', context.describe()))
        glClearColor(1.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        pixel = list(bytes(glReadPixels(2, 2, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)))
        say('%-14s clear colour reads back %s' % ('', pixel))
        failed = failed or pixel[0] < 250
        frame.swapBuffers()
        root.update()
        say('%-14s windows with the widget: %s' % ('', windows(objc)))
        if profile == 'core' and version == (3, 3) and len(sys.argv) > 1:
            screenshot(sys.argv[1], root)
        frame.destroy()
        root.update()

    root.destroy()
    faulthandler.cancel_dump_traceback_later()
    return 1 if failed else 0


def screenshot(path, root):
    """The screen as it is now, kept for a person to look at"""
    for _ in range(10):
        root.update()
    done = subprocess.run(['screencapture', '-x', path], capture_output=True,
                          text=True, check=False)
    say('screencapture exit %d%s' % (
        done.returncode,
        ': ' + done.stderr.strip() if done.stderr.strip() else ''))


if __name__ == '__main__':
    sys.exit(main())
