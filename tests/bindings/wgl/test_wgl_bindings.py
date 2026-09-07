"""Every WGL entry point, extension and type the registry declares is bound.

WGL is the namespace whose breakages only show on the platform that uses it,
and it is the one an ordinary run never touches: a Linux or macOS suite imports
none of it.  What a declaration *is* -- the name, the type it names, the module
it lives in -- is a static question that answers on any platform, so these run
everywhere and a Linux run catches a Windows-only breakage before it ships.

Calling the entry points is a separate matter, and needs a device context;
tests/test_wgl.py does that on Windows.

The registry offers a command through a ``<require>`` in a feature or an
extension.  A ``<command>`` that no feature and no extension requires is
declared but not offered -- ``wglGetDefaultProcAddress`` is one, an ICD-facing
entry point -- so the offered set is what is read here rather than every
command element in the file.
"""

import ctypes
import importlib
import os
import xml.etree.ElementTree as ElementTree

import paths
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT
WGL_XML = os.path.join(ROOT, 'src', 'khronosapi', 'xml', 'wgl.xml')

pytestmark = pytest.mark.skipif(
    not os.path.exists(WGL_XML),
    reason='no OpenGL registry checked out; run python src/fetch_registries.py',
)

#: An extension name has to become a Python module path, and two of them start
#: with a digit, which no identifier may.  The vendor tag loses the leading
#: digits: WGL_3DFX_multisample is OpenGL.raw.WGL.DFX.multisample.
VENDOR_RENAMES = {'3DFX': 'DFX', '3DL': 'DL'}


def _registry():
    """``(extensions, commands, enums, types)`` as the registry offers them."""
    root = ElementTree.parse(WGL_XML).getroot()

    extensions = {}
    commands = {}
    enums = {}
    offering = [(e.get('name'), e) for e in root.findall('./extensions/extension')]
    offering += [(f.get('name'), f) for f in root.findall('./feature')]
    for name, element in offering:
        extensions.setdefault(name, None)
        for require in element.findall('./require'):
            for command in require.findall('./command'):
                commands[command.get('name')] = name
            for enum in require.findall('./enum'):
                enums[enum.get('name')] = name
    # A feature is not an extension; only the extensions have their own module.
    for feature in root.findall('./feature'):
        extensions.pop(feature.get('name'), None)

    types = []
    for entry in root.findall('./types/type'):
        named = entry.get('name')
        if named is None:
            element = entry.find('name')
            named = element.text if element is not None else None
        if named:
            types.append(named)
    return extensions, commands, enums, types


if os.path.exists(WGL_XML):
    EXTENSIONS, COMMANDS, ENUMS, TYPES = _registry()
else:  # pragma: no cover - the whole module is skipped
    EXTENSIONS, COMMANDS, ENUMS, TYPES = {}, {}, set(), []


def module_for(owner):
    """The raw module that declares what ``owner`` offers.

    ``owner`` is a feature name (WGL_VERSION_1_0) or an extension name
    (WGL_ARB_pbuffer).
    """
    if owner.startswith('WGL_VERSION_'):
        return 'OpenGL.raw.WGL.VERSION.WGL_%s' % (
            owner[len('WGL_VERSION_') :].replace('.', '_'),
        )
    _wgl, vendor, rest = owner.split('_', 2)
    return 'OpenGL.raw.WGL.%s.%s' % (VENDOR_RENAMES.get(vendor, vendor), rest)


class TestTheRegistrySurfaceIsDeclared:
    """What the registry offers, the tree declares."""

    @pytest.mark.parametrize('name', sorted(EXTENSIONS))
    def test_the_extension_has_a_module(self, name):
        importlib.import_module(module_for(name))

    @pytest.mark.parametrize('name', sorted(COMMANDS))
    def test_the_command_is_bound(self, name):
        module = importlib.import_module(module_for(COMMANDS[name]))
        assert getattr(module, name, None) is not None, name

    @pytest.mark.parametrize('name', sorted(ENUMS))
    def test_the_enum_has_a_constant(self, name):
        module = importlib.import_module(module_for(ENUMS[name]))
        assert hasattr(module, name), name

    @pytest.mark.parametrize('name', TYPES)
    def test_the_type_is_defined(self, name):
        """A type the registry names has to resolve, or the modules using it fail.

        A handle type absent from ``_types`` is not a quiet gap: the module
        that names it raises AttributeError while it is being built, so the
        whole extension is unreachable.  ``VOID`` is defined as None, which is
        what ctypes spells "no return value", so this asks whether the name is
        there rather than what it holds.
        """
        from OpenGL.raw.WGL import _types

        assert hasattr(_types, name), name


class TestEveryModuleImports:
    """The friendly modules are what a caller reaches for."""

    @pytest.mark.parametrize('name', sorted(EXTENSIONS))
    def test_the_friendly_module_imports(self, name):
        importlib.import_module(module_for(name).replace('OpenGL.raw.', 'OpenGL.'))

    def test_the_core_module_imports(self):
        importlib.import_module('OpenGL.WGL.VERSION.WGL_1_0')


class TestReturnTypesAreDeclared:
    """A handle returned as a plain int is a handle with its top half gone."""

    def test_wglgetcurrentdc_returns_a_device_context(self):
        from OpenGL.raw.WGL import _types
        from OpenGL.WGL import wglGetCurrentDC

        assert wglGetCurrentDC.restype is _types.HDC

    def test_wglgetcurrentcontext_returns_a_render_context(self):
        from OpenGL.raw.WGL import _types
        from OpenGL.WGL import wglGetCurrentContext

        assert wglGetCurrentContext.restype is _types.HGLRC

    def test_a_handle_is_pointer_sized(self):
        """The reason the restype matters: the default is a 32-bit int."""
        from OpenGL.raw.WGL import _types

        assert ctypes.sizeof(_types.HDC) == ctypes.sizeof(ctypes.c_void_p)
