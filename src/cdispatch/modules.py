"""Describe the generated ``OpenGL/raw`` modules so they need not be files.

All but three of them are purely generated -- constants, entry-point
declarations and re-exports, with no hand-written material anywhere (the
hand-written sections all live in the friendly modules above them).  So what
each one *contains* is data, and a module object can be built from that data
on demand instead of a file being compiled, executed and kept resident.

What is emitted is a C table rather than a Python one: the constants as Python
source would cost more to import than the modules they replace, and as
``.rodata`` they cost nothing until something asks.

Read one and you get its constants, its re-exports and, for each entry point,
the signature its ``@_p.types(...)`` declaration stated.  The signature is
carried because running that declaration is what used to record the ctypes
binding a client demotes to, and nothing runs it when there is no file.
"""

import ast
import os
from dataclasses import dataclass, field

__all__ = ['RawCommand', 'RawModule', 'emit_modules', 'read_modules']


@dataclass
class RawCommand:
    """One entry-point declaration, as the data the file stated.

    The signature is carried because a client can still demote to the ctypes
    binding -- the Python layer does it wherever it derives a function whose
    arity differs from the entry point's.  Running the file used to be what
    recorded that signature, so with no file it has to be said here.
    """

    #: Its name, e.g. ``glTexImage3D``.
    name: str
    #: The parameter names, in order.
    argument_names: tuple = ()
    #: The ctypes type expressions, result first, exactly as written --
    #: ``None``, ``_cs.GLenum``, ``ctypes.c_void_p``, ``arrays.GLfloatArray``.
    #: They are resolved when a demotion asks for them and not before.
    types: tuple = ()


@dataclass
class RawModule:
    """One generated module, as the data needed to rebuild it."""

    #: Its dotted name, e.g. ``OpenGL.raw.GL.VERSION.GL_1_1``.
    name: str
    #: ``_EXTENSION_NAME``.
    extension: str = ''
    #: ``{constant name: value}``.
    constants: dict = field(default_factory=dict)
    #: The entry points it declares, as :class:`RawCommand`.
    commands: list = field(default_factory=list)
    #: Modules it re-exports with ``from ... import *``.
    reexports: list = field(default_factory=list)
    #: Set where the module does something a table cannot describe, in which
    #: case it keeps its file.
    hand_written: bool = False


def _dotted(root, path):
    relative = os.path.relpath(path, os.path.dirname(root))
    return relative[: -len('.py')].replace(os.sep, '.')


def read_module(root, path):
    """Read one generated module into the data it is made of."""
    with open(path, 'r', encoding='utf-8') as handle:
        try:
            tree = ast.parse(handle.read(), filename=path)
        except SyntaxError:
            return None
    module = RawModule(name=_dotted(root, path))
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.Expr, ast.Pass)):
            continue
        if isinstance(node, ast.ImportFrom):
            if node.names and node.names[0].name == '*' and node.module:
                module.reexports.append(node.module)
            continue
        if isinstance(node, ast.FunctionDef):
            # ``def _f(function): ...`` is the module's own binding helper.
            if node.name == '_f':
                continue
            command = _read_command(node)
            if command is None:
                module.hand_written = True
                continue
            module.commands.append(command)
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                module.hand_written = True
                continue
            if target.id == '_EXTENSION_NAME':
                try:
                    module.extension = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    module.hand_written = True
                continue
            value = _constant_value(node.value)
            if value is None:
                module.hand_written = True
                continue
            module.constants[target.id] = value
            continue
        # A class, a conditional, an assertion: not something a table says.
        module.hand_written = True
    return module


def _read_command(node):
    """``@_f @_p.types(None, _cs.GLenum, ...) def glFoo(target): pass``."""
    types = None
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue  # ``@_f``, which says only which DLL to look in
        called = getattr(decorator.func, 'attr', None)
        if called != 'types':
            return None  # something a table does not describe
        types = tuple(_type_source(argument) for argument in decorator.args)
        if any(item is None for item in types):
            return None
    if types is None:
        return None
    arguments = node.args
    if arguments.vararg or arguments.kwarg or arguments.kwonlyargs:
        return None
    names = tuple(item.arg for item in arguments.args)
    if len(types) != len(names) + 1:
        return None  # the result type plus one per parameter, or nothing said
    return RawCommand(name=node.name, argument_names=names, types=types)


#: What a type expression may be built from.  The declarations reach for the
#: GL typedefs, ctypes itself and PyOpenGL's array types, and nothing else, so
#: naming the three is what lets the text be resolved later without the
#: resolver having to trust it.
TYPE_NAMESPACES = frozenset(['_cs', 'ctypes', 'arrays'])


def _type_source(node):
    """A type expression as it was written.

    ``_cs.GLenum``, ``arrays.GLfloatArray``, ``ctypes.POINTER(_cs.GLchar)``:
    kept as text, so the table need not know what any of them mean and the
    resolving happens once, in the one process that asks.
    """
    if isinstance(node, ast.Constant) and node.value is None:
        return 'None'
    for name in ast.walk(node):
        if isinstance(name, ast.Name) and name.id not in TYPE_NAMESPACES:
            return None
        if not isinstance(
            name, (ast.Attribute, ast.Call, ast.Name, ast.Load, ast.expr_context)
        ):
            return None
    return ast.unparse(node)


def _constant_value(node):
    """The integer a ``_C('GL_FOO', 0x1234)`` names, or None."""
    if not isinstance(node, ast.Call):
        return None
    function = node.func
    called = getattr(function, 'id', None) or getattr(function, 'attr', None)
    if called not in ('_C', 'Constant', 'IntConstant'):
        return None
    if len(node.args) < 2:
        return None
    try:
        value = ast.literal_eval(node.args[1])
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, int) else None


def read_modules(package_root, apis):
    """Every generated module under ``OpenGL/raw`` that a table can describe."""
    modules = []
    raw_root = os.path.join(package_root, 'raw')
    for api in apis:
        api_root = os.path.join(raw_root, api)
        if not os.path.isdir(api_root):
            continue
        for directory, _folders, files in os.walk(api_root):
            if '__pycache__' in directory:
                continue
            for filename in sorted(files):
                if not filename.endswith('.py') or filename.startswith('_'):
                    # The private modules -- _types, _errors, _glgets -- carry
                    # classes and conditionals, and keep their files.
                    continue
                module = read_module(package_root, os.path.join(directory, filename))
                if module is not None and not module.hand_written:
                    modules.append(module)
    return modules


def _c_value(value):
    """A constant as an initialiser, and whether to read it back signed.

    The range runs from -6 to 2**64-1, which no one C integer type covers, so
    the value is held unsigned and the flag says how to read it.
    """
    if value < 0:
        return '(unsigned long long)(%dLL), 1' % (value,)
    return '%dULL, 0' % (value,)


def _c_string(value):
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return '"%s"' % (escaped,)


def emit_modules(modules):
    """The C table the module finder reads."""
    # Sorted by name, because the table is searched by name and a sorted table
    # is searchable.  The symbols are numbered in the same order, so the
    # per-module arrays line up with the rows that point at them.
    modules = sorted(modules, key=lambda module: module.name)
    lines = [
        '/* Generated by src/cdispatch -- do not edit. */',
        '#include "pygl.h"',
        '',
        '/* What each generated OpenGL/raw module contains.  Building the',
        ' * module from this costs nothing until something imports it, where a',
        ' * file costs a compile and an exec whether or not anything looks at',
        ' * it. */',
        '',
    ]
    for index, module in enumerate(modules):
        symbol = 'pygl_mod_%d' % (index,)
        if module.constants:
            lines.append('static const PyGLEnum %s_enums[] = {' % (symbol,))
            for name in sorted(module.constants):
                lines.append(
                    '    {%s, %s},' % (_c_string(name), _c_value(module.constants[name]))
                )
            lines.append('};')
        if module.commands:
            lines.append('static const PyGLDeclaration %s_commands[] = {' % (symbol,))
            for command in sorted(module.commands, key=lambda item: item.name):
                lines.append(
                    '    {%s, %s, %s},'
                    % (
                        _c_string(command.name),
                        _c_string(','.join(command.argument_names)),
                        _c_string(','.join(command.types)),
                    )
                )
            lines.append('};')
        if module.reexports:
            lines.append(
                'static const char *const %s_reexports[] = {%s};'
                % (symbol, ', '.join(_c_string(n) for n in module.reexports))
            )
        lines.append('')
    lines.append('/* In name order: pygl_module_for() binary-searches this. */')
    lines.append('const PyGLModule pygl_modules[] = {')
    for index, module in enumerate(modules):
        symbol = 'pygl_mod_%d' % (index,)
        lines.append(
            '    {%s, %s, %s, %d, %s, %d, %s, %d},'
            % (
                _c_string(module.name),
                _c_string(module.extension),
                '%s_enums' % (symbol,) if module.constants else 'NULL',
                len(module.constants),
                '%s_commands' % (symbol,) if module.commands else 'NULL',
                len(module.commands),
                '%s_reexports' % (symbol,) if module.reexports else 'NULL',
                len(module.reexports),
            )
        )
    lines.append('    {NULL, NULL, NULL, 0, NULL, 0, NULL, 0}')
    lines.append('};')
    lines.append('const Py_ssize_t pygl_module_count = %d;' % (len(modules),))
    lines.append('')
    return '\n'.join(lines)


#: Where the shipped declarations live, one file per API, relative to the
#: package root.  The C extension holds the same facts in ``.rodata``; this is
#: what the pure-Python path reads when no extension was built.
DECLARATIONS = os.path.join('raw', '_declarations')


def emit_declarations(modules):
    """The declarations as data, keyed by API.

    ``marshal`` because it is the fastest thing in the standard library at
    reading a nest of dicts, tuples and ints back, and because what is written
    here is written by the generator and read by us -- there is no format to
    agree with anyone about.  It is regenerated whenever the C is, so the two
    cannot drift.
    """
    import marshal

    by_api = {}
    for module in modules:
        api = module.name.split('.')[2]
        # Each module's declarations are marshalled on their own, so that
        # reading the file is reading an index: a program using forty modules
        # should not parse the other twelve hundred to find them.
        by_api.setdefault(api, {})[module.name] = marshal.dumps(
            (
                module.extension,
                dict(module.constants),
                tuple(
                    (command.name, command.argument_names, command.types)
                    for command in module.commands
                ),
                tuple(module.reexports),
            ),
            4,
        )
    return by_api


def write_declarations(package_root, modules):
    """Write one marshalled file per API, and say what was written."""
    import marshal

    directory = os.path.join(package_root, DECLARATIONS)
    os.makedirs(directory, exist_ok=True)
    written = {}
    for api, contents in sorted(emit_declarations(modules).items()):
        path = os.path.join(directory, '%s.dat' % (api,))
        with open(path, 'wb') as handle:
            marshal.dump(contents, handle, 4)
        written[api] = os.path.getsize(path)
    return written
