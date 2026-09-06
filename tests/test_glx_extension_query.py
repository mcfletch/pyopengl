"""Whether GLX's own extensions are reported, and how the display is named.

``_GLXQuerier`` is what answers ``platform.checkExtension('GLX_...')``, which is
the gate every GLX extension entry point is resolved through. When it answers
"no extensions", every GLX extension reads as absent: ``GLX_ARB_create_context``
(so no context can be asked for a profile), ``GLX_EXT_swap_control`` (so vsync
cannot be set), ``GLX_ARB_multisample``, and the rest.

It answered exactly that on Python 3, for every program, because
``XOpenDisplay`` takes a ``char *`` and was handed a ``str``: with no
``argtypes`` set, ctypes passes a ``str`` as ``wchar_t *``, X reads a display
name out of the wrong encoding, and the connection fails. The version then came
back ``[0, 0]`` from a NULL display and the extension list was empty.

See `plans/TK-WIDGET.md`, which is what needed the create-context extension.
"""

import os

import pytest

from OpenGL.raw.GLX._types import GLXQuerier, displayName


class TestNamingTheDisplay:
    """The name has to reach X as bytes; that is the whole of the defect."""

    def test_it_is_bytes(self, monkeypatch):
        monkeypatch.setenv('DISPLAY', ':0')
        assert displayName() == b':0'

    def test_a_name_with_a_host_survives_intact(self, monkeypatch):
        monkeypatch.setenv('DISPLAY', 'somewhere.example:1.0')
        assert displayName() == b'somewhere.example:1.0'

    def test_no_display_named_asks_for_the_default_one(self, monkeypatch):
        """NULL is what X reads as "whatever this session is using", which is
        right where the variable is unset -- and is not the same as an empty
        name, which X refuses."""
        monkeypatch.delenv('DISPLAY', raising=False)
        assert displayName() is None

    def test_an_empty_variable_is_no_name_at_all(self, monkeypatch):
        """An unexported shell variable expands to the empty string."""
        monkeypatch.setenv('DISPLAY', '')
        assert displayName() is None


@pytest.mark.skipif(not os.environ.get('DISPLAY', '').strip(),
                    reason='no X display to query GLX on')
class TestAgainstARealServer:
    def test_the_version_is_reported(self):
        """[0, 0] is what a failed connection answers, and no server is at 0."""
        version = GLXQuerier.getVersion()
        assert version >= [1, 1], version

    def test_the_extension_list_is_not_empty(self):
        """Every X server with GLX advertises something."""
        assert GLXQuerier.getExtensions()

    def test_a_named_extension_is_found(self):
        """`GLX_ARB_create_context` is on every driver since 2009, including
        the software one, and is what a context with a profile is asked
        through."""
        from OpenGL import platform

        assert platform.PLATFORM.checkExtension('GLX_ARB_create_context')

    def test_the_entry_point_it_gates_resolves(self):
        """Which is the thing that was actually broken: bool() on it was
        False, so nothing could create a context with a profile."""
        from OpenGL.GLX.ARB import create_context

        assert bool(create_context.glXCreateContextAttribsARB)

    def test_asking_twice_does_not_leak_a_connection(self):
        """Each query opened a display and never closed it, so a program that
        probed a few extensions leaked a file descriptor apiece."""
        import subprocess
        import sys

        script = (
            'import os\n'
            'from OpenGL.raw.GLX._types import GLXQuerier\n'
            'before = len(os.listdir("/proc/self/fd"))\n'
            'for _ in range(20):\n'
            '    GLXQuerier.pullExtensions()\n'
            'after = len(os.listdir("/proc/self/fd"))\n'
            'print(after - before)\n'
        )
        grew = int(subprocess.run([sys.executable, '-c', script],
                                  capture_output=True, text=True,
                                  check=True).stdout.strip())
        assert grew <= 1, 'leaked %d file descriptors over 20 queries' % (grew,)
