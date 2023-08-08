#! /usr/bin/env python
"""PyOpenGL setup script distutils/setuptools/pip based"""
import sys, os
from distutils.core import setup
from distutils.command.install_data import install_data

extra_commands = {}


class smart_install_data(install_data):
    def run(self):
        # need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command("install")
        self.install_dir = getattr(install_cmd, "install_lib")
        # should create the directory if it doesn't exist!!!
        return install_data.run(self)


extra_commands["install_data"] = smart_install_data

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
        cmdclass=extra_commands,
    )
