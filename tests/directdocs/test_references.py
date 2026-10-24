#! /usr/bin/env python3
"""The sample scan over other people's checkouts.

The sample sources are repositories nobody here maintains, so some of their
files do not tokenize as Python 3.  Such a file costs its own samples and is
named in the log; the files around it are still scanned.
"""

import logging
import os

from directdocs import references


def _names(path):
    found = []
    references.generate_tokens_file(
        str(path),
        processFunction=lambda *token: found.append(token[2]),
    )
    return found


def test_the_gl_names_in_a_file_are_found(tmp_path):
    source = tmp_path / 'sample.py'
    source.write_text('glBegin(GL_TRIANGLES)\nprint(len([]))\n')
    assert _names(source) == ['glBegin', 'GL_TRIANGLES']


def test_a_file_that_does_not_tokenize_is_named_in_the_log(tmp_path, caplog):
    source = tmp_path / 'broken.py'
    source.write_text('glBegin(GL_TRIANGLES)\nx = """never closed\n')
    with caplog.at_level(logging.WARNING, logger=references.log.name):
        found = _names(source)
    assert found == ['glBegin', 'GL_TRIANGLES']
    assert str(source) in caplog.text


def test_a_file_that_is_not_text_is_named_in_the_log(tmp_path, caplog):
    source = tmp_path / 'latin1.py'
    source.write_bytes(b'glBegin()\n# caf\xe9\n')
    with caplog.at_level(logging.WARNING, logger=references.log.name):
        _names(source)
    assert str(source) in caplog.text


class TestWhereItReadsAndWrites:
    """The scan is run from anywhere; ``generate.py`` reads the cache from
    ``directdocs/``, and ``samples.py`` checks out into ``directdocs/.samples``."""

    def test_the_samples_are_the_ones_samples_py_fetches(self):
        from directdocs import samples

        assert references.SAMPLES == os.path.join(samples.HERE, samples.SAMPLE_DIRECTORY)

    def test_the_cache_is_written_beside_the_script(self, tmp_path, monkeypatch):
        script = tmp_path / 'directdocs'
        script.mkdir()
        elsewhere = tmp_path / 'elsewhere'
        elsewhere.mkdir()
        monkeypatch.setattr(references, 'HERE', str(script))
        monkeypatch.chdir(elsewhere)
        written = references.write_cache({'glBegin': []})
        assert written == str(script / references.CACHE_FILE)
        assert (script / references.CACHE_FILE).is_file()
        assert not (elsewhere / references.CACHE_FILE).exists()
