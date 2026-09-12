#! /usr/bin/env python3
"""A gate nothing runs is a gate that stops being true.

This repository has had that four times in three months, each time with the
configuration sitting in the file saying it was covered:

* ``tox.ini`` declared ``py39`` cells and the matrix started at 3.10, so the
  lowest interpreter ``requires-python`` and the trove classifiers promise was
  never exercised.
* The accelerate suites ran in no job at all: tox's command named them in the
  posargs *default*, and every job passed ``-m "not performance"``, so the
  default never rendered.
* ``typecheck`` was an environment nobody called, so a plain ``tox`` did not
  run it.
* A ``serial`` marker meant nothing in the matrix, where it matters most: a
  cell ran ``pytest`` once, beside whatever else the machine was doing.

So the three files that describe a run have to agree.  ``tox.ini`` says what
the configurations are, ``.github/workflows/test.yml`` says which of them a
push runs, and ``pyproject.toml`` says what the suite is and which markers it
has.

The workflow is read with a regular expression rather than a YAML parser.
Every row in it is written ``{python: '3.12', toxenv: py312-...}``, the one
thing wanted from it is that field, and adding a YAML library to the ``test``
extra would put it in all thirty matrix environments to read one line.
"""

import itertools
import os
import re

import paths
import pytest

TOX = os.path.join(paths.ROOT, 'tox.ini')
WORKFLOW = os.path.join(paths.ROOT, '.github', 'workflows', 'test.yml')
PYPROJECT = os.path.join(paths.ROOT, 'pyproject.toml')

#: ``toxenv: py312-num1-accel0-dispctypes``, inline in a matrix row.
INLINE = re.compile(r'\btoxenv:[ \t]*([A-Za-z0-9_.][A-Za-z0-9_.-]*)')

#: The block form, where a job runs several environments::
#:
#:     toxenv:
#:       - py312-num1-accel0-dispctypes
#:       - py312-num1-accel1-dispc
BLOCK = re.compile(
    r'\btoxenv:[ \t]*\n((?:[ \t]*-[ \t]*[A-Za-z0-9_.][A-Za-z0-9_.-]*[ \t]*\n)+)'
)
BLOCK_ITEM = re.compile(r'-[ \t]*([A-Za-z0-9_.][A-Za-z0-9_.-]*)')

#: Factors declared in tox.ini that no row in test.yml names, and why.
UNRUN_FACTORS = {
    'pypy310': 'no PyPy runner in the matrix; run locally with `tox -e pypy310-...`',
    'pypy311': 'no PyPy runner in the matrix; run locally with `tox -e pypy311-...`',
    'py311': 'one interpreter between the 3.10 and 3.12 rows; the sweep is '
             'the floor, the next one up, and every release since',
}

#: Markers a run deselects and nothing selects back, with why nothing does.
#: A marker in this position is the shape the `serial` one had: declared,
#: used, and never actually run -- so each has to say that it is meant.
NEVER_SELECTED = {
    'performance': 'asserts how fast something draws, and no runner in the '
                   'matrix has a GPU -- llvmpipe answers a question about '
                   'speed wrongly by three orders of magnitude.  Run on a '
                   'machine with a driver: `tox -e ... -- -m performance`',
    'resources': 'asserts a budget in memory or import time, which other work '
                 'on a shared runner spends.  Run on a quiet machine: '
                 '`tox -e ... -- -m resources`',
}


def _text(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def envlist():
    """The environment names ``tox.ini``'s ``envlist`` declares, expanded."""
    text = _text(TOX)
    block = re.search(r'^envlist\s*=\s*\n(.*?)(?=^\S)', text, re.M | re.S)
    assert block, 'tox.ini declares no envlist'
    found = []
    for line in block.group(1).splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        found.extend(_expand(line))
    return found


def _expand(pattern):
    """``py{39,310}-num{0,1}`` -> the four names it stands for."""
    parts = re.split(r'\{([^}]*)\}', pattern)
    choices = [
        [literal] if index % 2 == 0 else literal.split(',')
        for index, literal in enumerate(parts)
    ]
    return [''.join(one) for one in itertools.product(*choices)]


def factors(name):
    """The factors a tox environment name is made of."""
    return set(name.split('-'))


def declared_environments():
    """Environments ``tox.ini`` gives a ``[testenv:...]`` section of its own."""
    return set(re.findall(r'^\[testenv:([A-Za-z0-9_.-]+)\]', _text(TOX), re.M))


def workflow_environments():
    """The tox environments ``test.yml`` names, in either form."""
    text = _text(WORKFLOW)
    found = set(INLINE.findall(text))
    for block in BLOCK.findall(text):
        found |= set(BLOCK_ITEM.findall(block))
    return found


def markers():
    """The markers ``pyproject.toml`` declares, by name."""
    block = re.search(r'^markers\s*=\s*\[(.*?)^\]', _text(PYPROJECT), re.M | re.S)
    assert block, 'pyproject.toml declares no markers'
    return set(re.findall(r'"\s*([a-z_]+)\s*:', block.group(1)))


def suite_paths():
    """The paths ``pyproject.toml`` says the suite is."""
    block = re.search(r'^testpaths\s*=\s*\[(.*?)\]', _text(PYPROJECT), re.M | re.S)
    assert block, 'pyproject.toml declares no testpaths'
    return set(re.findall(r'"([^"]+)"', block.group(1)))


def marked_in_the_suite():
    """The markers the suite actually puts on something."""
    import ast

    import sources

    found = set()
    for module in sources.suite():
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Attribute):
                continue
            base = node.value
            if isinstance(base, ast.Attribute) and base.attr == 'mark':
                found.add(node.attr)
    return found


#: A marker expression as a run writes one: ``-m "not performance"``.  Quoted,
#: which is how every one of them is written here and what keeps this from
#: reading ``python -m pytest`` as a marker named ``pytest``.
EXPRESSION = re.compile(r'-m\s+"([^"]*)"')

#: The words a marker expression is built from, which are not marker names.
OPERATORS = frozenset(['not', 'and', 'or'])


def _expressions():
    text = _text(TOX) + _text(WORKFLOW)
    return EXPRESSION.findall(text)


def _split(expression):
    """``('not', 'performance', 'and', ...)`` for a marker expression."""
    return re.findall(r'[A-Za-z_][A-Za-z0-9_]*|\(|\)', expression)


def deselected():
    """The markers a run leaves out."""
    found = set()
    for expression in _expressions():
        tokens = _split(expression)
        for index, token in enumerate(tokens):
            if token == 'not' and index + 1 < len(tokens):
                if tokens[index + 1] not in OPERATORS:
                    found.add(tokens[index + 1])
    return found


def selected():
    """The markers a run asks for by name, rather than leaving out."""
    found = set()
    for expression in _expressions():
        tokens = _split(expression)
        for index, token in enumerate(tokens):
            if token in OPERATORS or token in ('(', ')'):
                continue
            if index and tokens[index - 1] == 'not':
                continue
            found.add(token)
    return found


class TestEveryConfigurationIsRunSomewhere:
    def test_every_tox_factor_is_named_by_a_workflow_row(self):
        declared = set()
        for name in envlist():
            declared |= factors(name)
        run = set()
        for name in workflow_environments():
            run |= factors(name)
        missing = sorted(declared - run - set(UNRUN_FACTORS))
        assert not missing, (
            'these configurations are declared in tox.ini and no row of '
            '.github/workflows/test.yml runs one.  A configuration nobody '
            'runs is a claim nobody checks -- the py39 floor sat in the '
            'envlist while the matrix started at 3.10.  Add a row, or record '
            'the factor in UNRUN_FACTORS with the reason: %s' % missing
        )

    def test_every_recorded_gap_is_still_a_gap(self):
        run = set()
        for name in workflow_environments():
            run |= factors(name)
        stale = sorted(set(UNRUN_FACTORS) & run)
        assert not stale, (
            'these are recorded as configurations nothing runs, and a row '
            'now runs them.  Take them out of UNRUN_FACTORS: a record that is '
            'no longer true is one nobody reads: %s' % stale
        )

    def test_every_workflow_environment_is_one_tox_declares(self):
        known = set(envlist()) | declared_environments()
        unknown = sorted(workflow_environments() - known)
        assert not unknown, (
            'these rows name a tox environment tox does not declare, so the '
            'job builds an environment from the factors it can recognise and '
            'silently drops the rest: %s' % unknown
        )

    def test_the_gates_that_are_not_a_test_run_are_in_the_envlist(self):
        """``typecheck`` waited to be called by name and so was not called."""
        listed = set(envlist())
        missing = sorted(
            name
            for name in declared_environments()
            if name not in listed
        )
        assert not missing, (
            'these have a [testenv:...] section and are not in the envlist, '
            'so a plain `tox` does not run them: %s' % missing
        )


class TestEveryMarkerIsDecidedSomewhere:
    """``serial`` meant nothing in the matrix until tox ran the two passes: a
    cell ran ``pytest`` once, beside whatever else the machine was doing, so a
    test comparing wall-clock frame times read the load rather than the
    library.  A marker nothing acts on is decoration."""

    def test_every_declared_marker_is_put_on_something(self):
        unused = sorted(markers() - marked_in_the_suite())
        assert not unused, (
            'these markers are declared in pyproject.toml and nothing in the '
            'suite carries one, so selecting or deselecting them changes '
            'nothing: %s' % unused
        )

    def test_every_marker_a_run_names_is_declared(self):
        """An undeclared marker is a typo pytest cannot tell from a name."""
        undeclared = sorted((deselected() | selected()) - markers())
        assert not undeclared, (
            'tox.ini or the workflow names these in a `-m` expression and '
            'pyproject.toml declares none of them, so the expression selects '
            'nothing and says nothing: %s' % undeclared
        )

    def test_a_marker_that_is_only_ever_deselected_says_why(self):
        silent = sorted(
            name
            for name in deselected()
            if name not in selected() and name not in NEVER_SELECTED
        )
        assert not silent, (
            'these markers are deselected by every run there is and selected '
            'by none, so the cases carrying them are never run anywhere.  '
            'Either give them a pass of their own, as the two-pass `serial` '
            'run does, or record in NEVER_SELECTED that nothing here can run '
            'them and how somebody does: %s' % silent
        )

    def test_every_recorded_marker_is_still_never_selected(self):
        stale = sorted(set(NEVER_SELECTED) & selected())
        assert not stale, (
            'these are recorded as markers nothing selects, and something '
            'now does.  Take them out of NEVER_SELECTED: %s' % stale
        )


class TestTheSuiteThePathsNameIsRun:
    def test_every_testpath_is_reached_by_a_run(self):
        """The accelerate suites ran in no job: they were in the posargs
        default, and every job passed a ``-m`` expression, so the default
        never rendered."""
        text = _text(TOX) + _text(WORKFLOW)
        missing = sorted(path for path in suite_paths() if path not in text)
        assert not missing, (
            'these are declared as part of the suite and neither tox.ini nor '
            'the workflow names them, so nothing runs them unless a bare '
            '`pytest` is what runs: %s' % missing
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
