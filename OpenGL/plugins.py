"""Simple plug-in mechanism to provide replacement for setuptools plugins"""
import logging 
log = logging.getLogger(__name__)

class Plugin( object ):
    """Base class for plugins to be loaded"""
    loaded = False
    def __init__( self, name, import_path, check = None, **named ):
        """Register the plug-in"""
        self.name = name 
        self.import_path = import_path
        self.check = check
        self.registry.append( self )
        self.__dict__.update( named )
    def load( self ):
        """Attempt to load and return our entry point"""
        try:
            return importByName( self.import_path )
        except ImportError as err:
            log.warning(
                'Unable to import %s: %s',
                self.import_path,
                err
            )
            return None
    @classmethod
    def match( cls, *args ):
        """Match to return the plugin which is appropriate to load"""
    @classmethod
    def all( cls ):
        """Iterate over all registered plugins"""
        return cls.registry[:]
    @classmethod 
    def by_name( cls, name ):
        for instance in cls.all():
            if instance.name == name:
                return instance 
        return None
    
def importByName( fullName ):
    """Import a class by name"""
    name = fullName.split(".")
    moduleName = name[:-1]
    className = name[-1]
    module = __import__( ".".join(moduleName), {}, {}, moduleName)
    return getattr( module, className )


def _registries( ):
    """Iterate over every distinct registry any Plugin subclass declares"""
    seen = []
    pending = [Plugin]
    while pending:
        cls = pending.pop()
        pending.extend( cls.__subclasses__() )
        registry = getattr( cls, 'registry', None )
        if registry is not None and not any( registry is known for known in seen ):
            seen.append( registry )
    return seen

def registered_modules( prefix=None ):
    """Report the modules the registered plug-ins import, as a sorted list

    A plug-in declares its entry point as a dotted ``import_path`` and imports
    it only once something matches, so a tool that follows import statements --
    a freezer such as PyInstaller, cx_Freeze or Nuitka -- sees none of them and
    freezes an application that cannot load a platform, a format handler or,
    with OpenGLContext on top, a scenegraph node. This reports the modules
    those paths name so that such a tool can be told about them.

    Every registry is read, including those declared by packages layered on
    PyOpenGL, so the answer covers whatever is imported at the time of the call.

    prefix -- when given, report only the modules within this package. Matching
        is on whole dotted components, so ``OpenGL`` selects ``OpenGL.arrays``
        and not ``OpenGLContext``.
    """
    modules = set()
    for registry in _registries():
        for plugin in registry:
            module = plugin.import_path.rpartition( '.' )[0]
            if module:
                modules.add( module )
    if prefix is not None:
        modules = set([
            module for module in modules
            if module == prefix or module.startswith( prefix + '.' )
        ])
    return sorted( modules )

class PlatformPlugin( Plugin ):
    """Platform-level plugin registration"""
    registry: "list[PlatformPlugin]" = []
    @classmethod
    def match( cls, key ):
        """Determine what platform module to load
        
        key -- (sys.platform,os.name) key to load 
        """
        for possible in key:
            # prefer sys.platform, *then* os.name
            for plugin in cls.registry:
                if plugin.name == possible:
                    return plugin
        raise KeyError( """No platform plugin registered for %s"""%(key,))

class FormatHandler( Plugin ):
    """Data-type storage-format handler"""
    registry: "list[FormatHandler]" = []
    @classmethod
    def match( cls, value ):
        """Lookup appropriate handler based on value (a type)"""
        key = '%s.%s'%( value.__module__, value.__name__ )
        for plugin in cls.registry:
            set = getattr( plugin, 'check', ())
            if set and key in set:
                return plugin
        return None
