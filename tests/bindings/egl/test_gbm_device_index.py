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

    def refuse(path, mode):
        opened.append(path)
        raise PermissionError(path)

    monkeypatch.setattr(gbmdevice, 'enumerate_devices', lambda: ['/dev/dri/cardZ'])
    monkeypatch.setattr(gbmdevice, 'open', refuse, raising=False)
    with pytest.raises(PermissionError):
        gbmdevice.open_device(0)
    assert opened == ['/dev/dri/cardZ']
