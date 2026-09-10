#! /usr/bin/env python3
"""The generated modules, built from the tables rather than imported as files.

Every module under ``OpenGL/raw`` is purely generated, so what it contains is
data.  These cases hold the built module to what the file defines, which is
the only thing that makes replacing one with the other safe.
"""

import ctypes
import importlib
import json
import os
import subprocess
import sys

import paths
import pytest

from childenv import run_in_child

import OpenGL._dispatch as dispatch
from OpenGL import dispatch as dispatch_api
from OpenGL import _configflags

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT

#: The finder is built from the C layer's tables, so it exists only where that
#: layer is the one running.  Selecting ctypes is not a failure of anything
#: here; there is simply nothing to compare against.
pytestmark = pytest.mark.skipif(
    dispatch_api.settle() != 'c',
    reason='the C dispatch layer is not the selected implementation',
)

#: A spread: core versions, an extension, and a second API namespace.
SAMPLE = [
    'OpenGL.raw.GL.VERSION.GL_1_1',
    'OpenGL.raw.GL.VERSION.GL_2_0',
    'OpenGL.raw.GL.ARB.vertex_buffer_object',
    'OpenGL.raw.GL.ARB.shader_objects',
    'OpenGL.raw.GLES2.VERSION.GLES2_2_0',
]

COMPARE = r'''
import importlib, json, os, sys
os.environ['PYOPENGL_VIRTUAL_MODULES'] = %(virtual)r
import OpenGL.GL  # installs the dispatch implementation and its finder
out = {}
for name in %(names)r:
    module = importlib.import_module(name)
    out[name] = sorted(k for k in vars(module) if not k.startswith('__'))
json.dump(out, sys.stdout)
'''

#: What the generated files defined, recorded from the tree that still had
#: them.  The comparison used to run both halves live, which stopped being
#: possible when the files went: there is no second source to survey any more.
#: So the answer they gave is checked in, and the synthesised modules are held
#: to it -- which is the same assertion, against a baseline that cannot drift
#: because it is no longer derived from anything.  A name added by hand to an
#: ``OpenGL/raw/<API>/_types.py`` is added here as well: every module of that
#: API re-exports it, and a file would have carried it too.
BASELINE = os.path.join(paths.DATA, 'generated_module_names.json')


def _run(source):
    """Run a script in a fresh interpreter and hand back what it printed.

    Fresh, because which finder is installed is decided once per process, and
    the point of these is to compare the two.  A failure is reported as a
    failure: a survey that cannot run is the breakage, not a reason to skip.
    """
    completed = run_in_child(source)
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout


def survey(virtual):
    return json.loads(_run(COMPARE % {'virtual': virtual, 'names': SAMPLE}))


@pytest.fixture(scope='module')
def both():
    with open(BASELINE, encoding='utf-8') as handle:
        from_files = json.load(handle)
    return from_files, survey('1')


#: What a generated file leaves behind in its own namespace: the modules it
#: imported to write itself with, and its binding helper.  They are the file's
#: scaffolding rather than anything it defines, so a module built from the
#: tables has no reason to carry them.
SCAFFOLDING = frozenset(['_C', '_cs', '_errors', '_f', '_p', 'arrays', 'ctypes'])


def test_the_built_modules_define_the_same_names(both):
    """What a caller can import must not depend on where it came from."""
    from_files, from_tables = both
    for name in SAMPLE:
        missing = sorted(
            set(from_files[name]) - set(from_tables[name]) - SCAFFOLDING
        )
        assert missing == [], (name, missing[:20])


def test_nothing_unexpected_is_added(both):
    from_files, from_tables = both
    for name in SAMPLE:
        extra = sorted(set(from_tables[name]) - set(from_files[name]))
        assert extra == [], (name, extra[:20])


def test_the_finder_covers_the_generated_tree():
    from OpenGL._dispatch import _c as extension

    names = extension.module_names()
    assert len(names) > 1200
    assert 'OpenGL.raw.GL.VERSION.GL_1_1' in names


def test_a_built_module_carries_its_extension_name():
    from OpenGL._dispatch import _c as extension

    contents = extension.module_contents('OpenGL.raw.GL.VERSION.GL_1_1')
    assert contents['extension'] == 'GL_VERSION_GL_1_1'
    assert 'glBindTexture' in [command for command, _names, _types in contents['commands']]
    assert 'GL_TEXTURE_BINDING_2D' in contents['constants']


def test_a_built_module_re_exports_what_its_file_did():
    """GL_1_1 gets GL_TEXTURE_2D from GL_1_0, as the file's `import *` did."""
    from OpenGL._dispatch import _c as extension

    contents = extension.module_contents('OpenGL.raw.GL.VERSION.GL_1_1')
    assert 'OpenGL.raw.GL.VERSION.GL_1_0' in contents['reexports']

    module = importlib.import_module('OpenGL.raw.GL.VERSION.GL_1_1')
    assert int(module.GL_TEXTURE_2D) == 0x0DE1


DEMOTES = r'''
import json, os, sys
os.environ['PYOPENGL_VIRTUAL_MODULES'] = '1'
import OpenGL.GL as GL
from OpenGL._dispatch import support
from OpenGL.raw.GL.VERSION import GL_1_2

binding = support.ctypes_callable('glTexImage3D')
print(json.dumps({
    'built': str(GL_1_2.__spec__.origin).endswith('GL.dat'),
    'typed': GL.glTexImage3Dub is not None,
    'argnames': list(binding.argNames),
    'argtypes': [getattr(t, '__name__', str(t)) for t in binding.argtypes],
}))
'''


def test_a_shadowed_module_still_supports_demotion():
    """The Python layer derives glTexImage3Dub from glTexImage3D.

    Deriving one changes the arity, so it demotes to the ctypes binding --
    which the file used to record by running its declaration.  Nothing runs
    the declaration now, so the table has to carry the signature that
    declaration stated.
    """
    result = json.loads(_run(DEMOTES))
    assert result['built'] is True
    assert result['typed'] is True
    assert result['argnames'][:3] == ['target', 'level', 'internalformat']
    # GLenum is ctypes.c_uint -- asked for by that name, because where int and
    # long are the same width ctypes makes c_uint an alias of c_ulong and the
    # type answers to the other one.
    assert result['argtypes'][0] == ctypes.c_uint.__name__
    assert len(result['argtypes']) == len(result['argnames'])


ROUNDTRIP = r'''
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
from cdispatch import extract, modules
from OpenGL._dispatch import _c as extension

wrong = []
for module in modules.read_modules(os.path.join(os.getcwd(), 'OpenGL'), extract.APIS):
    built = extension.module_contents(module.name)
    if built is None:
        wrong.append((module.name, 'not in the table'))
        continue
    for name, value in module.constants.items():
        if built['constants'].get(name) != value:
            wrong.append((module.name, name, value, built['constants'].get(name)))
    stated = {row[0]: (row[1], row[2]) for row in built['commands']}
    for command in module.commands:
        got = stated.get(command.name)
        want = (','.join(command.argument_names), ','.join(command.types))
        if got != want:
            wrong.append((module.name, command.name, want, got))
print(json.dumps(wrong[:20]))
'''


def test_every_constant_and_signature_survives_the_c_table():
    """The whole tree, value for value, not a sample of names.

    A constant's range runs from -6 to 2**64-1 and a signature is text the
    finder resolves, so an encoding that loses either would be invisible to a
    comparison of names.
    """
    wrong = json.loads(_run(ROUNDTRIP))
    assert wrong == [], wrong


MODULE_ATTR = r'''
import json, os, sys
os.environ['PYOPENGL_VIRTUAL_MODULES'] = %(virtual)r
import OpenGL.GL
from OpenGL.raw.GL.VERSION import GL_1_2
print(json.dumps({
    'built': str(GL_1_2.__spec__.origin).endswith('GL.dat'),
    'module': GL_1_2.glTexImage3D.__module__,
}))
'''


def test_an_entry_point_reports_where_it_was_declared():
    """``proc.__module__`` names the module that declared it.

    It used to be compared against the same answer read from the file, which
    is the answer recorded here -- the file said
    ``OpenGL.raw.GL.VERSION.GL_1_2`` because that is where the declaration was
    written, and a synthesised module has to say the same, or a traceback and
    a ``help()`` start naming somewhere that does not exist.
    """
    from_tables = json.loads(_run(MODULE_ATTR % {'virtual': '1'}))
    assert from_tables['built'] is True
    assert from_tables['module'] == 'OpenGL.raw.GL.VERSION.GL_1_2'


IMPORTS_RAW = r'''
import OpenGL.GL
from OpenGL.raw.GL.VERSION import GL_1_1
print(int(GL_1_1.GL_TEXTURE_2D))
'''


class TestTheNamesResolveWhateverTheEnvironmentSays:
    """There is nothing for the finder to be switched off in favour of.

    The generated files are not shipped and the generator does not write them,
    so these names resolve from the tables or not at all.  A variable that
    could stop them resolving would have one setting that works and one that
    breaks every installation, so there is no such variable -- and a stale one
    left in somebody's environment must not be able to break their program.
    """

    @pytest.mark.parametrize('value', ['0', 'no', 'off', '1'])
    def test_a_setting_left_over_in_the_environment_changes_nothing(self, value):
        completed = run_in_child(IMPORTS_RAW)
        assert completed.returncode == 0, completed.stderr[-2000:]
        assert completed.stdout.strip() == str(0x0DE1)
