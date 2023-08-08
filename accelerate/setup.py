#!/usr/bin/env python
"""Builds accelleration functions for PyOpenGL
"""

import sys

if sys.version_info[:2] < (3, 12):
    from setuptools import setup, Extension
else:
    from distutils.core import setup, Extension

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
            # *cython* itself is using the deprecated api, and the
            # deprecated APIs are actually providing the attributes
            # that we use throughout our code...
            #    ('NPY_NO_DEPRECATED_API','NPY_1_7_API_VERSION'),
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
        options={
            "sdist": {
                "formats": ["gztar"],
                "force_manifest": True,
            },
        },
        ext_modules=extensions,
        **extraArguments
    )
