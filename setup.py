#! /usr/bin/env python
"""PyOpenGL setup script distutils/setuptools/pip based"""
import sys, os
from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))

# PyOpenGL builds nothing.  The C dispatch layer is compiled by
# pyopengl_accelerate, which is the optional compiled companion released from
# this same repository -- so this stays one universal wheel, and "is the fast
# path available?" is the question it has always been: is accelerate
# installed?
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
        include_package_data=True,
    )
