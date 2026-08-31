"""Read the generated PyOpenGL tree into command records.

The shipped ``OpenGL/raw`` modules say which commands exist, in which feature
or extension, with which types and argument names.  The friendly modules above
them say what each one promises its callers.  Both are read here, by AST rather
than by import, so that extraction needs no GL context and no working build.

This is Phase 1 of ``plans/C-DISPATCH.md``: the annotations stop living inside
the generated files and become the data file every later phase reads.
"""

import ast
import os

from . import model
from .ctypes_model import CType, parse_type

__all__ = [
    'extract_tree',
    'extract_raw',
    'extract_friendly',
    'extract_constants',
]

#: ``arrays.GLuintArray`` and friends name a pointer to their element type.
_ARRAY_ELEMENT = {
    'GLfloatArray': 'GLfloat',
    'GLclampfArray': 'GLclampf',
    'GLdoubleArray': 'GLdouble',
    'GLintArray': 'GLint',
    'GLuintArray': 'GLuint',
    'GLsizeiArray': 'GLsizei',
    'GLshortArray': 'GLshort',
    'GLushortArray': 'GLushort',
    'GLbyteArray': 'GLbyte',
    'GLubyteArray': 'GLubyte',
    'GLbooleanArray': 'GLboolean',
    'GLcharArray': 'GLchar',
    'GLcharARBArray': 'GLcharARB',
    'GLint64Array': 'GLint64',
    'GLuint64Array': 'GLuint64',
    'GLfixedArray': 'GLfixed',
    'GLhalfNVArray': 'GLhalfNV',
    'GLintptrArray': 'GLintptr',
    'GLsizeiptrArray': 'GLsizeiptr',
    'GLvoidpArray': 'void *',
    'EGLAttribArray': 'GLintptr',
    'ArrayDatatype': 'void',
}

#: Where each Tier 3 family is defined, so the extractor can name the helper
#: that will implement it in C rather than guessing from the customisations.
_HELPER_FILES = {
    'images.py': 'image',
    'imaging.py': 'image',
    'GL_1_2_images.py': 'image',
    'pointers.py': 'client_pointer',
    'exceptional.py': 'variadic',
}

#: Customisations that cannot be expressed as declarative table data.
_HAND_WRITTEN = frozenset(
    [
        'setPyConverter',
        'setCConverter',
        'setCResolver',
        'setStoreValues',
        'setReturnValues',
        'setImageInput',
        'setDimensionsAsInts',
    ]
)


def _literal(node):
    """The Python value of a literal node, or ``_UNKNOWN``."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return _UNKNOWN


class _Unknown:
    def __repr__(self):
        return '_UNKNOWN'


_UNKNOWN = _Unknown()


# ---------------------------------------------------------------- raw modules


def _ctype_from_node(node):
    """Turn a ``_p.types`` argument into a :class:`CType`."""
    if isinstance(node, ast.Constant) and node.value is None:
        return CType('void')
    if isinstance(node, ast.Attribute):
        owner = node.value
        if isinstance(owner, ast.Name):
            if owner.id == '_cs':
                return parse_type(node.attr)
            if owner.id == 'arrays':
                element = _ARRAY_ELEMENT.get(node.attr)
                if element is None:
                    return CType('void', 1)
                if element.endswith(' *'):
                    return CType(element[:-2].strip(), 2)
                return CType(element, 1)
            if owner.id == 'ctypes':
                return _ctypes_name(node.attr)
    if isinstance(node, ast.Name):
        return parse_type(node.id)
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr == 'POINTER':
            inner = _ctype_from_node(node.args[0])
            return CType(inner.base, inner.pointers + 1, inner.const)
    return CType('void', 1)


def _ctypes_name(name):
    simple = {
        'c_void_p': CType('void', 1),
        'c_char_p': CType('GLchar', 1),
        'c_int': CType('int'),
        'c_uint': CType('unsigned int'),
        'c_float': CType('float'),
        'c_double': CType('double'),
        'c_short': CType('GLshort'),
        'c_ushort': CType('GLushort'),
        'c_byte': CType('GLbyte'),
        'c_ubyte': CType('GLubyte'),
        'c_int64': CType('GLint64'),
        'c_uint64': CType('GLuint64'),
        'c_ssize_t': CType('GLintptr'),
        'c_size_t': CType('GLsizeiptr'),
    }
    return simple.get(name, CType('void', 1))


def _module_constant(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = _literal(node.value)
                    if value is not _UNKNOWN:
                        return value
    return None


def extract_raw(path, api):
    """Every entry point declared in one ``OpenGL/raw`` module."""
    with open(path, 'r', encoding='utf-8') as handle:
        source = handle.read()
    tree = ast.parse(source, filename=path)
    feature = _module_constant(tree, '_EXTENSION_NAME') or ''
    commands = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        types = None
        bound = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == '_f':
                bound = True
            elif isinstance(decorator, ast.Call):
                function = decorator.func
                if isinstance(function, ast.Attribute) and function.attr == 'types':
                    types = decorator.args
        if types is None or not bound:
            continue
        return_type = _ctype_from_node(types[0])
        arg_types = [_ctype_from_node(item) for item in types[1:]]
        arg_names = [argument.arg for argument in node.args.args]
        if len(arg_names) != len(arg_types):
            # A declaration whose types and names disagree is a defect in the
            # generated file; skip it rather than emit a stub that cannot be
            # called correctly.
            continue
        commands[node.name] = model.Command(
            name=node.name,
            return_type=return_type,
            parameters=[
                model.Parameter(name=name, ctype=ctype)
                for name, ctype in zip(arg_names, arg_types)
            ],
            feature=feature,
            api=api,
        )
    return commands


# ----------------------------------------------------------- friendly modules


def _size_from_node(node, arg_index):
    """Interpret a ``size=`` argument.

    The whole space is a constant tuple, the ``_glgets`` table, or a lambda
    that is an argument index and a divisor.
    """
    if isinstance(node, ast.Attribute) and node.attr == '_glget_size_mapping':
        return 'glget'
    if isinstance(node, ast.Lambda):
        body = node.body
        if isinstance(body, ast.Tuple) and len(body.elts) == 1:
            body = body.elts[0]
        if isinstance(body, ast.Name):
            return 1
        if (
            isinstance(body, ast.BinOp)
            and isinstance(body.op, ast.FloorDiv)
            and isinstance(body.right, ast.Constant)
        ):
            return int(body.right.value)
        return _UNKNOWN
    value = _literal(node)
    if isinstance(value, tuple) and len(value) == 1:
        return ('fixed', int(value[0]))
    if isinstance(value, int):
        return ('fixed', int(value))
    return _UNKNOWN


def _call_chain(node):
    """Unwind ``wrapper.wrapper(x).setA(...).setB(...)`` into its calls."""
    calls = []
    while isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute):
            calls.append((function.attr, node))
            node = function.value
        else:
            break
    calls.reverse()
    return calls


def extract_friendly(path):
    """The customisations one friendly module applies, keyed by command name."""
    with open(path, 'r', encoding='utf-8') as handle:
        source = handle.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return {}
    helper = _HELPER_FILES.get(os.path.basename(path))
    found = {}

    def record(name, entry):
        found.setdefault(name, {'annotations': [], 'helper': '', 'file': path})
        found[name].update(
            {
                key: value
                for key, value in entry.items()
                if key != 'annotations'
            }
        )
        found[name]['annotations'].extend(entry.get('annotations', []))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if not targets:
                continue
            name = targets[0]
            if not name.startswith(('gl', 'wgl', 'glX', 'egl')):
                continue
            calls = _call_chain(node.value)
            if calls and calls[0][0] == 'wrapper':
                annotations = []
                hand = ''
                for method, call in calls[1:]:
                    if method in _HAND_WRITTEN:
                        hand = helper or 'converter'
                    elif method == 'setOutput':
                        annotations.append(('output', call))
                    elif method == 'setInputArraySize':
                        annotations.append(('input', call))
                record(
                    name,
                    {'annotations': annotations, 'helper': hand, 'file': path},
                )
            elif helper:
                # A module that owns a Tier 3 family rebinds its commands in
                # whatever shape suits it -- ``setDimensionsAsInts(setImageInput(
                # ...))`` rather than a wrapper chain -- so the assignment
                # itself is what marks the family, not the call it is made of.
                record(name, {'annotations': [], 'helper': helper, 'file': path})
        elif isinstance(node, ast.FunctionDef) and node.name.startswith(
            ('gl', 'wgl', 'egl')
        ):
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                attribute = getattr(target, 'attr', None) or getattr(target, 'id', None)
                if attribute in ('lazy', '_lazy'):
                    record(
                        node.name,
                        {'annotations': [], 'helper': helper or 'variadic',
                         'file': path},
                    )
    return found


def _apply_annotations(command, entry):
    """Fold one module's customisations into the command record."""
    by_name = {parameter.name: index for index, parameter in enumerate(command.parameters)}
    if entry.get('helper'):
        command.helper = entry['helper']
    order = 0
    for kind, call in entry['annotations']:
        arguments = {
            keyword.arg: keyword.value for keyword in call.keywords if keyword.arg
        }
        positional = call.args
        if not positional:
            continue
        name = _literal(positional[0])
        if name is _UNKNOWN or name not in by_name:
            continue
        parameter = command.parameters[by_name[name]]
        if kind == 'input':
            size_node = positional[1] if len(positional) > 1 else arguments.get('size')
            value = _literal(size_node) if size_node is not None else None
            if isinstance(value, int) and not isinstance(value, bool):
                parameter.size = model.Fixed(int(value))
            elif value is _UNKNOWN:
                command.helper = command.helper or 'converter'
            continue
        # setOutput
        parameter.direction = model.OUT
        parameter.output_order = order
        order += 1
        pname = arguments.get('pnameArg')
        size_node = arguments.get('size') or (
            positional[1] if len(positional) > 1 else None
        )
        if size_node is None:
            parameter.size = model.Fixed(1)
            continue
        interpreted = _size_from_node(size_node, by_name)
        if interpreted is _UNKNOWN:
            command.helper = command.helper or 'converter'
        elif interpreted == 'glget':
            index = by_name.get(_literal(pname)) if pname is not None else None
            if index is None:
                command.helper = command.helper or 'converter'
            else:
                parameter.size = model.GLGetTable(pname_argument=index)
        elif isinstance(interpreted, tuple):
            parameter.size = model.Fixed(interpreted[1])
        else:
            index = by_name.get(_literal(pname)) if pname is not None else None
            if index is None:
                command.helper = command.helper or 'converter'
            else:
                parameter.size = model.FromArg(argument=index, divisor=interpreted)


#: The registry-defined APIs.  GLU, GLUT and GLE are hand-maintained rather
#: than registry-generated and stay on the ctypes path, as the plan's scope
#: says; ``osmesa`` is a platform binding rather than a drawing API.
APIS = ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'GLX', 'WGL', 'EGL')


def _is_core_feature(feature):
    """Whether a feature name is a core version rather than an extension."""
    return bool(feature) and 'VERSION' in feature.split('_')


def _prefer(existing, candidate):
    """Which of two declarations of the same command to keep.

    A command promoted into core is declared twice: once by the extension that
    introduced it and once by the version that adopted it.  The core
    declaration is the one to keep, because it resolves without an extension
    check -- a context that has the function but does not advertise the old
    extension string still gets it.
    """
    if _is_core_feature(existing.feature) and not _is_core_feature(candidate.feature):
        return existing
    if _is_core_feature(candidate.feature) and not _is_core_feature(existing.feature):
        return candidate
    # Both core or both extensions: the earlier version wins, so that a
    # command adopted in 4.1 is not re-attributed to 4.6.
    return existing if existing.feature <= candidate.feature else candidate


def _api_for_path(root, path):
    """Which API namespace a friendly module customises.

    ``OpenGL/GL/VERSION/GL_1_1.py`` customises GL; ``OpenGL/GLES2/...``
    customises GLES2.  The same command name lives in several of them with
    different bindings, so the namespace is part of a command's identity.
    """
    relative = os.path.relpath(path, root).split(os.sep)
    if relative and relative[0] in APIS:
        return relative[0]
    return None


#: Where the vendored Khronos registry lives, relative to the package root's
#: parent.  Absent in a source checkout that has not fetched it, in which case
#: the name-based fallback below still covers the shipped families.
_REGISTRY_FILES = ('gl.xml', 'glx.xml', 'wgl.xml')


def _registry_lengths(registry_root):
    """``{command name: {parameter: len}}`` from the Khronos registry.

    The registry says how each parameter is sized.  Reading it here is what
    stops a command whose sizing the generator cannot express from being
    emitted as though it were pass-through.
    """
    lengths = {}
    if not registry_root or not os.path.isdir(registry_root):
        return lengths
    try:
        import xmlreg
    except ImportError:
        return lengths
    for name in _REGISTRY_FILES:
        path = os.path.join(registry_root, name)
        if not os.path.exists(path):
            continue
        try:
            registry = xmlreg.parse(path)
        except Exception:
            continue
        for command in registry.command_set.values():
            if command.lengths:
                lengths.setdefault(command.name, {}).update(command.lengths)
    return lengths


def _is_image_length(length):
    """A ``COMPSIZE`` that depends on the pixel format is an image.

    Its size is a function of format, type, the dimensions and the current
    pixel-store state, which is the largest genuine computation in the friendly
    layer and one of the Tier 3 families.
    """
    if not length or not length.startswith('COMPSIZE'):
        return False
    variables = length[len('COMPSIZE'):].strip('()').split(',')
    return any(variable.strip() in ('format', 'type', 'imageSize') for variable in variables)


#: Commands whose sizing the registry describes but the shipped tree does not,
#: matched by name because they take a compressed image whose size is given
#: explicitly rather than computed.
_IMAGE_PREFIXES = ('glCompressedTex', 'glCompressedMultiTex', 'glGetCompressedTex')


def _apply_registry(commands, registry_root):
    lengths = _registry_lengths(registry_root)
    for (api, name), command in commands.items():
        if command.helper:
            continue
        if name.startswith(_IMAGE_PREFIXES):
            command.helper = 'image'
            continue
        for parameter, length in lengths.get(name, {}).items():
            if _is_image_length(length):
                command.helper = 'image'
                break


def extract_tree(root, registry_root=None):
    """Every command PyOpenGL ships, with the friendly layer's annotations.

    Keyed by ``(api, name)``: ``glTexImage2D`` exists in both GL and GLES2 as
    separate bindings resolved from separate libraries, so the name alone does
    not identify an entry point.
    """
    commands = {}
    raw_root = os.path.join(root, 'raw')
    for api in APIS:
        api_root = os.path.join(raw_root, api)
        if not os.path.isdir(api_root):
            continue
        for directory, _folders, files in os.walk(api_root):
            if '__pycache__' in directory:
                continue
            for name in sorted(files):
                if not name.endswith('.py'):
                    continue
                for command_name, command in extract_raw(
                    os.path.join(directory, name), api
                ).items():
                    key = (api, command_name)
                    existing = commands.get(key)
                    if existing is not None and _prefer(existing, command) is existing:
                        continue
                    commands[key] = command

    for directory, _folders, files in os.walk(root):
        if 'raw' in directory.split(os.sep) or '__pycache__' in directory:
            continue
        api = _api_for_path(root, directory)
        if api is None:
            continue
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = os.path.join(directory, name)
            for command_name, entry in extract_friendly(path).items():
                command = commands.get((api, command_name))
                if command is not None:
                    _apply_annotations(command, entry)

    if registry_root is None:
        registry_root = os.path.join(
            os.path.dirname(os.path.abspath(root)), 'src', 'khronosapi', 'xml'
        )
    _apply_registry(commands, registry_root)
    _mark_retained(commands)
    return commands


def api_view(commands, api):
    """The commands of one API, keyed by bare name."""
    return {
        name: command for (owner, name), command in commands.items() if owner == api
    }


#: The client-array family: the GL reads the memory after the call returns, so
#: the argument and its buffer must outlive the call.  Losing this is a
#: segfault rather than a leak.
_RETAINING = (
    'Pointer',
    'glDrawElements',
    'glDrawRangeElements',
    'glMultiDrawElements',
    'glInterleavedArrays',
)


def _mark_retained(commands):
    for key, command in commands.items():
        name = key[1] if isinstance(key, tuple) else key
        if command.helper != 'client_pointer' and not any(
            name.startswith(prefix) or name == prefix for prefix in _RETAINING
        ):
            continue
        for parameter in command.parameters:
            if parameter.is_array and parameter.direction == model.IN:
                parameter.retain = True


def extract_constants(root):
    """``{api: [constant name]}`` for every enum the raw modules define.

    The stubs need these: the enums are most of what a caller writes, and a
    stub that declared only the functions would make a type checker reject
    correct code.
    """
    constants = {}
    raw_root = os.path.join(root, 'raw')
    for api in APIS:
        api_root = os.path.join(raw_root, api)
        if not os.path.isdir(api_root):
            continue
        names = set()
        for directory, _folders, files in os.walk(api_root):
            if '__pycache__' in directory:
                continue
            for filename in sorted(files):
                if not filename.endswith('.py'):
                    continue
                path = os.path.join(directory, filename)
                with open(path, 'r', encoding='utf-8') as handle:
                    try:
                        tree = ast.parse(handle.read(), filename=path)
                    except SyntaxError:
                        continue
                for node in tree.body:
                    if not isinstance(node, ast.Assign):
                        continue
                    if not isinstance(node.value, ast.Call):
                        continue
                    function = node.value.func
                    called = getattr(function, 'id', None) or getattr(
                        function, 'attr', None
                    )
                    if called not in ('_C', 'Constant', 'IntConstant'):
                        continue
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isidentifier():
                            names.add(target.id)
        constants[api] = sorted(names)
    return constants
