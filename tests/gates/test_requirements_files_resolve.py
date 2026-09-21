#! /usr/bin/env python3
"""A requirements file that includes itself installs nothing.

``-r`` splices one file into another, so the graph those lines make has to be
acyclic.  Where it is not, pip stops before it installs anything::

    ERROR: accelerate/dev-requirements.txt recursively references itself in
    accelerate/test-requirements.txt

uv resolves the same pair without complaint, so a cycle survives every run that
goes through tox-uv while failing a plain ``pip install -r`` and GitHub's
dependency scanner.  Which of ``test`` and ``dev`` includes the other is a
decision, and this is where it stays recorded.

A ``-r`` naming a file that is not there stops pip the same way, and is checked
with it.
"""

import os
import re

import paths
import pytest

#: Directories holding somebody else's checkout or a build's output.  The
#: requirements files under these are not this project's to keep resolvable.
SKIP = frozenset(
    [
        '.git',
        '.samples',
        '.tox',
        '.venv',
        '__pycache__',
        'build',
        'dist',
        'manylinux-dist',
        'venv',
    ]
)

#: ``-r ./requirements.txt`` at the start of a line, in either spelling.  A
#: ``-r`` anywhere else is part of a requirement or a comment, not an include.
INCLUDE = re.compile(r'^[ \t]*(?:--requirement|-r)[ \t=]+(\S+)', re.M)

#: The files whose includes have to resolve, whatever else the walk turns up.
#: Named so a scan that reaches none of them fails rather than passing empty.
EXPECTED = (
    os.path.join('accelerate', 'requirements.txt'),
    os.path.join('accelerate', 'test-requirements.txt'),
    os.path.join('accelerate', 'dev-requirements.txt'),
)


def requirements_files():
    """Every requirements file in the checkout, as absolute paths."""
    found = []
    for directory, subdirectories, names in os.walk(paths.ROOT):
        subdirectories[:] = [
            name for name in subdirectories if name not in SKIP
        ]
        for name in names:
            if name.endswith('.txt') and 'requirements' in name:
                found.append(os.path.join(directory, name))
    return sorted(found)


def includes(path):
    """The files ``path``'s ``-r`` lines name, resolved against its directory."""
    with open(path, encoding='utf-8') as handle:
        text = handle.read()
    directory = os.path.dirname(path)
    return [
        os.path.normpath(os.path.join(directory, target))
        for target in INCLUDE.findall(text)
    ]


def relative(path):
    """``path`` as the checkout spells it, for a message somebody reads."""
    return os.path.relpath(path, paths.ROOT)


def cycle_from(start, graph):
    """The first cycle a walk from ``start`` reaches, or ``None``.

    The cycle is returned as the list of files that close it, beginning and
    ending at the same one, which is what an installer names in its error.
    """

    def walk(node, stack):
        for target in graph.get(node, ()):
            if target in stack:
                return stack[stack.index(target):] + [target]
            found = walk(target, stack + [target])
            if found:
                return found
        return None

    return walk(start, [start])


FILES = requirements_files()

#: Which files each one splices in.  A ``-r`` naming a file that is not there
#: is left in, so the missing-file case has something to report.
GRAPH = {path: includes(path) for path in FILES}

#: The file names for parametrisation, so a failure says which file it was.
IDS = [relative(path) for path in FILES]


class TestTheScanReachesTheFiles:
    def test_the_walk_finds_the_files_it_is_named_for(self):
        """A walk that reaches nothing passes every other case here."""
        missing = sorted(set(EXPECTED) - set(IDS))
        assert not missing, (
            'the walk from %s did not reach these, so it is skipping a '
            'directory it should not and the cases below are checking less '
            'than they name: %s' % (paths.ROOT, missing)
        )


class TestEveryIncludeResolves:
    @pytest.mark.parametrize('path', FILES, ids=IDS)
    def test_every_include_names_a_file_that_is_there(self, path):
        absent = sorted(
            relative(target)
            for target in GRAPH[path]
            if not os.path.isfile(target)
        )
        assert not absent, (
            '%s includes these with -r and they are not in the checkout, so '
            'pip stops before installing anything: %s'
            % (relative(path), absent)
        )

    @pytest.mark.parametrize('path', FILES, ids=IDS)
    def test_no_file_includes_itself_through_any_chain(self, path):
        found = cycle_from(path, GRAPH)
        assert found is None, (
            'these -r lines make a loop, which pip refuses and uv does not, '
            'so it installs here and fails wherever pip is what runs.  One '
            'of the includes has to go -- decide which of the files is the '
            'superset and let it be the only one that includes the other: %s'
            % ' -> '.join(relative(step) for step in found or [])
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
