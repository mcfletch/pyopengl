#! /usr/bin/env python3
"""``OpenGL.raw.osmesa.mesa``: the constants say what they are called.

This module is hand-written rather than generated from the Khronos registry --
OSMesa is Mesa's own interface and is in no registry -- so nothing keeps the
name a constant is bound under and the name it carries in step.  Every other
raw module has a generator doing that, and the ones that differ there differ
on purpose: ``GL_HALF_FLOAT`` in an AMD extension module is the canonical
``GL_HALF_FLOAT_ARB`` under a second name, which is aliasing rather than a
mistake.  There is no aliasing here, so the two agreeing is the whole rule.

It is worth holding because a ``Constant`` is the value *and* the name: the
value is what reaches the driver, and the name is what every log line, error
message and ``repr`` shows.  A constant carrying another constant's name is
invisible until something prints it, and then it is actively misleading --
``OSMESA_COMPAT_PROFILE`` describing itself as ``OSMESA_CORE_PROFILE`` says
the profile is the one the caller did not ask for.

``__all__`` matters for the same reason: ``from OpenGL.osmesa import *`` is how
these are reached, and a name missing from it is a constant that never arrives.

**Read rather than imported.**  ``OpenGL.raw.osmesa.mesa`` builds its entry
points against ``PLATFORM.OSMesa``, so importing it needs
``PYOPENGL_PLATFORM=osmesa`` and fails everywhere else -- which would make
this a case that runs on one configuration and is collected nowhere.  The
declarations are plain assignments, so the source answers the question on
every platform, with or without a Mesa installed.
"""

import ast
import os

import paths
import pytest

#: `NAME = _C('NAME', value)` is how each constant is declared.
_CONSTANT_FACTORY = '_C'

SOURCE = os.path.join(paths.PACKAGE, 'raw', 'osmesa', 'mesa.py')


def module():
    if not os.path.exists(SOURCE):
        pytest.skip('%s is not in this build' % (SOURCE,))
    with open(SOURCE, encoding='utf-8') as handle:
        return ast.parse(handle.read(), SOURCE)


def declared_constants():
    """``{bound name: name the constant carries}`` for each declaration."""
    found = {}
    for statement in ast.walk(module()):
        if not isinstance(statement, ast.Assign):
            continue
        value = statement.value
        if not (isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == _CONSTANT_FACTORY
                and value.args
                and isinstance(value.args[0], ast.Constant)):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name):
                found[target.id] = value.args[0].value
    return found


def exported_names():
    """The contents of ``__all__``, in order, so duplicates are visible."""
    for statement in ast.walk(module()):
        if (isinstance(statement, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == '__all__'
                        for target in statement.targets)):
            return [element.value for element in statement.value.elts]
    pytest.fail('%s declares no __all__' % (SOURCE,))


def assigned_names():
    """Every name the module binds at the top level."""
    found = set()
    for statement in module().body:
        if isinstance(statement, ast.Assign):
            found.update(target.id for target in statement.targets
                         if isinstance(target, ast.Name))
        elif isinstance(statement, ast.FunctionDef):
            found.add(statement.name)
    return found


def test_there_are_constants_to_check():
    assert len(declared_constants()) > 20, sorted(declared_constants())


def test_each_constant_carries_the_name_it_is_bound_under():
    wrong = [
        '%s is bound under that name but carries %r' % (bound, carried)
        for bound, carried in sorted(declared_constants().items())
        if bound != carried
    ]
    assert not wrong, '\n'.join(wrong)


def test_no_two_constants_carry_one_name():
    """Two bindings sharing a name is how the mismatch above happens."""
    seen, collisions = {}, []
    for bound, carried in sorted(declared_constants().items()):
        if carried in seen:
            collisions.append('%s and %s both carry %r'
                              % (seen[carried], bound, carried))
        seen[carried] = bound
    assert not collisions, '\n'.join(collisions)


def test_every_constant_is_exported():
    missing = sorted(set(declared_constants()) - set(exported_names()))
    assert not missing, (
        'not in __all__, so `from OpenGL.osmesa import *` does not bring '
        'them: %s' % (', '.join(missing),))


def test_nothing_is_exported_twice():
    names = exported_names()
    duplicated = sorted({name for name in names if names.count(name) > 1})
    assert not duplicated, ', '.join(duplicated)


def test_everything_exported_is_declared():
    absent = sorted(set(exported_names()) - assigned_names())
    assert not absent, ', '.join(absent)
