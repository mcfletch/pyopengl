"""Generate the EGL bindings from the EGL registry.

Khronos publishes EGL as its own repository, and nothing in PyOpenGL was
reading it: the shipped tree carried 116 of the 158 commands the registry
declares.  The 41 that were absent were not absent for a reason -- there was
simply nothing looking.  ``src/fetch_registries.py`` now fetches
``EGL-Registry`` beside the OpenGL one, and this turns it into bindings.

What is emitted is what the existing generated EGL modules look like, because
the point is that a reader cannot tell which of them came from here:

* ``OpenGL/raw/EGL/<VENDOR>/<name>.py`` -- the declarations and constants;
* ``OpenGL/EGL/<VENDOR>/<name>.py`` -- the friendly module, which under the
  table-driven layer is a ``define()`` call and an availability check.

Where the registry names a type ``OpenGL/raw/EGL/_types.py`` does not define,
:func:`undefined_types` reports it rather than the emitter guessing: a wrong
type is a crash in someone's driver, and there are only a handful of them.
"""

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

__all__ = [
    'read', 'ctypes_for', 'missing_commands', 'by_extension', 'undefined_types',
    'emit_raw', 'emit_friendly', 'module_path', 'write_missing',
]


@dataclass
class Command:
    """One entry point as the registry declares it."""

    name: str
    result: str
    argument_names: tuple = ()
    argument_types: tuple = ()


@dataclass
class Registry:
    """What ``egl.xml`` says."""

    commands: dict = field(default_factory=dict)
    #: ``{command: the feature or extension that declares it}``
    owner: dict = field(default_factory=dict)
    #: ``{extension: {constant: value}}``
    constants: dict = field(default_factory=dict)


def _text_of(node):
    """A ``<proto>`` or ``<param>`` as the C text it stands for."""
    return ''.join(node.itertext()).strip()


def _type_of(node):
    """The type half of a ``<param>``: everything but the name."""
    name = node.find('name')
    text = _text_of(node)
    if name is not None and name.text:
        # The name is always the tail of the declaration.
        index = text.rfind(name.text)
        if index >= 0:
            text = text[:index] + text[index + len(name.text):]
    return re.sub(r'\s+', ' ', text).strip()


#: ``EGL_CAST(EGLnsecsANDROID,-1)`` -- the registry's way of writing a value
#: that carries a type.  The older generator could not express these and
#: emitted them commented out, so they defined nothing at all.
_CAST = re.compile(r'^\s*EGL_CAST\s*\(\s*[^,]+,\s*(-?\w+)\s*\)\s*$')


def _value_of(text):
    """The integer an enum value denotes, or None where it is not one.

    A cast is written for its value: what a caller compares against is the
    number, and every one of these is a sentinel -- zero for "no object",
    -1 for "don't care".
    """
    if text is None:
        return None
    match = _CAST.match(text)
    if match:
        text = match.group(1)
    text = text.strip()
    try:
        int(text, 0)
    except ValueError:
        return None
    return text


def read(path):
    """Read the registry into commands, ownership and constants."""
    root = ET.parse(path).getroot()
    registry = Registry()

    for node in root.findall('commands/command'):
        proto = node.find('proto')
        if proto is None or proto.find('name') is None:
            continue
        name = proto.find('name').text
        registry.commands[name] = Command(
            name=name,
            result=_type_of(proto),
            argument_names=tuple(
                p.find('name').text for p in node.findall('param')
                if p.find('name') is not None
            ),
            argument_types=tuple(
                _type_of(p) for p in node.findall('param')
                if p.find('name') is not None
            ),
        )

    values = {
        enum.get('name'): _value_of(enum.get('value'))
        for enum in root.findall('enums/enum')
        if enum.get('name')
    }
    for group in list(root.findall('extensions/extension')) + list(
        root.findall('feature')
    ):
        label = group.get('name')
        for command in group.findall('.//command'):
            registry.owner.setdefault(command.get('name'), label)
        holder = registry.constants.setdefault(label, {})
        for enum in group.findall('.//enum'):
            name = enum.get('name')
            if name in values and values[name] is not None:
                holder[name] = values[name]
    return registry


# ------------------------------------------------------------------ types

#: A scalar whose pointer form is one of PyOpenGL's array types.  These are the
#: only ones the registry uses in EGL, and naming them is what keeps the
#: mapping honest: anything else is reported rather than guessed at.
_ARRAY_FOR = {
    'EGLint': 'arrays.GLintArray',
    'EGLAttrib': 'arrays.EGLAttribArray',
    'EGLuint64KHR': 'arrays.GLuint64Array',
    'EGLTime': 'arrays.GLuint64Array',
    'EGLTimeKHR': 'arrays.GLuint64Array',
    'EGLuint64NV': 'arrays.GLuint64Array',
    'EGLnsecsANDROID': 'arrays.GLint64Array',
}

#: Written as a plain pointer: a handle the caller passes back to us, or a
#: struct belonging to somebody else's library.
_VOID_POINTER = 'ctypes.c_void_p'


def _base(text):
    """``const  EGLint *`` -> ``EGLint``, and how many stars followed."""
    cleaned = text.replace('const', ' ').replace('struct', ' ')
    stars = cleaned.count('*')
    cleaned = cleaned.replace('*', ' ')
    parts = cleaned.split()
    return (parts[0] if parts else ''), stars


def ctypes_for(text):
    """The ctypes expression a declaration writes for this C type."""
    base, stars = _base(text)
    if not base or base == 'void':
        return 'None' if not stars else _VOID_POINTER
    if not stars:
        if base == 'char':
            return 'ctypes.c_char_p'
        return '_cs.%s' % (base,)
    if base == 'char':
        # ``const char *`` is a string; ``char **`` is a list of them.
        return 'ctypes.c_char_p' if stars == 1 else 'ctypes.POINTER(ctypes.c_char_p)'
    if stars == 1 and base in _ARRAY_FOR:
        return _ARRAY_FOR[base]
    # A pointer to a handle, or to a foreign struct: an address either way.
    if stars == 1 and base.startswith('EGL'):
        return 'arrays.GLvoidpArray'
    return _VOID_POINTER


def undefined_types(registry, package_root, only_missing=False):
    """Types the registry names that ``EGL/_types.py`` does not define.

    Every command by default, not only the ones without bindings: three
    ``EGL_KHR_debug`` entry points had declarations that named
    ``EGLDEBUGPROCKHR``, which nothing defined, so they could not be built at
    all -- and looking only at what was missing would never have found them.
    """
    path = os.path.join(package_root, 'raw', 'EGL', '_types.py')
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            source = handle.read()
    except OSError:
        return set()
    # Parsed rather than matched: the file chains its assignments --
    # ``EGLImageKHR = EGLImage = _opaque_pointer_cls('EGLImageKHR')`` -- and a
    # pattern that reads only the first name reports the others as undefined.
    import ast

    defined = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.ClassDef):
            # A struct is written as a class -- EGLClientPixmapHI is one.
            defined.add(node.name)
    needed = set()
    names = (
        missing_commands(registry, package_root)
        if only_missing
        else sorted(registry.commands)
    )
    for name in names:
        command = registry.commands[name]
        for text in (command.result,) + command.argument_types:
            base, _stars = _base(text)
            if base and base.startswith('EGL') and base not in defined:
                needed.add(base)
    return needed


# ------------------------------------------------------------------ what is absent


def _shipped(package_root):
    """Every EGL entry point the tree already declares.

    From the declaration table, and from any module still shipped beside it.
    """
    from . import extract

    names = {
        command.name
        for _module, declared in extract.read_declarations(package_root, 'EGL')
        for command in declared.values()
    }
    root = os.path.join(package_root, 'raw', 'EGL')
    for directory, folders, files in os.walk(root):
        if '__pycache__' in directory:
            continue
        for filename in files:
            if not filename.endswith('.py'):
                continue
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                names.update(re.findall(r'^def (egl\w+)\(', f.read(), re.M))
    return names


def missing_commands(registry, package_root):
    """Registry commands with no binding, in a stable order."""
    return sorted(set(registry.commands) - _shipped(package_root))


def by_extension(registry, names):
    """``{extension: [command, ...]}`` for the commands given."""
    groups = {}
    for name in names:
        groups.setdefault(registry.owner.get(name, 'EGL_VERSION_1_0'), []).append(name)
    return {key: sorted(value) for key, value in groups.items()}


def module_path(extension):
    """``EGL_WL_bind_wayland_display`` -> ``('WL', 'bind_wayland_display')``."""
    parts = extension.split('_', 2)
    return (parts[1], parts[2]) if len(parts) > 2 else ('VERSION', extension)


# ------------------------------------------------------------------ emission

_RAW_HEADER = """'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.EGL import _types as _cs
# End users want this...
from OpenGL.raw.EGL._types import *
from OpenGL.raw.EGL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = '%(extension)s'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.EGL,'%(extension)s',error_checker=_errors._error_checker)
"""


def emit_raw(registry, extension, names=None):
    """The declarations module for one extension."""
    lines = [_RAW_HEADER % {'extension': extension}]
    for name, value in sorted(registry.constants.get(extension, {}).items()):
        lines.append("%s=_C('%s',%s)" % (name, name, value))
    if names is None:
        names = sorted(
            name for name, owner in registry.owner.items() if owner == extension
        )
    for name in names:
        command = registry.commands[name]
        types = [ctypes_for(command.result)] + [
            ctypes_for(text) for text in command.argument_types
        ]
        lines.append('@_f')
        lines.append('@_p.types(%s)' % (','.join(types),))
        lines.append(
            'def %s(%s):pass' % (name, ','.join(command.argument_names))
        )
    return '\n'.join(lines) + '\n'


_FRIENDLY = '''\'\'\'OpenGL extension %(vendor)s.%(short)s

This module customises the behaviour of the
OpenGL.raw.EGL.%(vendor)s.%(short)s to provide a more
Python-friendly API

The official definition of this extension is available here:
https://www.khronos.org/registry/EGL/extensions/%(vendor)s/%(extension)s.txt
\'\'\'
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.EGL import _types, _glgets
from OpenGL._declarations import define as _define
_EXTENSION_NAME = _define(globals(), 'OpenGL.raw.EGL.%(vendor)s.%(short)s')

def eglInit%(camel)s():
    \'\'\'Return boolean indicating whether this extension is available\'\'\'
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )


### END AUTOGENERATED SECTION
'''


def _camel(vendor, short):
    """``WL, bind_wayland_display`` -> ``BindWaylandDisplayWL``."""
    return ''.join(part.title() for part in short.split('_')) + vendor


def emit_friendly(registry, extension):
    """The friendly module for one extension."""
    vendor, short = module_path(extension)
    return _FRIENDLY % {
        'vendor': vendor,
        'short': short,
        'extension': extension,
        'camel': _camel(vendor, short),
    }


def write_missing(registry, package_root, dry_run=False):
    """Write a module for every extension whose commands are absent.

    Returns the paths written.  An extension that already has a raw module --
    because the tree carries its constants but not its entry points -- has the
    declarations appended rather than the file replaced, so nothing
    hand-written is lost.
    """
    written = []
    groups = by_extension(registry, missing_commands(registry, package_root))
    for extension, names in sorted(groups.items()):
        vendor, short = module_path(extension)
        raw = os.path.join(package_root, 'raw', 'EGL', vendor, short + '.py')
        friendly = os.path.join(package_root, 'EGL', vendor, short + '.py')

        if os.path.exists(raw):
            # Keep what is there; add only the declarations it lacks.
            with open(raw, 'r', encoding='utf-8') as handle:
                existing = handle.read()
            addition = emit_raw(registry, extension, names)
            body = addition.split("error_checker=_errors._error_checker)\n", 1)[-1]
            text = existing.rstrip('\n') + '\n' + body
        else:
            text = emit_raw(registry, extension, names)
        if not dry_run:
            _write(raw, text)
        written.append(raw)

        if not os.path.exists(friendly):
            if not dry_run:
                _write(friendly, emit_friendly(registry, extension))
            written.append(friendly)
    return written


def _write(path, text):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    package = os.path.join(directory, '__init__.py')
    if not os.path.exists(package):
        with open(package, 'w', encoding='utf-8') as handle:
            handle.write('')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)
