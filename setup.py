#! /usr/bin/env python
"""PyOpenGL setup script distutils/setuptools/pip based"""
import glob
import sys, os
from setuptools import setup, Extension

HERE = os.path.dirname(os.path.abspath(__file__))

# The registry-generated C dispatch layer.  Optional: PyOpenGL runs on its
# ctypes implementation where no compiler is available, and PYOPENGL_DISPATCH
# selects between them at run time.  Set PYOPENGL_NO_C_DISPATCH=1 to skip
# building it.
_GENERATED = 'src/c/generated'


def dispatch_extension():
    # setuptools requires /-separated paths relative to this file.
    if os.environ.get('PYOPENGL_NO_C_DISPATCH'):
        return []
    sources = sorted(
        path.replace(os.sep, '/')
        for path in glob.glob(os.path.join(HERE, 'src', 'c', 'generated', '*.c'))
    )
    if not sources:
        return []
    sources = [os.path.relpath(path, HERE).replace(os.sep, '/') for path in sources]
    sources.insert(0, 'src/c/pygl_handwritten.c')
    sources.insert(0, 'src/c/pygl_runtime.c')
    # setuptools does not work out header dependencies for itself, so a change
    # to pygl.h would otherwise leave the generated objects stale and the build
    # mixed -- objects compiled against one version of a macro linked with a
    # runtime compiled against another.  Naming the headers makes a change to
    # any of them rebuild everything.
    headers = [
        'src/c/pygl.h',
        'src/c/generated/pygl_elements.h',
        'src/c/generated/pygl_glgets.h',
    ]
    return [
        Extension(
            'OpenGL._dispatch._dispatch',
            sources=sources,
            include_dirs=['src/c', _GENERATED],
            depends=[path for path in headers if os.path.exists(path)],
            # Optional so that a source install without a compiler still
            # works -- the layer falls back to ctypes on its own.  That also
            # means a compile error is a warning rather than a failure, and
            # the previous extension is quietly kept, so set
            # PYOPENGL_REQUIRE_C_DISPATCH=1 while working on it.
            optional=not os.environ.get('PYOPENGL_REQUIRE_C_DISPATCH'),
        )
    ]

if sys.platform == "win32":
    # binary versions of GLUT and GLE for Win32 (sigh)
    DLL_DIRECTORY = os.path.join("OpenGL", "DLLS")
    datafiles = [
        (
            DLL_DIRECTORY,
            [
                os.path.join(DLL_DIRECTORY, file)
                for file in os.listdir(DLL_DIRECTORY)
                if os.path.isfile(os.path.join(DLL_DIRECTORY, file))
            ],
        ),
    ]
else:
    datafiles = []


if __name__ == "__main__":
    setup(
        options={
            "sdist": {
                "formats": ["gztar"],
                "force_manifest": True,
            },
        },
        data_files=datafiles,
        ext_modules=dispatch_extension(),
        include_package_data=True,
    )
