#! /usr/bin/env python3
"""Every wrapper names a parameter its entry point actually has.

The friendly modules customise a raw entry point by *naming* its parameters:
``setInputArraySize('indices', None)`` says which argument is an array,
``setOutput('params', …, pnameArg='pname')`` says which is written to and
which other argument gives its size. The names are strings, matched against
the entry point's ``argNames`` at call time.

So a name that is not there does not fail: the wrapper is built, the module
imports, and the customisation it describes silently does not happen -- no
array conversion, no size check, or a call that dies deep inside the converter
machinery with a message naming none of this.

That is the risk #38 was opened about. Khronos renamed the parameters of
fourteen entry points in one commit, and PyOpenGL's wrappers are written
against those names: a rename that nobody notices turns a checked call into an
unchecked one. It is worth a sweep rather than a procedure, because the sweep
runs on every commit and a procedure runs when somebody remembers.

Read from the source rather than by calling anything: the question is what the
declarations say, and the modules that answer it are the ones that would fail
at a call nobody has made yet.

https://github.com/mcfletch/pyopengl/issues/38
"""

import ast
import collections
import importlib
import pathlib

import paths
import pytest

#: Wrapper methods whose first positional argument names a parameter.
NAMES_A_PARAMETER = (
    'setInputArraySize', 'setOutput', 'setPyConverter', 'setCConverter',
    'setCResolver',
)

#: Keyword arguments whose value names a parameter.
NAMES_A_PARAMETER_BY_KEYWORD = ('pnameArg',)


def _entry_point_of(call):
    """Walk ``wrapper.wrapper(fn).setA(...).setB(...)`` back to ``fn``."""
    node = call
    while isinstance(node, ast.Call):
        if (isinstance(node.func, ast.Attribute)
                and node.func.attr in NAMES_A_PARAMETER):
            node = node.func.value
            continue
        if node.args and isinstance(node.args[0], ast.Name):
            return node.args[0].id
        return None
    return None


def _referenced(tree):
    """``{entry point: {parameter names its wrappers mention}}``."""
    wanted = collections.defaultdict(set)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in NAMES_A_PARAMETER):
            continue
        names = set()
        if node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            names.add(node.args[0].value)
        for keyword in node.keywords:
            if (keyword.arg in NAMES_A_PARAMETER_BY_KEYWORD
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)):
                names.add(keyword.value.value)
        entry = _entry_point_of(node)
        if entry and names:
            wanted[entry] |= names
    return wanted


def _friendly_modules():
    """The modules that wrap entry points, with their raw counterpart."""
    package = pathlib.Path(paths.PACKAGE)
    for path in sorted(package.rglob('*.py')):
        relative = path.relative_to(package)
        if 'raw' in relative.parts or relative.name.startswith('_'):
            continue
        yield path, 'OpenGL.raw.%s' % (
            '.'.join(relative.with_suffix('').parts),)


def _findings():
    findings, checked, modules = [], 0, 0
    for path, rawname in _friendly_modules():
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError:                # pragma: no cover - not our source
            continue
        wanted = _referenced(tree)
        if not wanted:
            continue
        try:
            raw = importlib.import_module(rawname)
        except Exception:
            # An API this platform cannot bind; covered elsewhere.
            continue
        modules += 1
        for entry, names in sorted(wanted.items()):
            declared = getattr(getattr(raw, entry, None), 'argNames', None)
            if declared is None:
                continue
            declared = set(declared)
            for name in sorted(names):
                checked += 1
                if name not in declared:
                    findings.append(
                        '%s.%s names %r, but the entry point has %s'
                        % (rawname.replace('.raw', '', 1), entry, name,
                           sorted(declared)))
    return findings, checked, modules


#: Computed once: it parses several hundred modules.
FINDINGS, CHECKED, MODULES = _findings()


def test_the_sweep_found_wrappers_to_check():
    """A sweep that matched nothing would pass while checking nothing."""
    assert MODULES > 10, MODULES
    assert CHECKED > 100, CHECKED


def test_no_wrapper_names_a_parameter_that_is_not_there():
    assert not FINDINGS, (
        '%d wrapper customisation(s) name a parameter their entry point does '
        'not have, so the customisation silently does not happen:\n  %s'
        % (len(FINDINGS), '\n  '.join(FINDINGS)))


def test_no_wrapper_names_an_empty_parameter():
    """The shape the generator produces from a registry ``COMPSIZE()`` that
    names no argument: there is nothing to size the output from, and
    ``pnameArg=''`` says there is."""
    empty = [finding for finding in FINDINGS if "names ''" in finding]
    assert not empty, '\n  '.join(empty)
