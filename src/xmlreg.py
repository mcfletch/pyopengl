#! /usr/bin/env python
"""Registry for loading Khronos API definitions from XML files"""
from lxml import etree as ET
import os, sys, json, logging
from OpenGL._bytes import as_8_bit
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )

LENGTH_OVERRIDES={
    'glGetPolygonStipple': {
        'mask': str(32*32/8), # 32x32 bits
    },
    'glGetUniformfv': {
        'params': None,
    },
    'glGetUniformiv': {
        'params': None,
    },
#    'glShaderSourceARB': {
#        'string': None,
#    },
#    'glShaderSource': {
#        'string': None,
#    },
}


class Registry( object ):
    def __init__( self ):
        self.type_set = {}
        self.enum_namespaces = {}
        self.enum_groups = {}
        self.enumeration_set = {}
        self.command_set = {}
        self.apis = {}
        self.feature_set = {}
        self.extension_set = {}
        self.output_mapping = json.loads( open( os.path.join( HERE, 'gl_out_parameters.json' )).read())
        self.output_enum_groups = {}
        
    def load( self, tree ):
        """Load an lxml.etree structure into our internal descriptions"""
        self.dispatch( tree, None )
    
    def dispatch( self, tree, context=None):
        """Dispatch for all children of the element"""
        for element in tree:
            if isinstance( element.tag, (str,unicode)):
                method = getattr( self, element.tag, None )
                if method:
                    method( element, context )
                else:
                    print 'Expand', element.tag
                    self.dispatch( element, context )
    
    def type( self, element, context=None ):
        name = element.get('name')
        if not name:
            name = element.find('name').text 
        self.type_set[as_8_bit(name)] = element 
    
    def debug_types( self ):
        for name,type in self.types.items():
            print name, type
    
    def enums( self, element, context=None ):
        name = as_8_bit(element.get('namespace'))
        if name not in self.enum_namespaces:
            namespace = EnumNamespace(name)
            self.enum_namespaces[name] = namespace
        else:
            namespace = self.enum_namespaces[name]
        self.dispatch( element, namespace )
    
    def enum( self, element, context=None ):
        if isinstance( context, EnumNamespace ):
            name,value = as_8_bit(element.get('name')),element.get('value')
            enum = Enum( name, value )
            context.append( enum )
            self.enumeration_set[name] = enum
        elif isinstance( context, (Require,Remove)):
            context.append( self.enumeration_set[element.get('name')] )
        elif isinstance( context, EnumGroup ):
            name = element.get('name')
            assert name, 'No name on %s'%ET.tostring(element)
            context.append( as_8_bit(name) )
    
    def debug_enums( self ):
        for name,namespace in self.enum_namespaces.items():
            print 'Namespace', namespace.namespace
            for enum in namespace:
                print '  ', enum
    
    def command( self, element, context=None ):
        """Parse command definition into structured format"""
        proto = element.find( 'proto' )
        if proto is not None:
            name = as_8_bit(proto.find('name').text)
            assert name, 'No name in command: %s'%(ET.tostring( element))
            return_type = self._type_decl( proto )
            assert return_type, 'No return type in command: %s'%(ET.tostring( element))
            arg_names = []
            arg_types = []
            lengths = {}
            groups = {}
            for param in [x for x in element if x.tag == 'param']:
                pname = as_8_bit(param.find( 'name' ).text)
                arg_names.append( pname )
                arg_types.append( self._type_decl( param ))
                if param.get( 'len' ):
                    length = param.get('len')
                    while length.endswith( '*1' ):
                        length = length[:-2]
                    length = LENGTH_OVERRIDES.get(name,{}).get(pname,length)
                    lengths[pname] = length 
                if param.get( 'group' ):
                    groups[pname] = param.get('group')
            aliases = []
            for alias in [x for x in element if x.tag == 'alias']:
                aliases.append( alias.get('name') )
            # Process lengths to look for output parameters
            outputs = self.output_mapping.get( name )
            command = Command( name, return_type, arg_names, arg_types, aliases, lengths,groups, outputs=outputs )
            self.command_set[name] = command
        elif isinstance( context, (Require,Remove)):
            context.append( self.command_set[element.get('name')])
    
    def _type_decl( self, proto ):
        """Get the string type declaration for parent (proto/param)"""
        return_type = []
        if proto.text:
            return_type.append( proto.text )
        for item in proto:
            if item.tag == 'name':
                break
            else:
                if item.text:
                    return_type.append(item.text.strip())
                if item.tail:
                    return_type.append(item.tail.strip())
        return ' '.join( [x for x in return_type if x] ) or 'void'
    
    def debug_commands( self ):
        for name,command in sorted(self.command_set.items()):
            print command
        
    def feature( self, element, context=None ):
        api,name,number = [element.get(x) for x in ('api','name','number')]
        feature = Feature( api, name, number )
        self.feature_set[name] = feature 
        self.dispatch( element, feature )
    def extension( self, element, context=None ):
        name,apis,require = [element.get(x) for x in ['name','supported','protect']]
        extension = Extension( name, apis.split('|'),require)
        self.extension_set[name] = extension
        self.dispatch( element, extension )
    def unused( self, element, context=None):
        pass
    def group( self, element, context=None):
        name = element.get('name')
        current = self.enum_groups.get( name )
        if current is None:
            current = self.enum_groups[name] = EnumGroup( name )
        self.dispatch( element, current )
    
    def require( self, element, context ):
        if isinstance( context, (Feature,Extension)):
            profile,comment = element.get('profile'),element.get('comment')
            require = Require( profile, comment )
            context.append( require )
            self.dispatch( element, require )
    def remove( self, element, context ):
        if isinstance( context, Feature):
            profile,comment = element.get('profile'),element.get('comment')
            remove = Remove( profile, comment )
            context.append( remove )
            self.dispatch( element, remove )
    
    def debug_apis( self ):
        print [x.api for x in self.feature_set.values()]

class EnumNamespace( list ):
    def __init__( self, namespace, *args ):
        self.namespace = namespace 
        super( EnumNamespace, self ).__init__(*args)
class EnumGroup( list ):
    def __init__( self, name, *args ):
        self.name = name 
        super( EnumGroup, self ).__init__( *args )
class Enum( object ):
    def __init__( self, name, value ):
        self.name = name 
        self.value = value
    def __repr__( self ):
        return '%s = %s'%( self.name, self.value )

class Command( object ):
    def __init__( self, name, returnType, argNames, argTypes, aliases=None, lengths=None, groups=None, outputs=None ):
        self.name =name 
        self.returnType = returnType 
        self.argNames = argNames 
        self.argTypes = argTypes
        self.aliases = aliases or []
        self.lengths = lengths or {}
        self.groups = groups or {}
        self.outputs = outputs or {}
        self.output_groups = {}
        self.size_dependencies = self.calculate_sizes()
    def __repr__( self ):
        return '%s %s( %s )'%( 
            self.returnType, 
            self.name, 
            ', '.join([
                '%s %s'%(typ,name) 
                for (typ,name) in zip( self.argTypes,self.argNames )
            ])
        )
    def calculate_sizes( self ):
        result = []
        other_lengths = self.lengths.copy()
        for target in self.outputs.keys():
            definition = self.lengths.get( target )
            if definition is None:
                if target not in self.argNames:
                    # may be a discrepency between .spec and xml registry file...
                    if target == 'params' and 'data' in self.argNames:
                        target = 'data'
                        definition = self.lengths.get( 'data' )
            if target in other_lengths:
                del other_lengths[target]
        
            if definition is None:
                result.append( (target, Output() ))
            elif definition.startswith( 'COMPSIZE' ):
                variables = definition[8:].strip('()').split(',')
                output_groups = {}
                if len(variables) == 1:
                    # for now we only support automated single-dependency wrapping...
                    for var in variables:
                        if var in self.groups:
                            output_groups.setdefault( self.groups[var], []).append( target )
                    self.output_groups.update( output_groups )
                result.append( (target,Compsize( variables, output_groups )))
            elif definition.isdigit():
                result.append( (target,Staticsize( int(definition,10))))
            elif '*' in definition:
                var,multiple = definition.split('*')
                result.append( (target,Multiple( var, int(multiple,10))))
            else:
                result.append( (target,Dynamicsize( definition )))
        for (target,length) in other_lengths.items():
            if length is None:
                # length/array-conversion suppressed
                continue 
            if length.isdigit():
                result.append( (target,StaticInput( int(length,10))))
            elif length.startswith( 'COMPSIZE' ):
                result.append( (target,Input(length[9:-1])))
            elif length in self.argNames:
                result.append( (target,DynamicInput(length)))
            elif '*' in length:
                params = length.split('*')
                in_set = [
                    x for x in params 
                    if x in self.argNames
                ]
#                if params == in_set:
                result.append( (target,MultipleInput(params)))
#                else:
#                    result.append( (target, Input()))
            else:
                raise RuntimeError( (target,length))
        return dict(result)
class IsInput(object):
    pass
class Input( IsInput, object ):
    """Unsized Input Parameter"""
    def __init__( self, value=None ):
        self.value = value
    def __repr__( self ):
        return repr(self.value)
class StaticInput( IsInput,int ):
    """Statically sized input parameter"""
class DynamicInput( IsInput,str ):
    """Dynamically sized based on other parameter"""
class MultipleInput( IsInput,list ):
    """Size depends on multiple elements being multiplied"""
    def __str__( self ):
        return '*'.join( self )
        
class Output( object ):
    """Unsized output parameter"""
class Compsize( list ):
    """Compute size based on other variables"""
    def __init__( self, iterable, groups=None ):
        super( Compsize,self ).__init__( iterable )
        self.groups = groups

class Staticsize( int ):
    """Static output array size"""
class Dynamicsize( str ):
    """Sized by the value in dynamic variable"""
class Multiple( list ):
    """Variable * static size for array"""

# The order-dependent set of require/remove holding features/extensions
class Module( list ):
    """Base class for Features and Extensions"""
    feature = False
    def __init__( self, name ):
        self.name = name 
    def members( self, of_type=None ):
        members = []
        for req in self:
            if req.require:
                for item in req:
                    if of_type is not None:
                        if isinstance( item, of_type ):
                            members.append( item )
                    else:
                        members.append( item )
        return members
    def enums( self ):
        return self.members( Enum )
    def commands( self ):
        return self.members( Command )


class Feature( Module ):
    feature = True
    NORMALIZERS = {
        'GL_VERSION_ES_CM_1_0': 'GLES_VERSION_1_0',
        'GL_ES_VERSION_2_0': 'GLES_VERSION_2_0',
        'GL_ES_VERSION_3_0': 'GLES_VERSION_3_0',
    }
    def __init__( self, api,name,number ):
        super( Feature, self ).__init__(self.NORMALIZERS.get(name,name))
        self.api = api 
        if name == 'GL_ES_VERSION_3_0':
            self.api = 'gles3'
        self.number = number 
    _profiles = None
    @property 
    def profiles( self ):
        """Create set of profiles with subsets of our functionality"""
        if self._profiles is None:
            profiles = {}
            for req in self:
                # Logic isn't right here, there's a base and then 
                # a set of profiles which customize the base...
                profile = req.profile or ''
                set = profiles.get( profile )
                if set is None:
                    set = Module( profile or '' )
                    set.feature = True
                    profiles[profile] = set
                if req.require:
                    
                    set.extend( req )
                else:
                    for item in req:
                        while item in set:
                            set.remove( item )
            self._profiles = sorted(profiles.values(),key=lambda x: x.name)
        return self._profiles
    
class Extension( Module ):
    def __init__(self, name, apis, require=None ):
        super( Extension, self ).__init__(name)
        self.apis = apis # only available for these APIs
        self.require = require
    @property
    def profiles( self ):
        module = Module( 'default' )
        module.extend( self )
        return module
    
class Require( list ):
    require = True
    remove = False
    def __init__( self, profile=None, comment=None ):
        self.profile = profile 
        self.comment = comment 
        super( Require, self ).__init__()
class Remove( list ):
    require = False
    remove = True
    def __init__( self, profile=None, comment=None ):
        self.profile = profile 
        self.comment = comment 
        super( Remove, self ).__init__()

def parse( xmlfile ):
    registry = Registry()
    registry.load( ET.fromstring( open( xmlfile ).read()) )
    return registry 


if __name__ == "__main__":
    if sys.argv[1:]:
        for file in sys.argv[1:]:
            print file
            registry = parse( file )
    
    #registry.debug_types()
    #registry.debug_enums()
    #registry.debug_commands()
    #registry.debug_apis()
    
