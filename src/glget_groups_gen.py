#! /usr/bin/env python3
"""Generate the per-feature/per-extension glGet pname map used by the glGet
size/semantics test suite.

For each GL version (``feature``) and extension in the Khronos registry, this
records the ``glGet*`` pnames it defines, classified by *getter family* -- the
call you must make to read them:

* ``state``                 -- ``glGetIntegerv`` / ``glGetInteger64v`` / indexed ``glGetIntegeri_v`` ... (group ``GetPName``)
* ``program``               -- ``glGetProgramiv``                  (group ``ProgramPropertyARB``)
* ``shader``                -- ``glGetShaderiv``                   (group ``ShaderParameterName``)
* ``uniform_block``         -- ``glGetActiveUniformBlockiv``       (group ``UniformBlockPName``)
* ``atomic_counter_buffer`` -- ``glGetActiveAtomicCounterBufferiv``(group ``AtomicCounterBufferPName``)
* ``program_interface``     -- ``glGetProgramInterfaceiv``         (group ``ProgramInterfacePName``)

The registry's enum ``group`` attribute + each getter's ``<param group=...>`` give
the family; it does *not* encode scalar-vs-indexed or how to set a value up, which
stays in the hand-curated semantics layer (``tests/glget_check.py``).

Only pnames already present in ``glgetsizes.csv`` get a descriptor (we can assert
their size).  Registry glGet pnames *missing* from the CSV are reported per
feature under ``missing_size`` -- the backlog of sizes still to add.

Output: ``tests/<suite>/glget_groups.json`` (suite ``gl`` for desktop, ``gles``
for ES).  Run::

    python src/glget_groups_gen.py                 # both suites, autodetect gl.xml
    python src/glget_groups_gen.py --xml path/to/gl.xml
"""

import os
import re
import sys
import json
import argparse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: getter command name -> family kind.  Only getters that take a pname/target
#: enum we want to exercise; everything else falls through to ``other``.
_GETTER_FAMILY = {
    'glGetBooleanv': 'state', 'glGetIntegerv': 'state', 'glGetFloatv': 'state',
    'glGetDoublev': 'state', 'glGetInteger64v': 'state',
    'glGetBooleani_v': 'state', 'glGetIntegeri_v': 'state',
    'glGetInteger64i_v': 'state', 'glGetFloati_v': 'state', 'glGetDoublei_v': 'state',
    'glGetProgramiv': 'program',
    'glGetShaderiv': 'shader',
    'glGetActiveUniformBlockiv': 'uniform_block',
    'glGetActiveAtomicCounterBufferiv': 'atomic_counter_buffer',
    'glGetProgramInterfaceiv': 'program_interface',
}
#: families ranked: a group accepted by several getters takes the strongest.
_FAMILY_RANK = ['state', 'program', 'shader', 'uniform_block',
                'atomic_counter_buffer', 'program_interface']

#: Constants the registry files under GetPName but that are NOT served by the
#: size-mapped array getters -- they are read with glGetUnsignedBytev/i_v (byte
#: arrays sized via setInputArraySize, not _glget_size_mapping).  They must stay
#: out of glgetsizes.csv: a blind glGetFloatv/glGetIntegerv on them returns
#: garbage and crashes some drivers (llvmpipe segfaults on GL_DEVICE_LUID_EXT).
#: The registry can't distinguish them (glGetUnsignedBytev's pname is also
#: GetPName), so they are listed explicitly.
NON_GLGET = {
    'GL_DEVICE_UUID_EXT',
    'GL_DRIVER_UUID_EXT',
    'GL_DEVICE_LUID_EXT',
    'GL_DEVICE_NODE_MASK_EXT',
    'GL_NUM_DEVICE_UUIDS_EXT',
}

#: which registry api a test suite consumes, and how its version features are named.
_SUITES = {
    'gl': {'api': 'gl', 'feature_re': re.compile(r'^GL_VERSION_\d+_\d+$')},
    'gles': {'api': 'gles2', 'feature_re': re.compile(r'^GL_ES_VERSION_\d+_\d+$')},
}


def find_xml(explicit=None):
    cands = [
        explicit,
        os.environ.get('GL_XML'),
        os.path.join(HERE, 'khronosapi', 'xml', 'gl.xml'),
        os.path.join(ROOT, '..', 'pyopengl-orig', 'src', 'khronosapi', 'xml', 'gl.xml'),
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise SystemExit('gl.xml not found; pass --xml PATH or set GL_XML')


def csv_sizes():
    """``{enum_name: size_str}`` from glgetsizes.csv (joins extra columns)."""
    out = {}
    with open(os.path.join(HERE, 'glgetsizes.csv')) as fh:
        for raw in fh.read().splitlines():
            cols = raw.split('\t')
            if not cols or not cols[0].strip():
                continue
            size = ''.join([c for c in (c.strip('"') for c in cols[1:]) if c])
            if size:
                out[cols[0].strip('"').strip()] = size
    return out


def build_registry(root):
    """Return ``(enum_value, enum_group, group_family)`` lookup dicts."""
    enum_value, enum_group = {}, {}
    for en in root.iter('enum'):
        name = en.get('name')
        if name is None or en.get('value') is None:
            continue
        enum_value.setdefault(name, en.get('value'))
        if en.get('group') and name not in enum_group:
            enum_group[name] = en.get('group')

    group_family = {}
    for cmd in root.iter('command'):
        proto = cmd.find('proto')
        if proto is None:
            continue
        fam = _GETTER_FAMILY.get(proto.findtext('name') or '')
        if not fam:
            continue
        for prm in cmd.findall('param'):
            grp = prm.get('group')
            if grp and prm.findtext('name') in ('pname', 'target'):
                prev = group_family.get(grp)
                if prev is None or _FAMILY_RANK.index(fam) < _FAMILY_RANK.index(prev):
                    group_family[grp] = fam
    return enum_value, enum_group, group_family


def required_enums(node):
    """Enum names a ``<feature>``/``<extension>`` requires (ignores <remove>)."""
    names = []
    for req in node.findall('require'):
        for en in req.findall('enum'):
            names.append(en.get('name'))
    return names


def descriptors(names, sizes, enum_value, enum_group, group_family):
    """Classify ``names`` into testable descriptors + a missing-size backlog."""
    descs, missing = [], []
    for name in dict.fromkeys(names):  # de-dup, keep order
        if name in NON_GLGET:          # byte-array getters; never size-mapped
            continue
        group = enum_group.get(name)
        value = enum_value.get(name)
        if group in group_family:
            family = group_family[group]            # a real getter group
        elif group is None:
            family = 'state?'                       # ungrouped: probe tolerantly
        else:
            family = None                           # typed non-getter group -> not a glGet
        if name in sizes and family:
            descs.append({
                'name': name,
                'value': value,
                'size': sizes[name],
                'group': group,
                'family': family,
            })
        elif family and family != 'state?':
            # a real glGet pname per the registry but no size recorded yet
            missing.append({'name': name, 'value': value,
                            'group': group, 'family': family})
    return descs, missing


def build_suite(root, suite, sizes):
    api = _SUITES[suite]['api']
    feat_re = _SUITES[suite]['feature_re']
    enum_value, enum_group, group_family = build_registry(root)

    out = {'suite': suite, 'api': api, 'features': {}, 'extensions': {}}
    for feat in root.iter('feature'):
        if feat.get('api') != api or not feat_re.match(feat.get('name') or ''):
            continue
        d, m = descriptors(required_enums(feat), sizes, enum_value, enum_group, group_family)
        out['features'][feat.get('name')] = {'glgets': d, 'missing_size': m}
    for ext in root.find('extensions').findall('extension'):
        if api not in (ext.get('supported') or '').split('|'):
            continue
        d, m = descriptors(required_enums(ext), sizes, enum_value, enum_group, group_family)
        if d or m:
            out['extensions'][ext.get('name')] = {'glgets': d, 'missing_size': m}
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--xml')
    ap.add_argument('--suite', choices=list(_SUITES), action='append')
    args = ap.parse_args(argv)

    root = ET.parse(find_xml(args.xml)).getroot()
    sizes = csv_sizes()
    for suite in (args.suite or list(_SUITES)):
        data = build_suite(root, suite, sizes)
        dest_dir = os.path.join(ROOT, 'tests', suite)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, 'glget_groups.json')
        with open(dest + '.partial', 'w') as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
            fh.write('\n')
        os.replace(dest + '.partial', dest)
        nfeat = sum(len(v['glgets']) for v in data['features'].values())
        next_ = sum(len(v['glgets']) for v in data['extensions'].values())
        nmiss = sum(len(v['missing_size']) for v in
                    list(data['features'].values()) + list(data['extensions'].values()))
        print('%s: %d feature + %d extension glgets across %d ext, %d missing-size'
              % (os.path.relpath(dest, ROOT), nfeat, next_, len(data['extensions']), nmiss))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
