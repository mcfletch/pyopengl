#! /usr/bin/env python3
"""Builds links from the OpenGL.org man pages to our "original" directory"""
from __future__ import absolute_import
import os, sys, glob, shutil, re, subprocess

MAN_TARGET = 'original'

MAN_SOURCES = [
    ('https://github.com/KhronosGroup/OpenGL-Refpages', 'OpenGL-Refpages'),
]

def ensure_sources( ):
    """Ensure that the OpenGL.org man-page sources are available"""
    for source, target in MAN_SOURCES:
        if not os.path.exists(target):
            subprocess.check_call(['git', 'clone', source, target])
        else:
            subprocess.check_call(['git', 'pull', '--ff-only'], cwd=target)

def package_name( name ):
    if name.startswith( 'glX' ):
        return 'GLX'
    elif name.startswith( 'glut' ):
        return 'GLUT'
    elif name.startswith( 'glu' ):
        return 'GLU'
    elif name.startswith( 'gl' ):
        return 'GL'
    else:
        return None

if __name__ == "__main__":
    ensure_sources()
    # link_sources()
