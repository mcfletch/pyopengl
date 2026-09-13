#! /usr/bin/env python
"""PyOpenGL setup script distutils/setuptools/pip based"""
from setuptools import setup

# PyOpenGL builds nothing.  The C dispatch layer is compiled by
# pyopengl_accelerate, which is the optional compiled companion released from
# this same repository -- so this stays one universal wheel, and "is the fast
# path available?" is the question it has always been: is accelerate
# installed?
#
# Nor is anything installed outside the package.  The Windows builds of GLUT
# and GLE used to ship as package data under `OpenGL/DLLS`, and were briefly
# named in `data_files` instead -- which installs relative to the *install
# prefix* rather than into the package.  On Windows the prefix is a directory
# the interpreter imports from: `site.getsitepackages()` there answers
# `[prefix, prefix\\Lib\\site-packages]`.  So the copy put an `OpenGL`
# directory with no `__init__.py` in it on sys.path, ahead of the real
# package, and PyOpenGL imported as a namespace package for every process that
# ran from anywhere but the checkout.
#
# The builds are `PyOpenGL-glut-binaries` now, so nothing here ships them at
# all -- but the rule outlives them, and
# `tests/bindings/test_broken_installation.py` holds it.

if __name__ == "__main__":
    setup(
        options={
            "sdist": {
                "formats": ["gztar"],
                "force_manifest": True,
            },
        },
        include_package_data=True,
    )
