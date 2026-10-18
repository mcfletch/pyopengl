"""``open_device`` takes an index into the enumerated devices, or a name.

libgbm is Linux graphics infrastructure; where it is absent the binding raises
ImportError and there is nothing to ask.
"""

import pytest

gbmdevice = pytest.importorskip('OpenGL.EGL.gbmdevice', exc_type=ImportError)


def test_an_index_past_the_devices_there_are_says_how_many(monkeypatch):
    monkeypatch.setattr(gbmdevice, 'enumerate_devices', lambda: ['/dev/dri/card0'])
    with pytest.raises(RuntimeError, match='Only 1 devices available'):
        gbmdevice.open_device(3)


def test_an_index_is_looked_up_among_the_devices(monkeypatch):
    opened = []

    def refuse(path, mode, *rest, **named):
        opened.append(path)
        raise PermissionError(path)

    monkeypatch.setattr(gbmdevice, 'enumerate_devices', lambda: ['/dev/dri/cardZ'])
    monkeypatch.setattr(gbmdevice, 'open', refuse, raising=False)
    with pytest.raises(PermissionError):
        gbmdevice.open_device(0)
    assert opened == ['/dev/dri/cardZ']


class TestHowTheDeviceNodeIsOpened:
    """Mesa maps buffers through the descriptor it is handed, and a mapping that
    is both readable and writable is refused on a descriptor opened write-only
    (``EACCES``).  radeonsi then dereferences the screen it failed to build, and
    the process ends in ``gbm_create_device``.  The node is opened read-write,
    and opened rather than created: ``open(path, 'w')`` makes a regular file
    where there is none and truncates one where there is."""

    @pytest.fixture
    def seen(self, monkeypatch, tmp_path):
        import fcntl
        import os

        node = tmp_path / 'renderD999'
        node.write_bytes(b'not truncated')
        seen = {}

        def create_device(descriptor):
            access = fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_ACCMODE
            seen['access'] = access
            seen['size'] = node.stat().st_size
            return 0

        monkeypatch.setattr(gbmdevice.gbm, 'gbm_create_device', create_device)
        # An absolute name replaces the /dev/dri directory it is joined to.
        with pytest.raises(RuntimeError, match='Unable to create'):
            gbmdevice.open_device(str(node))
        seen['os'] = os
        return seen

    def test_it_is_open_for_reading_and_writing(self, seen):
        assert seen['access'] == seen['os'].O_RDWR

    def test_what_is_at_the_path_is_left_as_it_was(self, seen):
        assert seen['size'] == len(b'not truncated')
