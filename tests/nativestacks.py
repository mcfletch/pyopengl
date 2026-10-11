"""The native stack of every thread in another process, as text.

A child that has printed its result and not exited is waiting somewhere no
Python traceback reaches: in a driver, or in the loader while its libraries
are detached.  A debugger attached to it before it is killed reports which.

    import nativestacks

    except subprocess.TimeoutExpired:
        stacks = nativestacks.of(child.pid)
        child.kill()

``cdb`` on Windows, from the Debugging Tools in the Windows SDK; ``lldb`` on
macOS; ``gdb`` elsewhere.  Linux's Yama restriction (``ptrace_scope`` 1, the
default on Ubuntu) lets a process be attached to by its ancestors only, so
there ``gdb`` reports that it was refused and that is what is returned.
"""

import os
import shutil
import subprocess
import sys

#: Where the Windows SDK installs ``cdb.exe``, under each Program Files root.
_WINDOWS_KITS = os.path.join('Windows Kits', '10', 'Debuggers', 'x64', 'cdb.exe')


def _cdb(environment=os.environ, exists=os.path.exists, which=shutil.which):
    """The path of ``cdb.exe``, or None: on ``PATH``, then where the SDK puts it."""
    found = which('cdb')
    if found:
        return found
    for variable in ('ProgramFiles(x86)', 'ProgramFiles'):
        root = environment.get(variable)
        if root and exists(os.path.join(root, _WINDOWS_KITS)):
            return os.path.join(root, _WINDOWS_KITS)
    return None


def command(pid, platform=sys.platform, which=shutil.which, cdb=_cdb):
    """The debugger command that prints every thread's stack in ``pid``, or None.

    Each attaches, prints and detaches, leaving the process as it was.  ``cdb``
    attaches non-invasively (``-pv``): an ordinary attach starts a thread in
    the target, which cannot run in a process holding the loader lock.
    """
    if platform == 'win32':
        debugger = cdb()
        if debugger:
            return [debugger, '-pv', '-p', str(pid), '-c', '~*kn 40; qd']
    elif platform == 'darwin':
        debugger = which('lldb')
        if debugger:
            return [debugger, '--batch', '-p', str(pid), '-o', 'thread backtrace all']
    else:
        debugger = which('gdb')
        if debugger:
            return [debugger, '-p', str(pid), '-batch', '-ex', 'thread apply all backtrace 40']
    return None


def of(pid, timeout=60.0):
    """What the platform's debugger printed for ``pid``, or why there is nothing."""
    asked = command(pid)
    if asked is None:
        return 'no debugger here to read the stacks of process %d with' % (pid,)
    try:
        ran = subprocess.run(
            asked, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL
        )
    except (OSError, subprocess.SubprocessError) as err:
        return '%s did not report: %s' % (asked[0], err)
    return (ran.stdout + ran.stderr).decode('utf-8', errors='replace').strip()
