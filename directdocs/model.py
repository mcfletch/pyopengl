"""Modelling objects for the documentation generator"""
from __future__ import absolute_import
import logging, types, inspect
from six.moves import zip
log = logging.getLogger( 'directdocs.model' )

from OpenGL import __version__
MAJOR_VERSION = '.'.join(__version__.split('.')[:2] )


class NotDefined( object ):
    def __nonzero__( self ):
        return False

NOT_DEFINED = NotDefined()

class Reference( object ):
    """Overall reference text"""
    def __init__( self ):
        self.sections = {}
        self.section_titles = {}
        self.functions = {}
        self.constants = {}
    def append( self, section ):
        """Add the given section to our tables"""
        if section.id != section.title:
            if not section.id:
                log.warn( 'Null section id in %s', section.title )
            elif '.' in section.id and section.id.split('.')[0] == section.title and section.id.split('.')[1].startswith( '3' ):
                pass
            else:
                log.warn( "Unmatched id/title: %s (title) %s (id)", section.title, section.id )
        if section.id in self.sections:
            log.warn( "Duplicate section id: %s", section.id )
        if section.title in self.sections:
            log.warn( "Duplicate section title: %s", section.title )
        self.sections[section.id] = section
        self.section_titles[section.title]= section
        for function in section.functions.values():
            self.functions[ function.name ] = function

    def suffixed_name( self, a,b ):
        """Is b a with a suffix?"""
        if b.startswith( a ):
            for char in b[len(a):]:
                if char not in self.suffix_chars:
                    return False
            return True
        return False
    def get_crossref( self, title, volume=None,section=None ):
        raise NotImplemented( """Need a get_crossref method""" )
    def package_names( self ):
        raise NotImplemented( """Need a package_names method""" )
    def modules( self ):
        raise NotImplemented( """Need a modules method""" )

    suffix_chars = 'iufs1234v'
    def check_crossrefs( self ):
        sections = sorted(self.sections.items())
        for i,(name,section) in enumerate(sections):
            list(section.get_crossrefs(self))
            if i > 0:
                section.previous = sections[i-1][1]
            if i < len(sections)-1:
                section.next = sections[i+1][1]
            section.find_python_functions()

    def packages( self ):
        result = []
        for source in self.package_names():
            result.append( (source,sorted([
                (name,section) for name,section in self.section_titles.items()
                if section.package == source
            ])))
        return result

class RefSect( object ):
    id = None
    title = None
    purpose = None
    next = None
    previous = None
    deprecated = False
    def __init__( self, package='GL', reference=None ):
        self.package = package
        self.reference = reference
        self.functions = {}
        self.py_functions = {}
        self.varrefs = []
        self.see_also = []
        self.discussions = []
        self.samples = []
        self.constants = {}
    def set_deprecation( self, value ):
        """Set our deprecated flag"""
        self.deprecated = value
    def has_function( self, name ):
        """Ask whether we have this name defined"""
        return (
            name in self.functions or
            name in self.py_functions
        )
    def get_module( self ):
        """Retrieve our module"""
        return self.reference.modules()[
            self.reference.package_names().index( self.package )
        ]
    def get_crossrefs( self, reference ):
        """Retrieve all cross-references from reference"""
        result = []
        for (title,volume) in self.see_also:
            target = reference.get_crossref( title, volume, self )
            if target is not None:
                result.append( target )
        return result
        # should also look for mentions in the description sections
    def find_python_functions( self ):
        """Find our functions, aliases and the like in python module"""
        # TODO this is a very inefficient scan...
        source = self.get_module()
        for name,function in sorted(self.functions.items()):
            if hasattr( source, function.name ):
                function.python[name] = PyFunction(
                    root_function = function,
                    py_function = getattr( source,name ),
                    alias = name,
                )
                for name in sorted(dir(source)):
                    if (
                        self.reference.suffixed_name( name, function.name ) or
                        self.reference.suffixed_name( function.name, name )
                    ):
                        if not self.has_function( name ):
                            function.python[name] = PyFunction(
                                root_function = function,
                                py_function = getattr( source,name ),
                                alias = name,
                            )
                            self.py_functions[name] = function
                            if name not in self.reference.functions:
                                self.reference.functions[ name ] = function
    def get_samples( self, sample_set ):
        """Populate our sample-set for all of the available samples"""
        names = (
            sorted(self.functions.keys()) +
            sorted(self.py_functions.keys())
        )
        filtered = []
        filter_set = {}
        for name in names:
            if name not in filter_set:
                filtered.append( name )
        for name in filtered:
            if name in sample_set:
                self.samples.append( (name,Sample.joined(sample_set[name])))
        self.samples.sort()

class Function( object ):
    """Function description produced from docs

    Each function represents an original OpenGL function,
    which may have many Python-level functions associated
    with it.
    """
    return_value = None
    varargs = varnamed = False
    docstring = None
    deprecated = False
    NOT_DEFINED = NOT_DEFINED
    def __init__( self,name, section ):
        self.name = name
        self.section = section
        self.python = {} # name to python function...
        self.parameters = []
#        if section.package == 'GL':
#            from OpenGL.platform import entrypoint31
#            self.deprecated = entrypoint31.deprecated( self.name )
#            if self.deprecated:
#                self.section.set_deprecation( True )
    def __repr__( self ):
        return '%s( %s ) -> %s'%(
            self.name,
            self.parameters,
            self.return_value,
        )

class PyFunction( Function ):
    """Python-implemented function produced via introspection"""
    def __init__( self, root_function, py_function, alias=None ):
        self.root_function = root_function
        self.py_function = py_function
        self.alias = alias
    @property
    def alternates( self ):
        """Yield any alternate definitions"""
        if hasattr( self.py_function, '_alternatives' ):
            return [
                PyFunction( self.root_function, alternate )
                for alternate in self.py_function._alternatives
            ]
        return []
    @property
    def name( self ):
        """Introspect to get a name for our function"""
        if self.alias:
            return self.alias
        # okay, so do some introspection...
        if hasattr( self.py_function, '__name__' ):
            return self.py_function.__name__
        raise ValueError( """Don't know how to get name for %r type"""%(
            self.py_function.__class__,
        ))
    @property
    def target( self ):
        function = self.py_function
        function = getattr( function, '__func__', function )
        return function
    @property
    def docstring( self ):
        """Retrieve docstring for pure-python objects"""
        if hasattr( self.target, '__doc__' ):
            return self.target.__doc__
        return None
    @property
    def section( self ):
        return self.root_function.section
    @property
    def python( self ):
        return {}
    _parameters = None
    @property
    def parameters( self ):
        """Calculate (and store) parameter-list for the function"""
        if self._parameters is None:
            self._parameters = self.get_parameters( self.target )
        return self._parameters
    def get_parameters( self, target ):
        names = None
        if hasattr( target, 'pyConverterNames' ):
            names = target.pyConverterNames
        elif hasattr( target, 'argNames' ):
            names = target.argNames
        elif hasattr( target, 'wrapperFunction' ):
            # only values *past* the first for lazy-wrapped operations
            return self.get_parameters( target.wrapperFunction )[1:]
        elif hasattr( target, 'wrappedOperation' ):
            return self.get_parameters( target.wrappedOperation )
        elif isinstance( target, (types.FunctionType,types.MethodType) ):
            args,varargs,varkw,defaults = inspect.getargspec(
                target
            )
            defaults = defaults or ()
            default_dict = dict([
                (arg,default)
                for (arg,default) in zip(args[-len(defaults):],defaults)
            ])
            try:
                parameters = []
                for name in args:
                    if isinstance( name, list ):
                        name = tuple(name)
                    parameters.append( Parameter(
                        name, default=default_dict.get( name, NOT_DEFINED ),
                        function = self,
                    ))
            except Exception as err:
                import pdb
                pdb.set_trace()
            if varargs:
                parameters.append(
                    Parameter(
                        varargs,
                        function = self,
                        varargs = True,
                    )
                )
            if varkw:
                parameters.append(
                    Parameter(
                        varkw,
                        function = self,
                        varnamed = True,
                    )
                )
            return parameters
        else:
            if hasattr( target, 'argtypes' ) and target.argtypes is None:
                return []
            log.warn( """No parameters for type: %r""", target.__class__ )
            names = []
        return [
            Parameter( name, data_type=None, function = self )
            for name in names
        ]
    @property
    def return_value( self ):
        """Determine (if possible) whether we have a return-value type"""
        if hasattr( self.py_function, 'restype' ):
            return self.py_function.restype
        return None

class Parameter( object ):
    """Description of a parameter to a function"""
    NOT_DEFINED = NOT_DEFINED
    def __init__(
        self, name, description=None,
        data_type=None,function=None,
        default=NOT_DEFINED,
        varargs=False, varnamed=False
    ):
        """Initialize with the values for the parameter"""
        self.function = function
        self.data_type = data_type
        self.name = name
        self.description = description
        self.default = default
        self.varargs = varargs
        self.varnamed = varnamed
    @property
    def has_default( self ):
        return not( self.default is NOT_DEFINED )

class ParameterReference( object ):
    def __init__( self, names, description ):
        self.names = names
        self.description = description
    def __repr__( self ):
        result = []
        return '\t\t%s -- %s'%( ', '.join(self.names), self.description )

class Sample( object ):
    def __init__(
        self, url,
        projectName, deltaPath,
        tokenString=None,
        sourceRow=None, sourceCol=None,
        endRow=None,endCol=None,
        lineText=None,
    ):
        self.positions = []
        (
            self.url, self.projectName, self.deltaPath,
            self.tokenString,self.lineText,
        ) = (
            url, projectName, deltaPath,
            tokenString, lineText,
        )
        if sourceRow:
            self.positions.append( (sourceRow, sourceCol,endRow,endCol) )
    @classmethod
    def joined( cls, instances ):
        """Compress same-file references to a single instance"""
        result = []
        if instances:
            set = {}
            for instance in instances:
                key = instance.projectName,instance.deltaPath
                current = set.get( key )
                if current is None:
                    current = cls( instance.url, instance.projectName, instance.deltaPath, instance.tokenString )
                    set[key] = current
                    result.append( current )
                current.positions.extend( instance.positions )
        return result

