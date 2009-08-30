"""Abstraction for the platform-specific code in PyOpenGL

Each supported platform has a module which provides the
specific functionality required to support the base OpenGL 
functionality on that platform.  These modules are 
registered using plugins in the:

    OpenGL.plugin.PlatformPlugin

objects.  To support a new platform you'll need to create
a new PlatformPlugin instance *before* you import 
OpenGL.platform .  Once you have a working platform 
module, please consider contributing it back to the project.

See baseplatform.BasePlatform for the core functionality 
of a platform implementation.  See the various platform 
specific modules for examples to use when porting.
"""
import os, sys
from OpenGL.plugins import PlatformPlugin

def _load( ):
    """Load the os.name plugin for the platform functionality"""
    
    key = (sys.platform,os.name)
    plugin  = PlatformPlugin.match( key )
    plugin_class = plugin.load()
    plugin.loaded = True
    # create instance of this platform implementation
    plugin = plugin_class()

    # install into the platform module's namespace now
    plugin.install(globals())
    return plugin

_load()