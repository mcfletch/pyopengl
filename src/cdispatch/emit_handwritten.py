"""Stubs for the hand-maintained APIs: GLU, GLUT and GLE.

None of the three is in the Khronos registry, so each is written by hand rather
than generated, and the registry-driven emitter has nothing to say about any of
them.  Their declarations are still perfectly regular --
``platform.createBaseFunction`` with ``argTypes`` and ``argNames``, ``Constant``
with a name and a value, ``GLUTCallback`` with the signature the library calls
back on -- so a stub is read out of the source.  Read rather than run, because
what a machine loads depends on which libraries are installed and the stub has
to describe the API on every machine.

One shape cannot be read that way.  ``OpenGL.wrapper`` builds several GLE and
GLU entry points by *removing* arguments from the C form -- ``gleExtrusion``
takes five where the C entry point takes seven, because both counts are read
off the arrays passed with them -- and the rule for which arguments go lives in
the wrapper machinery.  Restating that rule here would be a second copy of it,
and a second copy that drifts is what put the wrong signature on
``glDeleteTextures``.  So the *names* of those arguments come from the wrapper
itself, through ``pyConverterNames``, which it works out as it is built.  That
is not machine-dependent: an entry point whose library is missing still carries
the argument names its declaration gave it.

``emit_handwritten`` is called from :mod:`regenerate_c`; :func:`declarations` is
the part worth reading.
"""

import ast
import os

from . import emit_pyi

__all__ = ['declarations', 'emit_handwritten', 'emit_api', 'APIS',
           'CTYPES_ANNOTATION']

#: The modules that make up each namespace, in the order the package imports
#: them -- a later one shadowing an earlier one is how freeglut replaces a GLUT
#: entry point and how ``GLU/tess.py`` replaces ``gluTessVertex``, so order
#: decides.
APIS = {
    'GLUT': [
        'raw/GLUT/constants.py',
        'raw/GLUT/__init__.py',
        'GLUT/special.py',
        'GLUT/fonts.py',
        'GLUT/freeglut.py',
        'GLUT/osx.py',
    ],
    'GLU': [
        'raw/GLU/constants.py',
        'raw/GLU/__init__.py',
        'raw/GLU/annotations.py',
        'GLU/quadrics.py',
        'GLU/projection.py',
        'GLU/tess.py',
        'GLU/glunurbs.py',
    ],
    'GLE': [
        'raw/GLE/constants.py',
        'raw/GLE/__init__.py',
        'raw/GLE/annotations.py',
        'GLE/exceptional.py',
    ],
}

#: What an entry point of each library is called.  Selecting by name is what
#: separates the API from the machinery sharing its namespace -- ``ctypes``,
#: ``platform``, ``arrays`` and the rest arrive there by import.
PREFIXES = {
    'GLUT': ('glut', 'fg', 'GLUT_'),
    'GLU': ('glu', 'GLU_'),
    'GLE': ('gle', 'GLE_', 'rot_', 'urot_', 'uview'),
}

#: What each ctypes type in a declaration looks like to a caller.  A small
#: closed vocabulary: these declarations were written by hand against the
#: libraries' headers, and the headers use a handful of scalar types.
CTYPES_ANNOTATION = {
    'c_int': 'int', 'c_uint': 'int', 'c_ubyte': 'int', 'c_short': 'int',
    'c_ushort': 'int', 'c_long': 'int', 'c_ulong': 'int',
    'c_float': 'float', 'c_double': 'float',
    'c_char_p': 'bytes | str', 'STRING': 'bytes | str',
    'c_void_p': 'Any',
    'GLint': 'int', 'GLuint': 'int', 'GLenum': 'int', 'GLsizei': 'int',
    'GLboolean': 'int', 'GLbitfield': 'int', 'GLubyte': 'int',
    'GLfloat': 'float', 'GLdouble': 'float', 'GLclampf': 'float',
    'GLclampd': 'float', 'gleDouble': 'float',
    'None': 'None',
}

_PREAMBLE = '''"""OpenGL.%(api)s -- generated; regenerate with src/regenerate_c.py.

%(api)s is hand-maintained rather than registry-generated (it is not a Khronos
API), so this is emitted from the declarations in ``OpenGL/raw/%(api)s`` and
``OpenGL/%(api)s`` rather than from the registry.
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


#: A name a stub may use, spelled the way the registry-driven emitter spells
#: it: the two write into one package, and a parameter renamed in one and not
#: the other is a name a caller cannot pass.
_parameter = emit_pyi.parameter_name


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


def _lazy_wrapper(node):
    """The stub line for a ``@_lazy``-decorated wrapper, or None.

    ``lazy`` binds the entry point as the wrapper's first parameter, so that
    one is not a parameter a caller passes.  Nothing else records the call the
    wrapper takes; its own parameter list is it.
    """
    for decorator in node.decorator_list:
        function = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not (isinstance(function, ast.Name) and function.id in ('_lazy', 'lazy')):
            continue
        arguments = node.args.posonlyargs + node.args.args
        if not arguments:                       # pragma: no cover - would take none
            return None
        supplied = arguments[1:]                # the entry point is bound already
        defaults = node.args.defaults
        first_default = len(supplied) - len(defaults)
        declared = [
            '%s: Any%s' % (_parameter(argument.arg),
                           ' = ...' if index >= first_default else '')
            for index, argument in enumerate(supplied)
        ]
        return 'def %s(%s) -> Any: ...' % (node.name, ', '.join(declared))
    return None


def _factory_declaration(node, lines):
    """Declare ``name = factory(...)`` into ``lines``, by the factory called.

    A closed set of four, matched on the last segment of the call rather than
    by suffix: each is reached through whichever module the file imported it
    from -- ``platform.createBaseFunction``, a bare ``Constant`` -- while a
    suffix test would take ``enums.MyConstant`` for ``Constant`` and declare a
    wrapper as an integer.  Anything else is left to the readers that follow.
    """
    name = node.targets[0].id
    call = node.value
    called = ast.unparse(call.func).rsplit('.', 1)[-1]
    if called == 'createBaseFunction':
        _name, arguments, result = _base_function(name, call)
        lines[name] = 'def %s(%s) -> %s: ...' % (
            name, ', '.join(arguments), result)
    elif called == 'Constant':
        lines[name] = '%s: int' % (name,)
    elif called == 'GLUTCallback':
        # The wrapper takes the function GLUT will call back on, and answers
        # the one it replaced -- which is how a program puts a callback back
        # when it is done with its own.
        lines[name] = ('def %s(function: Callable[..., Any] | None)'
                       ' -> Any: ...' % (name,))
    elif called == 'GLUTTimerCallback':
        lines[name] = ('def %s(milliseconds: int,'
                       ' function: Callable[..., Any] | None,'
                       ' value: int) -> Any: ...' % (name,))


def _wrapper_built(package_root, api):
    """{name: line} for the entry points ``OpenGL.wrapper`` reshapes.

    These take fewer arguments than the C form, and which ones go is decided by
    the wrapper as it is built.  Asking it is the only account of that which
    cannot drift from the one a caller meets.

    An API that will not import stops the generation rather than answering
    "none".  A stub written without these carries the C form of every call a
    program makes with fewer arguments -- which is the defect that cost
    4.0.0a4 a re-release over ``glDeleteTextures`` -- and it would be written
    with the run reporting success.
    """
    lines = {}
    try:
        module = __import__('OpenGL.%s' % (api,), {}, {}, ['*'])
    except Exception as err:
        raise RuntimeError(
            'OpenGL.%s could not be imported, so the entry points its wrapper '
            'reshapes cannot be read; a stub written now would declare the C '
            'form of each of them. Install what %s needs and generate again. '
            '(%s: %s)' % (api, api, type(err).__name__, err)) from err
    for name in dir(module):
        if name.startswith('_') or not name.startswith(PREFIXES[api]):
            continue
        entry_point = getattr(module, name)
        argument_names = getattr(entry_point, 'pyConverterNames', None)
        if argument_names is None:
            continue
        declared = ['%s: Any' % (_parameter(argument),)
                    for argument in argument_names]
        lines[name] = 'def %s(%s) -> Any: ...' % (name, ', '.join(declared))
    return lines


def declarations(package_root, api):
    """{name: line} for everything ``OpenGL.<api>`` offers, in module order.

    A later module shadowing an earlier one is how freeglut replaces a GLUT
    entry point and how ``GLU/tess.py`` replaces ``gluTessVertex``, so a later
    declaration wins -- which is what the namespace does at import time.
    """
    lines = {}
    prefixes = PREFIXES[api]
    for relative in APIS[api]:
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
                    and target.id.startswith(prefixes)):
                # freeglut writes some of its own as bare numbers rather than
                # through Constant; they are constants all the same.
                lines[target.id] = '%s: int' % (target.id,)
                continue
            if (isinstance(node.value, (ast.Name, ast.BinOp, ast.Attribute))
                    and target.id.startswith(prefixes)):
                # A ctypes type under an API name: `gleDouble = c_double`, and
                # `gleAffine`, the 2x3 transform GLE's lathes are steered with.
                # What a caller does is build one and pass it back.
                lines[target.id] = '%s: Any' % (target.id,)
                continue
            if not isinstance(node.value, ast.Call):
                continue
            _factory_declaration(node, lines)
        for name, line in _hand_written(tree, prefixes).items():
            lines[name] = line
    # The wrapper-built forms outrank the C ones they were built over, and the
    # hand-shaped table outranks everything: it describes calls no declaration
    # in the tree does.
    lines.update(_wrapper_built(package_root, api))
    lines.update({name: line for name, line in HAND_SHAPED.items()
                  if name.startswith(prefixes)})
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


def _hand_written(tree, prefixes):
    """Module-level ``def``s and classes a module offers under an API name.

    Also the API names it imports from elsewhere: ``GLUT_GUARD_CALLBACKS`` is a
    configuration flag that lives in ``OpenGL.platform`` and reaches a caller
    through that namespace like any other.
    """
    lines = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                if name.startswith(prefixes) and name.isupper():
                    lines[name] = '%s: int' % (name,)
            continue
        if isinstance(node, ast.ClassDef) and node.name.startswith(prefixes):
            # A GLU handle -- a tessellator, a quadric, a NURBS renderer.  What
            # a caller does with one is pass it back, so the name is what
            # matters and the body is the library's business.
            lines[node.name] = 'class %s: ...' % (node.name,)
            continue
        if not isinstance(node, ast.FunctionDef) or node.name.startswith('_'):
            continue
        if not node.name.startswith(prefixes):
            continue
        lazy = _lazy_wrapper(node)
        if lazy is not None:
            lines[node.name] = lazy
            continue
        arguments = node.args.posonlyargs + node.args.args
        defaults = node.args.defaults
        first_default = len(arguments) - len(defaults)
        declared = [
            '%s: Any%s' % (_parameter(argument.arg),
                           ' = ...' if index >= first_default else '')
            for index, argument in enumerate(arguments)
        ]
        if node.args.vararg:
            declared.append('*%s: Any' % (node.args.vararg.arg,))
        lines[node.name] = 'def %s(%s) -> Any: ...' % (
            node.name, ', '.join(declared))
    return lines


def emit_api(package_root, api):
    """Write one ``OpenGL/<api>/__init__.pyi``; answers how many names it holds."""
    lines = declarations(package_root, api)
    classes = sorted(name for name in lines if lines[name].startswith('class '))
    constants = sorted(name for name in lines
                       if not lines[name].startswith(('def ', 'class ')))
    functions = sorted(name for name in lines if lines[name].startswith('def '))
    body = [lines[name] for name in classes]
    if classes:
        body.append('')
    body += [lines[name] for name in constants]
    body.append('')
    body += [lines[name] for name in functions]
    path = os.path.join(package_root, api, '__init__.pyi')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(_PREAMBLE % {'api': api})
        handle.write('\n'.join(body))
        handle.write(_EPILOGUE)
    return len(lines)


def emit_handwritten(package_root):
    """Write a stub for each hand-maintained API; answers ``{api: name count}``."""
    return {api: emit_api(package_root, api) for api in sorted(APIS)}
