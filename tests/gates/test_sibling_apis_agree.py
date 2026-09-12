#! /usr/bin/env python3
"""The same file, done for nine APIs, does the same thing in each of them.

``PYOPENGL_ERROR_CHECKING=0`` made ``import OpenGL.GLES2`` fail outright with
``TypeError: 'NoneType' object is not callable``.  Turning error checking off
sets ``OpenGL.error._ErrorChecker`` to None -- there is no checker, which is
the point of the flag -- and two raw modules built one without asking.
``OpenGL/raw/GL/_errors.py`` has always guarded it; GLES2's and GLSC2's
``_types.py`` did not.  The reporter had no way to read the traceback: the
failing line names neither the flag responsible nor anything they wrote.

That defect is a *difference between siblings*, and nothing looks for one.  A
test asks its own API and passes; the flag axis is one cell of the matrix; and
the modules are generated from a template nobody diffs.

Two questions here.  The first is the one the defect was: wherever a checker
is built, the flag that can take the class away is honoured.  The second is
broader: the APIs group into recorded shapes, and a group that is not recorded
-- a tenth spelling of ``_errors.py``, a seventh of something else -- is a
difference somebody has to say is deliberate before it ships.
"""

import ast
import os

import _families
import pytest


#: How the APIs group, per file, with why each group is its own.  The digest
#: names the shape; ``_families`` prints the shape on a mismatch, so updating
#: an entry is reading what changed and pasting the new digest beside a reason.
#:
#: ``_types.py`` is not here.  It is each API's own vocabulary of ctypes
#: typedefs and opaque handles -- nine APIs, nine genuinely different files --
#: so a shape record over it would go red on every ordinary edit and say
#: nothing.  What it does carry is the checker construction, and
#: :class:`TestAFlagThatRemovesTheCheckerIsHonoured` reads that wherever it is.
RECORDED = {
    '_errors.py': [
        (
            ('EGL',),
            '628580d1a9bc',
            'EGL raises an error class of its own from a base its own codes '
            'are numbered from, so the checker is built with both',
        ),
        (
            ('GL',),
            '99d076724a81',
            'GL_KHR_debug is GL\'s alone, so GL\'s checker is the only one '
            'offered to the debug-output path that replaces the round trip',
        ),
        (
            ('GLES1', 'GLES2', 'GLES3', 'GLSC2'),
            '7d31d7b775a5',
            'the plain form: ask this API\'s own glGetError, build a checker '
            'where there is one, and register it as this API\'s error source',
        ),
        (
            ('GLU',),
            '8257cc985329',
            'GLU is hand-maintained rather than registry-generated, so the '
            'compiled dispatch layer has no GLU module and there is no error '
            'source for it to register -- the eight APIs that do register are '
            'exactly the eight pygl_*.c the generator emits',
        ),
        (
            ('GLX',),
            'e500c187e217',
            'GLX has no getError of its own to poll, so the checker is built '
            'without one and says it needs no current context: its calls are '
            'the ones a program makes to *get* a context',
        ),
        (
            ('WGL',),
            'ca015e67e5a2',
            'WGL has nothing to poll at all, so the error source it registers '
            'is None rather than a checker that would find nothing',
        ),
    ],
    '_glgets.py': [
        (
            ('EGL', 'GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'GLX', 'WGL'),
            'c72b08ba9726',
            'one shape for all eight: the size table, and the live query for '
            'the handful of pnames whose size is itself a glGetIntegerv',
        ),
    ],
    'annotations.py': [
        (
            ('GLE',),
            '89d4dfabd309',
            'one shape in three spellings.  These differ only in naming their '
            'own namespace in an import, and a module path is compared as '
            'written -- erasing the API name there would make the one '
            '`_glgets.py` importing its own `_lookupint` differ from the '
            'seven importing the same one from GL',
        ),
        (('GLU',), '7532dc763192', 'as GLE, naming GLU'),
        (('GLUT',), '1c7fec76fdc2', 'as GLE, naming GLUT'),
    ],
    'constants.py': [
        (
            ('GLE',),
            'ad3833d14274',
            'GLE alone keeps a private `__GLE_DOUBLE`, the element type its '
            'array parameters are declared with',
        ),
        (('GLU', 'GLUT'), '72f9c1836c4e', 'constants and nothing else'),
    ],
}

#: Families deliberately outside the shape record, and why.
UNRECORDED = {
    '_types.py': 'each API\'s own ctypes vocabulary; see RECORDED above',
}


def recorded_for(name):
    return {apis: (shape, why) for apis, shape, why in RECORDED[name]}


class TestTheAPIsGroupAsRecorded:
    """A new spelling of a shared module is a difference somebody chose."""

    def test_every_family_is_recorded_or_excluded(self):
        found = sorted(_families.families())
        known = sorted(set(RECORDED) | set(UNRECORDED))
        assert found == known, (
            'a file now appears in more than one OpenGL/raw/<API>/ and this '
            'gate has no entry for it.  Add it to RECORDED with a reason per '
            'group, or to UNRECORDED with the reason it is data rather than '
            'policy.\n  found:    %s\n  recorded: %s' % (found, known)
        )

    @pytest.mark.parametrize('name', sorted(RECORDED))
    def test_the_groups_are_the_recorded_ones(self, name):
        members = _families.families()[name]
        computed = _families.partition(members)
        expected = recorded_for(name)
        complaints = []
        for apis, shape in computed:
            if apis not in expected:
                complaints.append(
                    'a group that is not recorded: %s\n%s'
                    % (', '.join(apis), _show(shape))
                )
                continue
            digest = _families.digest(shape)
            if digest != expected[apis][0]:
                complaints.append(
                    '%s changed shape (recorded %s, now %s -- %s)\n%s'
                    % (
                        ', '.join(apis),
                        expected[apis][0],
                        digest,
                        expected[apis][1],
                        _show(shape),
                    )
                )
        grouped = {apis for apis, _shape in computed}
        for apis in expected:
            if apis not in grouped:
                complaints.append(
                    'a recorded group is gone: %s -- %s'
                    % (', '.join(apis), expected[apis][1])
                )
        assert not complaints, (
            '%s no longer groups as recorded.  A change that applies to every '
            'API keeps the grouping and only moves the digests; a change that '
            'moves one API into a group of its own is the shape of defect '
            'this gate exists for -- so say which it is, in the reason beside '
            'the entry:\n\n%s' % (name, '\n\n'.join(complaints))
        )


def _show(shape):
    return '\n'.join('        %s' % line for line in shape)


class TestAFlagThatRemovesTheCheckerIsHonoured:
    """``_ErrorChecker`` is None when error checking is off, and calling None
    raises from a line naming neither the flag nor the API."""

    def _constructions(self):
        """Every ``_ErrorChecker(...)`` under ``OpenGL/raw``, with its parents."""
        for api in _families.apis():
            directory = os.path.join(_families.root(), api)
            for name in sorted(os.listdir(directory)):
                if not name.endswith('.py'):
                    continue
                path = os.path.join(directory, name)
                with open(path, encoding='utf-8') as handle:
                    tree = ast.parse(handle.read(), filename=path)
                parents = {}
                for parent in ast.walk(tree):
                    for child in ast.iter_child_nodes(parent):
                        parents[child] = parent
                for node in ast.walk(tree):
                    if not _is_a_checker_call(node):
                        continue
                    ancestors = []
                    walker = parents.get(node)
                    while walker is not None:
                        ancestors.append(walker)
                        walker = parents.get(walker)
                    yield ('%s/%s' % (api, name), ancestors, node)

    def test_every_construction_is_guarded(self):
        found = []
        for where, ancestors, node in self._constructions():
            if not any(_guards_on_the_class(one) for one in ancestors):
                found.append('%s:%s' % (where, node.lineno))
        assert not found, (
            'these build an `_ErrorChecker` without asking whether there is '
            'one to build.  `OpenGL.error._ErrorChecker` is None with '
            'PYOPENGL_ERROR_CHECKING=0 -- no checker being the point of the '
            'flag -- so the module raises `TypeError: \'NoneType\' object is '
            'not callable` on import, from a line naming neither the flag nor '
            'the API.  Write it as `if _get_error and _ErrorChecker:`, the '
            'way the others do:\n  %s' % '\n  '.join(found)
        )


def _is_a_checker_call(node):
    """Whether `node` is a call of ``_ErrorChecker(...)`` itself."""
    if not isinstance(node, ast.Call):
        return False
    name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
    return name == '_ErrorChecker'


def _guards_on_the_class(parent):
    """Whether `parent` is an ``if`` whose test reads ``_ErrorChecker``."""
    if not isinstance(parent, ast.If):
        return False
    return any(
        isinstance(child, ast.Name) and child.id == '_ErrorChecker'
        for child in ast.walk(parent.test)
    )


#: The two shapes the rule above is about, so that a change to the rule is
#: seen to keep answering.  A gate nobody has watched fail is a gate nobody
#: knows the shape of.
GUARDED = '''
from OpenGL.error import _ErrorChecker
_get_error = getattr(_p.GL, 'glGetError', None)
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker(_p, _get_error)
else:
    _error_checker = None
'''

UNGUARDED = '''
from OpenGL.error import _ErrorChecker
_get_error = getattr(_p.GLES2, 'glGetError', None)
_error_checker = _ErrorChecker(_p, _get_error)
'''


def _unguarded_calls(text):
    """The rule above, applied to a snippet rather than to the tree."""
    tree = ast.parse(text)
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    found = []
    for node in ast.walk(tree):
        if not _is_a_checker_call(node):
            continue
        ancestors = []
        walker = parents.get(node)
        while walker is not None:
            ancestors.append(walker)
            walker = parents.get(walker)
        if not any(_guards_on_the_class(one) for one in ancestors):
            found.append(node.lineno)
    return found


class TestTheRuleAnswers:
    """What the rule says about the two shapes it is written for."""

    def test_the_guarded_form_passes(self):
        assert _unguarded_calls(GUARDED) == []

    def test_the_form_that_broke_the_import_fails(self):
        """`OpenGL/raw/GLES2/_types.py` as it was when #166 was filed."""
        assert _unguarded_calls(UNGUARDED) == [4]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
