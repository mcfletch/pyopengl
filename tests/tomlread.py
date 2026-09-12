#! /usr/bin/env python3
"""Reading a TOML file on every interpreter the matrix runs.

``tomllib`` is the standard library's TOML reader from 3.11, and the floor here
is 3.9.  ``tomli`` is the same module under its original name and the same API;
the ``test`` extra names it below 3.11.

This is the one place the guarded import is written, so that the floor gate
(``tox -e floor``) can name a single file as the one allowed to reach for a
module two supported interpreters do not have, and go on reporting every other
use of one.

Import the name instead::

    from tomlread import load
"""

try:
    import tomllib as _toml
except ModuleNotFoundError:
    import tomli as _toml


def load(path):
    """The parsed document at ``path``, read as the binary TOML wants."""
    with open(path, 'rb') as handle:
        return _toml.load(handle)
