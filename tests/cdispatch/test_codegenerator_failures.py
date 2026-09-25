"""The ctypes module generator stops on a failure.

``src/codegenerator.py`` runs unattended, from ``xml_generate.py`` and in CI,
so a failure while it writes a module is raised to the caller with its
traceback rather than waiting on a terminal nobody is at.
"""

import pdb
import types

import pytest

import codegenerator


class _Broken(Exception):
    pass


def test_a_failure_in_the_output_wrapping_is_raised(monkeypatch):
    def commands():
        raise _Broken('a registry that cannot list its commands')

    def set_trace(*_args, **_named):
        raise AssertionError('the generator entered the debugger')

    monkeypatch.setattr(pdb, 'set_trace', set_trace)
    generator = codegenerator.ModuleGenerator.__new__(codegenerator.ModuleGenerator)
    generator.registry = types.SimpleNamespace(commands=commands)
    with pytest.raises(_Broken):
        _ = generator.output_wrapping


def _wrapping_of(dependency):
    function = types.SimpleNamespace(
        name='glGetThing', size_dependencies={'params': dependency}
    )
    generator = codegenerator.ModuleGenerator.__new__(codegenerator.ModuleGenerator)
    generator.registry = types.SimpleNamespace(commands=lambda: [function])
    return generator.output_wrapping


def test_a_size_divided_by_a_constant():
    text = _wrapping_of(codegenerator.xmlreg.Dynamicsize('count/2'))
    assert 'size=lambda x: (x//2),pnameArg=\'count\'' in text


def test_a_size_multiplied_by_a_constant():
    text = _wrapping_of(codegenerator.xmlreg.Dynamicsize('count*3'))
    assert 'size=lambda x: (x*3),pnameArg=\'count\'' in text
