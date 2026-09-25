#! /usr/bin/env python3
"""The sample scan over other people's checkouts.

The sample sources are repositories nobody here maintains, so some of their
files do not tokenize as Python 3.  Such a file costs its own samples and is
named in the log; the files around it are still scanned.
"""

import logging

from directdocs import references


def _names(path):
    found = []
    references.generate_tokens_file(
        str(path),
        processFunction=lambda filename, kind, name, *rest: found.append(name),
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
