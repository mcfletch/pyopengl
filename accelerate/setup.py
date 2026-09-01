#!/usr/bin/env python
"""Builds accelleration functions for PyOpenGL
"""
import sys
from setuptools import setup, Extension

try:
    from Cython.Distutils import build_ext
except ImportError:
    have_cython = False
    build_ext = False
else:
    have_cython = True

import sys, os

HERE = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

extensions = []


def dispatch_extension():
    """The registry-generated C implementation of the OpenGL entry points.

    It lives here rather than in ``pyopengl`` so that ``pyopengl`` stays a
    single universal wheel: the C is what needs a compiler and a wheel per
    platform, and this package is already the optional compiled companion.
    "Is the fast path available?" is then the question it has always been --
    is accelerate installed?

    Both packages are released together from one repository, and the two
    share generated tables, so the versions must match exactly; the module
    checks that at import.
    """
    import glob

    if os.environ.get('PYOPENGL_NO_C_DISPATCH'):
        return []
    generated = os.path.join(HERE, 'src', 'c', 'generated')
    sources = sorted(
        os.path.relpath(path, HERE).replace(os.sep, '/')
        for path in glob.glob(os.path.join(generated, '*.c'))
    )
    if not sources:
        return []
    sources.insert(0, 'src/c/pygl_handwritten.c')
    sources.insert(0, 'src/c/pygl_runtime.c')
    # setuptools does not work out header dependencies, so a change to pygl.h
    # would otherwise leave the generated objects stale and the build mixed:
    # objects compiled against one version of a macro linked with a runtime
    # compiled against another.
    headers = [
        'src/c/pygl.h',
        'src/c/generated/pygl_elements.h',
        'src/c/generated/pygl_glgets.h',
    ]
    return [
        Extension(
            'OpenGL_accelerate.dispatch',
            sources=sources,
            include_dirs=['src/c', 'src/c/generated'],
            depends=[
                path for path in headers if os.path.exists(os.path.join(HERE, path))
            ],
            # Optional so a source install without a compiler still yields a
            # working accelerate; PyOpenGL falls back to ctypes on its own.
            # Set PYOPENGL_REQUIRE_C_DISPATCH=1 while working on it, or a
            # compile error is a warning and the stale object is kept.
            optional=not os.environ.get('PYOPENGL_REQUIRE_C_DISPATCH'),
        )
    ]


extensions.extend(dispatch_extension())


def cython_extension(
    name,
    include_dirs=(),
):
    """Create a cython extension object"""
    filenames = "%(name)s.c" % locals(), "%(name)s.pyx" % locals()
    filename = filenames[bool(have_cython)]
    return Extension(
        "OpenGL_accelerate.%(name)s" % locals(),
        [
            os.path.join("src", filename),
        ],
        include_dirs=[
            os.path.join(HERE, "src"),
            HERE,
        ]
        + list(include_dirs),
        define_macros=[
            ('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION'),
        ],
        compiler_directives={'language_level': "3"} if have_cython else {},
    )


extensions.extend(
    [
        cython_extension("wrapper"),
        cython_extension("formathandler"),
        cython_extension("arraydatatype"),
        cython_extension("errorchecker"),
        cython_extension("vbo"),
        cython_extension("nones_formathandler"),
        cython_extension("latebind"),
    ]
)
if sys.version_info[:2] >= (2, 7):
    extensions.extend(
        [
            cython_extension("buffers_formathandler"),
        ]
    )

try:
    import numpy
except ImportError:
    sys.stderr.write("""Unable to import numpy, skipping numpy extension building\n""")
else:
    if hasattr(numpy, "get_include"):
        includeDirectories = [
            numpy.get_include(),
        ]
    else:
        includeDirectories = [
            os.path.join(
                os.path.dirname(numpy.__file__),
                "core",
                "include",
            ),
        ]
    extensions.append(
        cython_extension(
            "numpy_formathandler",
            includeDirectories,
        )
    )

if (  # Prevents running of setup during code introspection imports
    __name__ == "__main__"
):
    # Workaround for Broken apple Python build params echoed in distutils
    # Approach taken from the PyMongo driver. OS-X Python builds were created with
    # non-existent flag, and distutils passes those flags to the extension
    # build, newer clangs now treat those flags as errors rather than warnings.
    import platform, sys

    if sys.platform == "darwin" and "clang" in platform.python_compiler().lower():
        from distutils.sysconfig import get_config_vars

        res = get_config_vars()
        for key in ("CFLAGS", "PY_CFLAGS"):
            if key in res:
                res[key] = res[key].replace("-mno-fused-madd", "")

    extraArguments = {}
    ### Now the actual set up call
    if have_cython:
        extraArguments["cmdclass"] = {
            "build_ext": build_ext,
        }
    setup(
        build_requires=['cython'],
        options={
            "sdist": {
                "formats": ["gztar"],
                "force_manifest": True,
            },
        },
        ext_modules=extensions,
        **extraArguments
    )
