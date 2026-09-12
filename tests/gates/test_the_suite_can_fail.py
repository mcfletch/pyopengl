#! /usr/bin/env python3
"""A test that cannot fail is worse than no test: it is a claim nobody checks.

Every rule here is a shape this suite has actually had, and each one produced a
green run over something broken:

* ``pytest.raises(Exception)`` is satisfied by a typo in the case.
* ``@pytest.fixture`` under ``@staticmethod`` hands pytest an object carrying
  no fixture marker, so the fixture is simply not there and the cases asking
  for it error at setup.
* A module-scope import of a library the machine may not have is a *collection*
  error, and pytest abandons the whole run rather than the one module -- four
  modules reaching for EGL, and a ``parametrize`` argument importing numpy, each
  cost a run that reported nothing about anything else.
* ``from numpy import *`` brings numpy's own ``test`` object into the module
  namespace, and pytest refuses to collect a module-level ``test`` that is not
  a function -- again a collection error rather than a result.
* A case naming a script that is not there skips for as long as nobody looks.
* A blanket ``tolerate_glerror()`` passes with every call in the block failing.
* A skip with no reason is a number in a summary and nothing else.

These are questions about the text, so they are asked of every module at once
rather than waiting for the configuration that runs it.
"""

import ast
import os

import pytest
import sources


def collected():
    """The modules pytest collects: ``test_*.py`` under ``tests/``."""
    return [
        module
        for module in sources.suite()
        if os.path.basename(module.relative).startswith('test_')
    ]


def _decorator_names(node):
    """The spelling of each decorator on `node`, outermost first."""
    names = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute):
            names.append(target.attr)
        elif isinstance(target, ast.Name):
            names.append(target.id)
        else:
            names.append('')
    return names


class TestAnAssertionNamesWhatItExpects:
    """``Exception`` is every mistake the case itself could make."""

    def test_no_bare_exception_is_asserted(self):
        found = []
        for module in collected():
            for node in sources.calls(
                module.tree, 'raises', 'assertRaises', 'assertRaisesRegex'
            ):
                if not node.args:
                    continue
                named = sources.dotted(node.args[0]) or getattr(
                    node.args[0], 'id', None
                )
                if named in ('Exception', 'BaseException'):
                    found.append('%s: %s' % (module.where(node), named))
        assert not found, (
            'these assert that something raises `Exception`, which a typo in '
            'the case satisfies as well as the defect it is about.  Name the '
            'exception the code under test is documented to raise:\n  %s'
            % '\n  '.join(found)
        )


class TestAFixtureIsRegistered:
    """``pytest.fixture`` has to be the outer decorator."""

    def test_fixture_is_the_outermost_decorator(self):
        found = []
        for module in collected() + list(sources.suite()):
            for node in ast.walk(module.tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                names = _decorator_names(node)
                if 'fixture' not in names:
                    continue
                wrapping = [
                    index
                    for index, name in enumerate(names)
                    if name in ('staticmethod', 'classmethod')
                ]
                if wrapping and min(wrapping) < names.index('fixture'):
                    found.append('%s: %s' % (module.where(node), node.name))
        assert not found, (
            '`@pytest.fixture` is applied under `@staticmethod` or '
            '`@classmethod` here, so what pytest is handed is the descriptor '
            'and carries no fixture marker -- the fixture is not registered '
            'and every case asking for it errors at setup.  Put '
            '`@pytest.fixture` outermost, or move the fixture to module '
            'scope:\n  %s' % '\n  '.join(sorted(set(found)))
        )


#: Libraries a machine this suite runs on may not have, and the reason each is
#: optional.  Importing one of these while a test module is being *imported*
#: is a collection error, which ends the run rather than the module -- so an
#: import of one has to sit behind a guard that skips the module first.
#:
#: ``OpenGL.GLES1``, ``GLES2`` and ``GLES3`` are deliberately not here: the
#: platform answers None for an entry point the machine has no library for, so
#: importing the namespace is an ordinary success everywhere and the ES suite
#: imports it at module scope.  ``OpenGL.EGL`` is the opposite by design -- it
#: raises ImportError naming the missing library, because ``try: from OpenGL
#: import EGL`` is how a program asks whether the machine has EGL.
OPTIONAL_AT_MODULE_SCOPE = {
    'numpy': 'the num0 environments run without it; use `from arraycompat import np`',
    'OpenGL.EGL': 'EGL ships with the graphics driver, and macOS has none',
    'pygame': 'the pygame backend is absent below 3.11 and wherever SDL is not built',
    'glfw': 'a headless machine has no windowing library to load',
    'Xlib': 'X11 is one display server among several, and Windows has none',
    'gbm': 'libgbm is Linux graphics infrastructure',
}


def _imported_at_module_scope(module):
    """``[(name, node)]`` for what `module` imports before anything runs."""
    found = []
    for node in module.tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.module, node))
            for alias in node.names:
                found.append(('%s.%s' % (node.module, alias.name), node))
    return found


def _guarded_from(module):
    """The line from which this module has already said it may not run.

    ``pytest.importorskip(...)`` and ``pytest.skip(..., allow_module_level=
    True)`` are the two ways a module declines to be imported here, and both
    have to come *before* the import they are protecting.  Everything after
    the first of them is reached only on a machine that got past it.
    """
    earliest = None
    for node in ast.walk(module.tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, 'attr', None) or getattr(node.func, 'id', None)
        if name == 'importorskip' or (
            name in ('skip', 'exit')
            and sources.keyword(node, 'allow_module_level') is not None
        ):
            if earliest is None or node.lineno < earliest:
                earliest = node.lineno
    return earliest


class TestACollectionErrorEndsTheRun:
    """What a module reaches for while being imported is every module's risk."""

    def test_no_optional_library_is_imported_at_module_scope(self):
        found = []
        for module in collected():
            guarded_from = _guarded_from(module)
            for name, node in _imported_at_module_scope(module):
                if name not in OPTIONAL_AT_MODULE_SCOPE:
                    continue
                if guarded_from is not None and node.lineno > guarded_from:
                    continue
                found.append(
                    '%s: %s -- %s'
                    % (module.where(node), name, OPTIONAL_AT_MODULE_SCOPE[name])
                )
        assert not found, (
            'these import a library the machine may not have while the module '
            'is being imported, with nothing above them to skip the module '
            'first.  That is a collection error, and pytest ends the whole '
            'run on one rather than reporting the module that could not be '
            'collected.  `pytest.importorskip(name, exc_type=ImportError)` '
            'above the import is how the modules that do this already say '
            'it:\n  %s' % '\n  '.join(sorted(set(found)))
        )

    def test_no_star_import_from_outside_the_package(self):
        """``from numpy import *`` brought numpy's own ``test`` object in.

        pytest refuses to collect a module-level ``test`` that is not a
        function, so the module was a collection error on the one platform
        that runs it.  Star imports from ``OpenGL`` are how a GL program is
        written and are used throughout; the rule is about everything else.
        """
        found = []
        for module in collected():
            for node in module.tree.body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                if not any(alias.name == '*' for alias in node.names):
                    continue
                origin = node.module or ''
                if origin == 'OpenGL' or origin.startswith('OpenGL.'):
                    continue
                found.append('%s: from %s import *' % (module.where(node), origin))
        assert not found, (
            'a star import from outside the package puts names nobody wrote '
            'into a module pytest then collects:\n  %s' % '\n  '.join(found)
        )


class TestASkipSaysWhy:
    """A skip with no reason is a number in a summary."""

    def test_every_skip_carries_a_reason(self):
        found = []
        for module in sources.suite():
            for node in sources.calls(module.tree, 'skip', 'skipTest', 'xfail'):
                if node.args or sources.keyword(node, 'reason'):
                    continue
                found.append(module.where(node))
            for node in sources.calls(module.tree, 'skipif'):
                if not sources.keyword(node, 'reason'):
                    found.append(module.where(node))
        assert not found, (
            'these skip without saying what the machine lacked.  `-ra` prints '
            'the reasons at the end of a run, which is how a skip that is '
            'really a defect gets noticed:\n  %s' % '\n  '.join(found)
        )


class TestForgivenessIsNamed:
    """A block that tolerates any GL error passes with every call failing."""

    def test_tolerate_glerror_names_the_codes(self):
        found = []
        for module in sources.suite():
            for node in sources.calls(module.tree, 'tolerate_glerror'):
                if not node.args:
                    found.append(module.where(node))
        assert not found, (
            '`tolerate_glerror()` with no codes forgives everything the '
            'driver can say, so the block passes with every call in it '
            'failing.  Name the codes, or use `exercise(reason)`, which '
            'tolerates the three a driver uses to decline an entry point and '
            'records what it forgave:\n  %s' % '\n  '.join(found)
        )


class TestANamedFileIsThere:
    """A case naming a script that is not there skips until somebody looks.

    ``TestTeapotRegression`` in OpenGLContext drove a script deleted seven
    weeks earlier, so both its cases had been skipping ever since while
    claiming to cover teapot rendering under both profiles.  Nothing said so
    until the run was asked to print its skip reasons.

    A *written path* is what this reads: a literal with a directory in it and
    a ``.py`` on the end.  A bare basename is usually a suffix handed to
    ``endswith`` or a name joined onto a directory worked out at run time, and
    reading those as paths finds nothing but noise.
    """

    #: Where a path written in the suite may be relative to: the checkout, the
    #: suite, the package, and the companion distribution.
    ROOTS = (
        sources.paths.ROOT,
        sources.paths.TESTS,
        sources.paths.PACKAGE,
        os.path.join(sources.paths.ROOT, 'accelerate'),
    )

    def _resolves(self, module, text):
        if os.path.isabs(text):
            return True
        here = os.path.dirname(module.path)
        for root in self.ROOTS + (here,):
            if os.path.exists(os.path.join(root, text)):
                return True
        return False

    def test_every_script_a_case_names_exists(self):
        found = []
        for module in sources.suite():
            for node in ast.walk(module.tree):
                text = sources.literal(node)
                if not text or not text.endswith('.py'):
                    continue
                if '/' not in text:
                    continue  # a basename or a suffix, not a written path
                if any(character in text for character in '%{}* '):
                    continue  # a format string or a glob, not a written path
                if not self._resolves(module, text):
                    found.append('%s: %r' % (module.where(node), text))
        assert not found, (
            'these name a Python file that is not in the checkout.  A case '
            'driving a script that was deleted skips for as long as nobody '
            'reads the reasons:\n  %s' % '\n  '.join(sorted(set(found)))
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
