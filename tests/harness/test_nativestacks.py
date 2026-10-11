"""Which debugger reads a stuck child's stacks, and what comes back."""
import subprocess
import sys

import nativestacks


def nowhere(name):
    return None


class TestTheCommand:
    def test_windows_attaches_without_starting_a_thread(self):
        asked = nativestacks.command(41, platform='win32', cdb=lambda: 'cdb.exe')
        assert asked[:4] == ['cdb.exe', '-pv', '-p', '41']
        assert asked[-1].endswith('qd'), 'the process is left running'

    def test_macos_asks_lldb(self):
        asked = nativestacks.command(41, platform='darwin', which=lambda name: '/usr/bin/' + name)
        assert asked[0] == '/usr/bin/lldb'
        assert '41' in asked

    def test_elsewhere_asks_gdb(self):
        asked = nativestacks.command(41, platform='linux', which=lambda name: '/usr/bin/' + name)
        assert asked[0] == '/usr/bin/gdb'
        assert '41' in asked

    def test_no_debugger_is_no_command(self):
        for platform in ('win32', 'darwin', 'linux'):
            assert nativestacks.command(41, platform=platform, which=nowhere, cdb=lambda: None) is None


class TestWhereCdbIs:
    def test_on_the_path(self):
        assert nativestacks._cdb(which=lambda name: 'found') == 'found'

    def test_where_the_sdk_installs_it(self):
        found = nativestacks._cdb(
            environment={'ProgramFiles(x86)': 'kits'}, exists=lambda path: True, which=nowhere
        )
        assert found.startswith('kits') and found.endswith('cdb.exe')

    def test_not_installed(self):
        assert nativestacks._cdb(environment={}, which=nowhere) is None


class TestWhatComesBack:
    def test_no_debugger_says_so(self, monkeypatch):
        monkeypatch.setattr(nativestacks, 'command', lambda pid: None)
        assert 'no debugger' in nativestacks.of(41)

    def test_a_debugger_that_cannot_be_run_says_so(self, monkeypatch):
        monkeypatch.setattr(nativestacks, 'command', lambda pid: ['no-such-debugger-here'])
        assert 'did not report' in nativestacks.of(41)

    def test_what_the_debugger_printed(self, monkeypatch):
        monkeypatch.setattr(
            nativestacks, 'command', lambda pid: [sys.executable, '-c', 'print("frame", %d)' % pid]
        )
        assert nativestacks.of(41) == 'frame 41'

    def test_a_live_process_is_left_running(self):
        """Whatever the debugger here is allowed to do, the child survives it."""
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        try:
            assert nativestacks.of(child.pid)
            assert child.poll() is None
        finally:
            child.kill()
            child.wait()
