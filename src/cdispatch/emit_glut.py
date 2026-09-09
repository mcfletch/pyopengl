"""The stub for ``OpenGL.GLUT``, read out of the declarations themselves.

GLUT is not in the Khronos registry, so it is hand-maintained rather than
generated and the registry-driven emitter has nothing to say about it.  Its
declarations are still perfectly regular, though -- ``createBaseFunction`` with
``argTypes`` and ``argNames``, ``Constant`` with a name and a value,
``GLUTCallback`` with the signature the library will call back on -- so the
stub is read from the source rather than from a running import.  Read rather
than run, because what a machine loads depends on which GLUT is installed, and
the stub has to describe the API on every machine.

``emit_glut`` is called from :mod:`regenerate_c`; :func:`declarations` is the
part worth reading.
"""

import ast
import os

__all__ = ['declarations', 'emit_glut', 'MODULES', 'CTYPES_ANNOTATION']

#: The modules that make up ``OpenGL.GLUT``'s namespace, in the order the
#: package imports them -- a later one shadowing an earlier one is how freeglut
#: replaces a GLUT entry point, so order decides.
MODULES = [
    'raw/GLUT/constants.py',
    'raw/GLUT/__init__.py',
    'GLUT/special.py',
    'GLUT/fonts.py',
    'GLUT/freeglut.py',
    'GLUT/osx.py',
]

#: What each ctypes type in a GLUT declaration looks like to a caller.  A small
#: closed vocabulary: these declarations were written by hand against the GLUT
#: headers, and the headers use a handful of scalar types.
CTYPES_ANNOTATION = {
    'c_int': 'int', 'c_uint': 'int', 'c_ubyte': 'int', 'c_short': 'int',
    'c_ushort': 'int', 'c_long': 'int', 'c_ulong': 'int',
    'c_float': 'float', 'c_double': 'float',
    'c_char_p': 'bytes | str', 'STRING': 'bytes | str',
    'c_void_p': 'Any',
    'GLint': 'int', 'GLuint': 'int', 'GLenum': 'int', 'GLsizei': 'int',
    'GLboolean': 'int', 'GLbitfield': 'int',
    'GLfloat': 'float', 'GLdouble': 'float', 'GLclampf': 'float',
    'GLclampd': 'float',
    'None': 'None',
}

_PREAMBLE = '''"""OpenGL.GLUT -- generated; regenerate with src/regenerate_c.py.

GLUT is hand-maintained rather than registry-generated (it is not a Khronos
API), so this is emitted from the declarations in ``OpenGL/raw/GLUT`` and
``OpenGL/GLUT`` rather than from the registry.
"""

from collections.abc import Callable, Sequence
from typing import Any

from OpenGL.raw.GL._types import *

'''

_EPILOGUE = '''

def __getattr__(name: str) -> Any: ...
'''


def _annotation(expression):
    """What a caller may pass for one declared argument type."""
    text = expression.strip()
    if text.startswith(('ctypes.', '_simple.', 'arrays.', 'constant.',
                        'platform.', 'special.')):
        text = text.split('.', 1)[1]
    if text in CTYPES_ANNOTATION:
        return CTYPES_ANNOTATION[text]
    if text.startswith('POINTER(') or text.endswith('Array'):
        # A pointer argument takes whatever PyOpenGL's array handling accepts,
        # which is far wider than one ctypes type: a sequence, a numpy array, a
        # ctypes buffer, or None for an output the call allocates.
        return 'Any'
    if 'FUNCTION_TYPE' in text or text.endswith('functype'):
        return 'Callable[..., Any] | None'
    return 'Any'


def _keyword(call, name):
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _base_function(node, call):
    """(name, arguments, result) for a ``createBaseFunction`` binding."""
    types_node = _keyword(call, 'argTypes')
    names_node = _keyword(call, 'argNames')
    result_node = _keyword(call, 'resultType')
    types = ([ast.unparse(element) for element in types_node.elts]
             if isinstance(types_node, (ast.List, ast.Tuple)) else [])
    names = ([ast.unparse(element).strip('\'"') for element in names_node.elts]
             if isinstance(names_node, (ast.List, ast.Tuple)) else [])
    if len(names) != len(types):                # a declaration naming nothing
        names = ['arg%d' % (index,) for index in range(len(types))]
    arguments = ['%s: %s' % (_parameter(name), _annotation(kind))
                 for name, kind in zip(names, types)]
    result = _annotation(ast.unparse(result_node)) if result_node else 'Any'
    return node, arguments, result


def _parameter(name):
    """A name a stub may use: registry and header names include keywords."""
    import keyword as keyword_module
    if keyword_module.iskeyword(name) or not name.isidentifier():
        return '%s_' % (name,)
    return name


def _font_names(tree):
    """The font pointers ``fonts.py`` writes into its own globals.

    They are loaded in a loop over a literal list and assigned through
    ``globals()``, so there is no assignment naming them -- the list is the
    declaration.
    """
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.For) and isinstance(node.iter, ast.List)):
            continue
        for element in node.iter.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append(element.value)
    return found


def declarations(package_root):
    """{name: line} for everything ``OpenGL.GLUT`` offers, in module order.

    A later module shadowing an earlier one is how freeglut replaces a GLUT
    entry point, so a later declaration wins -- which is what the namespace
    does at import time.
    """
    lines = {}
    for relative in MODULES:
        path = os.path.join(package_root, relative)
        if not os.path.exists(path):            # pragma: no cover - a partial tree
            continue
        with open(path, encoding='utf-8') as handle:
            tree = ast.parse(handle.read(), filename=path)
        for name in _font_names(tree):
            lines[name] = '%s: Any' % (name,)
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name) or target.id.startswith('_'):
                continue
            if (isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, (int, bool))
                    and target.id.startswith('GLUT')):
                # freeglut writes some of its own as bare numbers rather than
                # through Constant; they are constants all the same.
                lines[target.id] = '%s: int' % (target.id,)
                continue
            if not isinstance(node.value, ast.Call):
                continue
            name, call = target.id, node.value
            called = ast.unparse(call.func)
            if called.endswith('createBaseFunction'):
                _name, arguments, result = _base_function(name, call)
                lines[name] = 'def %s(%s) -> %s: ...' % (
                    name, ', '.join(arguments), result)
            elif called.endswith('Constant'):
                lines[name] = '%s: int' % (name,)
            elif called.endswith('GLUTCallback'):
                # The wrapper takes the function GLUT will call back on, and
                # answers the one it replaced -- which is how a program puts a
                # callback back when it is done with its own.
                lines[name] = ('def %s(function: Callable[..., Any] | None)'
                               ' -> Any: ...' % (name,))
            elif called.endswith('GLUTTimerCallback'):
                lines[name] = ('def %s(milliseconds: int,'
                               ' function: Callable[..., Any] | None,'
                               ' value: int) -> Any: ...' % (name,))
        for name, line in _hand_written(tree).items():
            lines[name] = line
    lines.update(HAND_SHAPED)
    return lines


#: Entry points whose Python form is not the C one, and which no declaration in
#: the tree describes: each is a class or a wrapper written for the call a
#: program actually makes.
HAND_SHAPED = {
    'glutInit': 'def glutInit(*args: Any) -> Sequence[Any]: ...',
    'glutCheckLoop': 'def glutCheckLoop() -> Any: ...',
    'glutCreateMenu': ('def glutCreateMenu(function: Callable[..., Any] | None)'
                       ' -> int: ...'),
    'glutDestroyMenu': 'def glutDestroyMenu(menu: int) -> Any: ...',
    'glutDestroyWindow': 'def glutDestroyWindow(window: int) -> Any: ...',
    'glutSolidSierpinskiSponge': (
        'def glutSolidSierpinskiSponge(levels: int, offset: Any,'
        ' scale: float) -> None: ...'),
    'glutWireSierpinskiSponge': (
        'def glutWireSierpinskiSponge(levels: int, offset: Any,'
        ' scale: float) -> None: ...'),
}


def _hand_written(tree):
    """Module-level ``def``s a GLUT module offers under a ``glut`` name.

    Also the GLUT names it imports from elsewhere: ``GLUT_GUARD_CALLBACKS`` is
    a configuration flag that lives in ``OpenGL.platform`` and reaches a caller
    through this namespace like any other.
    """
    lines = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                if name.startswith('GLUT_'):
                    lines[name] = '%s: int' % (name,)
            continue
        if not isinstance(node, ast.FunctionDef) or node.name.startswith('_'):
            continue
        if not node.name.startswith(('glut', 'GLUT')):
            continue
        arguments = node.args.posonlyargs + node.args.args
        declared = ['%s: Any' % (_parameter(argument.arg),)
                    for argument in arguments]
        if node.args.vararg:
            declared.append('*%s: Any' % (node.args.vararg.arg,))
        lines[node.name] = 'def %s(%s) -> Any: ...' % (
            node.name, ', '.join(declared))
    return lines


def emit_glut(package_root):
    """Write ``OpenGL/GLUT/__init__.pyi``; answers how many names it declares."""
    lines = declarations(package_root)
    constants = sorted(name for name in lines if not lines[name].startswith('def '))
    functions = sorted(name for name in lines if lines[name].startswith('def '))
    body = [lines[name] for name in constants]
    body.append('')
    body += [lines[name] for name in functions]
    path = os.path.join(package_root, 'GLUT', '__init__.pyi')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(_PREAMBLE)
        handle.write('\n'.join(body))
        handle.write(_EPILOGUE)
    return len(lines)
