#! /usr/bin/env python3
"""An entry point called through ctypes says what it takes and what it answers.

ctypes is lenient in exactly the wrong direction.  A function with no
``argtypes`` accepts any arguments at all, and one with no ``restype`` answers
a C ``int`` -- half the width of a handle on a 64-bit Windows.  Both went
wrong here at once: ``OpenGL.Tk``'s Windows implementation reached ``GetDC``,
``SetPixelFormat`` and the rest through ``ctypes.windll`` with nothing
declared, so every ``HDC`` lost its top half and ``SetPixelFormat``, taking a
truncated one, refused the format for a window that was perfectly good.

Three declarations in ``OpenGL/raw/osmesa/mesa.py`` had the same shape and were
invisible for the same reason, and ``_GLXQuerier.getDisplay`` handed
``XOpenDisplay`` a ``str`` where the C takes ``char *``: with no ``argtypes``
ctypes passes ``wchar_t *``, the connection fails, and the querier answers GLX
version ``[0, 0]`` with an empty extension list -- which is the gate every GLX
entry point is resolved through.

None of these fails on the machine most of us develop on, because none of them
is on Linux.  A parser reads them anywhere.

What this does *not* cover is ``platform.createBaseFunction``, which takes
``resultType`` and ``argTypes`` as arguments and so cannot be written without
them, and builds a function of its own rather than setting a prototype on the
library's -- a shared ``ctypes.windll`` object would otherwise carry this
package's signatures under whoever else in the process calls through it.
"""

import ast

import pytest
import sources

#: How a ctypes library object is made.
LOADERS = frozenset(['WinDLL', 'CDLL', 'OleDLL', 'PyDLL', 'LoadLibrary'])

#: The process-wide library caches.  ``ctypes.windll.gdi32`` is one object
#: shared with every other library in the process that asks for it.
SHARED = frozenset(['windll', 'cdll', 'oledll', 'pydll'])

#: A helper in this package that answers a library with its prototypes already
#: declared.  Named so that its callers are read as holding a library.
HELPERS = frozenset(['windowsLibrary'])


def _bound_name(target):
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def libraries(tree):
    """``{name: how}`` for every name bound to a ctypes library object."""
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        how = None
        if isinstance(value, ast.Call):
            called = getattr(value.func, 'attr', None) or getattr(
                value.func, 'id', None
            )
            if called in LOADERS or called in HELPERS:
                how = called
        elif isinstance(value, ast.Attribute):
            base = _bound_name(value.value)
            if base in SHARED:
                how = 'ctypes.%s.%s' % (base, value.attr)
        if how is None:
            continue
        for target in targets:
            spelled = _bound_name(target)
            if spelled:
                found[spelled] = how
    return found


def called_through(tree, held):
    """``{entryPoint: lineno}`` for calls made through one of `held`."""
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if _bound_name(node.func.value) not in held:
            continue
        found.setdefault(node.func.attr, node.lineno)
    return found


def sets_a_prototype(tree):
    """Whether the module assigns ``argtypes`` or ``restype`` anywhere."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr in (
                'argtypes',
                'restype',
            ):
                return True
    return False


def undeclared(tree):
    """``[(entryPoint, lineno)]`` called through a library with no prototype."""
    held = libraries(tree)
    if not held:
        return []
    callees = called_through(tree, held)
    if not callees:
        return []
    if not sets_a_prototype(tree):
        return sorted(callees.items())
    # A name is declared where it appears other than as the thing being
    # called: as a string in a signature table, or as the attribute a
    # prototype is set on.  Both forms are in this tree --
    # ``OpenGL/Tk/win32.py`` carries a ``SIGNATURES`` dict keyed by
    # ``(library, name)`` and applies it in a loop, and
    # ``OpenGL/WGL/offscreen.py`` names ``self.user32.RegisterClassW`` in a
    # tuple and sets ``argtypes`` over it -- and neither can be followed by
    # looking only at the call site.
    mentioned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value in callees:
            mentioned.add(node.value)
        elif isinstance(node, ast.Attribute) and node.attr in callees:
            if not _is_a_callee(tree, node):
                mentioned.add(node.attr)
    return sorted((name, line) for name, line in callees.items()
                  if name not in mentioned)


def _is_a_callee(tree, attribute):
    """Whether this attribute node is the thing a Call calls."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.func is attribute:
            return True
    return False


class TestEveryForeignCallIsDeclared:
    def test_nothing_calls_through_an_undeclared_prototype(self):
        found = []
        for module in sources.package():
            for name, line in undeclared(module.tree):
                found.append('%s:%s: %s' % (module.relative, line, name))
        assert not found, (
            'these reach a foreign function through a ctypes library and say '
            'nothing about its signature.  With no `argtypes` ctypes converts '
            'by guessing -- a `str` crosses as `wchar_t *` where the C wants '
            '`char *` -- and with no `restype` it reads the answer as a C '
            '`int`, which on 64-bit Windows loses the top half of every '
            'handle.  Declare them beside the call, or in a signature table '
            'the way `OpenGL/Tk/win32.py` does:\n  %s' % '\n  '.join(found)
        )


#: The shape the rule is written for, so a change to the rule is seen to keep
#: answering.  The first is `OpenGL/Tk/win32.py` before the prototypes were
#: declared: a 64-bit `HDC` read back as a C `int`.
UNDECLARED = '''
import ctypes
gdi32 = ctypes.WinDLL('gdi32')
def swap(hdc):
    return gdi32.SwapBuffers(hdc)
'''

DECLARED_INLINE = '''
import ctypes
gdi32 = ctypes.WinDLL('gdi32')
gdi32.SwapBuffers.argtypes = [ctypes.c_void_p]
gdi32.SwapBuffers.restype = ctypes.c_int
def swap(hdc):
    return gdi32.SwapBuffers(hdc)
'''

DECLARED_BY_TABLE = '''
import ctypes
SIGNATURES = {('gdi32', 'SwapBuffers'): (ctypes.c_int, [ctypes.c_void_p])}
gdi32 = ctypes.WinDLL('gdi32')
for (where, entryPoint), (restype, argtypes) in SIGNATURES.items():
    declared = getattr(gdi32, entryPoint)
    declared.restype = restype
    declared.argtypes = argtypes
def swap(hdc):
    return gdi32.SwapBuffers(hdc)
'''


class TestTheRuleAnswers:
    def test_an_undeclared_call_is_found(self):
        assert undeclared(ast.parse(UNDECLARED)) == [('SwapBuffers', 5)]

    def test_a_prototype_beside_the_call_passes(self):
        assert undeclared(ast.parse(DECLARED_INLINE)) == []

    def test_a_signature_table_passes(self):
        assert undeclared(ast.parse(DECLARED_BY_TABLE)) == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
