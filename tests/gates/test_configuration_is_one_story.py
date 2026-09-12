#! /usr/bin/env python3
"""A flag is documented, settable from the environment, and snapshotted once.

``OpenGL.ERROR_ON_COPY = True`` after ``import OpenGL.GL`` changed nothing and
said nothing.  The flags are read once, when the first entry point is built,
and frozen into ``OpenGL._configflags``; every wrapper is built from that
snapshot, so an assignment afterwards is dropped and the caller runs on
believing a setting is in force that is not.  Two tracker issues are that, and
both were spent looking at the array machinery, which was behaving correctly
throughout.

What settles it for a caller who cannot control import order is the
environment: ``PYOPENGL_ERROR_ON_COPY=1`` is read before anything is built, and
the warning ``OpenGL.__init__`` raises on a late assignment says so.  That
advice is only true of a flag that goes through ``environ_key`` -- and
``SIZE_1_ARRAY_UNPACK`` was the one in the list that did not, so the variable
did nothing, nothing could select the behaviour, nothing tested it, and it had
stopped working.

So the four statements of the configuration have to agree:

* the assignments in ``OpenGL/__init__.py``,
* the names ``OpenGL/_configflags.py`` snapshots,
* ``_SNAPSHOTTED_FLAGS``, which is what the late-assignment warning reads,
* and the module docstring, which is where a user reads about any of it.
"""

import ast
import os
import re

import paths
import pytest

PACKAGE_INIT = os.path.join(paths.PACKAGE, '__init__.py')
CONFIGFLAGS = os.path.join(paths.PACKAGE, '_configflags.py')

#: How the docstring introduces a flag: ``    NAME -- what it does``.
DOCUMENTED = re.compile(r'^ {4}([A-Z][A-Z0-9_]+) --', re.MULTILINE)


def tree(path):
    with open(path, encoding='utf-8') as handle:
        return ast.parse(handle.read(), filename=path)


def assignments():
    """``{name: how}`` for the module-level flag assignments in the package.

    ``how`` is ``'environ_key'`` where the value comes through it, and the
    spelling of whatever else it came from otherwise.
    """
    found = {}
    for node in tree(PACKAGE_INIT).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if not re.match(r'^[A-Z][A-Z0-9_]+$', target.id):
                continue
            if target.id.startswith('_'):
                continue
            value = node.value
            if isinstance(value, ast.Call):
                called = getattr(value.func, 'id', None) or getattr(
                    value.func, 'attr', None
                )
                found[target.id] = called
            else:
                found[target.id] = ast.dump(value).split('(')[0]
    return found


def snapshotted():
    """The names ``_configflags`` imports from the package."""
    for node in tree(CONFIGFLAGS).body:
        if isinstance(node, ast.ImportFrom) and node.module == 'OpenGL':
            return {alias.name for alias in node.names}
    raise AssertionError('OpenGL/_configflags.py imports nothing from OpenGL')


def declared():
    """``_SNAPSHOTTED_FLAGS``, which the late-assignment warning reads."""
    for node in tree(PACKAGE_INIT).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '_SNAPSHOTTED_FLAGS':
                return {
                    element.value
                    for element in ast.walk(node.value)
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                }
    raise AssertionError('OpenGL/__init__.py declares no _SNAPSHOTTED_FLAGS')


def documented():
    """The flags the package docstring introduces."""
    with open(PACKAGE_INIT, encoding='utf-8') as handle:
        text = handle.read()
    module = ast.parse(text, filename=PACKAGE_INIT)
    return set(DOCUMENTED.findall(ast.get_docstring(module) or ''))


class TestTheFourStatementsAgree:
    def test_the_snapshot_and_the_warning_name_the_same_flags(self):
        assert snapshotted() == declared(), (
            'OpenGL/_configflags.py and `_SNAPSHOTTED_FLAGS` disagree about '
            'which flags are frozen.  `_SNAPSHOTTED_FLAGS` is what decides '
            'whether a late assignment warns, so a flag missing from it is '
            'one that is silently dropped -- which is the whole defect.\n'
            '  only in _configflags: %s\n  only in the declaration: %s'
            % (
                sorted(snapshotted() - declared()),
                sorted(declared() - snapshotted()),
            )
        )

    def test_every_snapshotted_flag_is_assigned_here(self):
        missing = sorted(declared() - set(assignments()))
        assert not missing, (
            'these are snapshotted but not assigned at module level in '
            'OpenGL/__init__.py, so the snapshot reads a name that is not '
            'there: %s' % missing
        )

    def test_every_snapshotted_flag_is_documented(self):
        undocumented = sorted(declared() - documented())
        assert not undocumented, (
            'these are flags a caller can set and the module docstring does '
            'not introduce, which is where a user reads about any of '
            'them: %s' % undocumented
        )


class TestTheEnvironmentCanSetWhatTheWarningSaysItCan:
    """The warning tells a caller to use ``PYOPENGL_<NAME>``.

    That is only true of a flag whose value comes through ``environ_key``.
    ``SIZE_1_ARRAY_UNPACK`` was the one in the list that did not, so setting
    the variable did nothing and only assigning to the name before the first
    import had any effect -- and because nothing could select the behaviour,
    nothing tested it and it had stopped working.
    """

    def test_every_snapshotted_flag_reads_the_environment(self):
        made = assignments()
        elsewhere = sorted(
            '%s (from %s)' % (name, made[name])
            for name in declared()
            if made.get(name) != 'environ_key'
        )
        assert not elsewhere, (
            'these are snapshotted flags whose value does not come through '
            '`environ_key`, so `PYOPENGL_<NAME>` does nothing for them -- '
            'while the warning raised on a late assignment tells the caller '
            'to set exactly that, "which works whatever the import order".  A '
            'flag nothing can select from outside the process is also a flag '
            'no configuration axis in the matrix can test:\n  %s'
            % '\n  '.join(elsewhere)
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
