#! /usr/bin/env python3
"""``tests/stubs.py``: the one reader of a shipped ``.pyi``.

Nine modules used to open, parse and walk a stub for themselves, each in a
slightly different shape -- so a question about the declared surface was
answered nine ways and a change to what counts as a declaration reached
whichever of them someone remembered.  These hold the shared reader to what
those modules need of it.
"""

import ast
import os

import paths
import pytest
import stubs


def test_a_relative_name_resolves_under_the_package():
    assert stubs.path('GL/__init__.pyi') == os.path.join(
        paths.PACKAGE, 'GL/__init__.pyi')


def test_a_stub_the_package_does_not_ship_reads_as_nothing():
    """A checkout that has not been generated into has no stubs, and a case
    about what one says must not answer that question by failing."""
    assert stubs.tree('GL/no-such-module.pyi') is None
    assert stubs.declarations('GL/no-such-module.pyi') == {}


def test_the_same_stub_is_parsed_once():
    assert stubs.tree('GL/__init__.pyi') is stubs.tree('GL/__init__.pyi')


def a_shipped_stub():
    """A stub this checkout has, or ``None`` where it was never generated."""
    for relative in ('GL/__init__.pyi', 'GLU/__init__.pyi'):
        if stubs.tree(relative) is not None:
            return relative
    return None


class TestWhatItReadsOutOfOne:
    @pytest.fixture
    def sample(self):
        relative = a_shipped_stub()
        if relative is None:
            pytest.skip('this checkout has no generated stubs')
        return relative

    def test_it_finds_the_entry_points(self, sample):
        found = stubs.functions(sample)
        assert found, sample
        assert all(isinstance(node, ast.FunctionDef) for node in found.values())

    def test_it_finds_the_constants(self, sample):
        found = stubs.annotations(sample)
        assert found, sample
        assert all(isinstance(text, str) for text in found.values())

    def test_the_two_do_not_overlap(self, sample):
        assert not set(stubs.functions(sample)) & set(stubs.annotations(sample))

    def test_together_they_are_everything_declared(self, sample):
        assert (set(stubs.functions(sample)) | set(stubs.annotations(sample))
                == set(stubs.declarations(sample)))


class TestEveryDeclarationOfAName:
    """A name declared twice -- an ``@overload`` pair, or the C form beside
    the Pythonic one -- is one name in the namespace and two declarations."""

    def test_a_stub_that_is_not_there_declares_nothing(self):
        assert stubs.every_function('GL/no-such-module.pyi') == ()

    def test_it_keeps_the_declarations_the_namespace_collapses(self):
        relative = a_shipped_stub()
        if relative is None:
            pytest.skip('this checkout has no generated stubs')
        every = stubs.every_function(relative)
        assert len(every) >= len(stubs.functions(relative))
        assert {name for name, _node in every} == set(stubs.functions(relative))

    def test_they_come_back_in_the_order_the_file_declares_them(self):
        relative = a_shipped_stub()
        if relative is None:
            pytest.skip('this checkout has no generated stubs')
        lines = [node.lineno for _name, node in stubs.every_function(relative)]
        assert lines == sorted(lines)


class TestReadingOneParameter:
    def test_a_declared_parameter_answers_its_annotation(self):
        if stubs.tree('GL/__init__.pyi') is None:
            pytest.skip('this checkout has no generated stubs')
        assert stubs.parameter_annotation(
            'GL/__init__.pyi', 'glBindTexture', 'target') == 'int'

    def test_an_entry_point_the_stub_does_not_declare(self):
        assert stubs.parameter_annotation(
            'GL/__init__.pyi', 'glNotAnEntryPoint', 'target') is None

    def test_a_parameter_the_entry_point_does_not_take(self):
        if stubs.tree('GL/__init__.pyi') is None:
            pytest.skip('this checkout has no generated stubs')
        assert stubs.parameter_annotation(
            'GL/__init__.pyi', 'glBindTexture', 'notAParameter') is None


class TestTheWholeSurface:
    def test_it_names_the_stubs_that_are_there(self):
        found = stubs.every_stub()
        if not found:
            pytest.skip('this checkout has no generated stubs')
        assert all(name.endswith('.pyi') for name in found)
        assert all(os.path.exists(stubs.path(name)) for name in found)

    def test_the_names_are_relative_to_the_package(self):
        found = stubs.every_stub()
        if not found:
            pytest.skip('this checkout has no generated stubs')
        assert not any(os.path.isabs(name) for name in found)

    def test_it_is_sorted_so_a_parametrised_run_is_stable(self):
        assert list(stubs.every_stub()) == sorted(stubs.every_stub())
