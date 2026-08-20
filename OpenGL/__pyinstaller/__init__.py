"""PyInstaller hooks for PyOpenGL

PyInstaller finds these through the ``pyinstaller40`` entry point declared in
``pyproject.toml``: it calls :func:`get_hook_dirs` and reads every
``hook-*.py`` in the directory returned. Nothing here is imported when
PyOpenGL is merely used.
"""

import os


def get_hook_dirs():
    """Directories PyInstaller should read hooks from"""
    return [os.path.dirname(__file__)]
