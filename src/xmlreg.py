#! /usr/bin/env python
"""Registry for loading Khronos API definitions from XML files"""
from lxml import etree as ET
import os, sys, time

class Registry( object ):
    def __init__( self ):
        self.type_set = {}
        self.enum_namespaces = {}
        self.enumeration_set = {}
        self.command_set = {}
        self.apis = {}
        self.feature_set = {}
        self.extension_set = {}
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
        self.type_set[name] = element 
    
    def debug_types( self ):
        for name,type in self.types.items():
            print name, type
    
    def enums( self, element, context=None ):
        name = element.get('namespace')
        if name not in self.enum_namespaces:
            namespace = EnumNamespace(name)
            self.enum_namespaces[name] = namespace
        else:
            namespace = self.enum_namespaces[name]
        self.dispatch( element, namespace )
    
    def enum( self, element, context=None ):
        if isinstance( context, EnumNamespace ):
            name,value = element.get('name'),element.get('value')
            enum = Enum( name, value )
            context.append( enum )
            self.enumeration_set[name] = enum
        elif isinstance( element, (Require,Remove)):
            context.append( self.enumeration_set[name] )
        elif isinstance( element, EnumGroup ):
            name = element.get('name')
            assert name, 'No name on %s'%ET.tostring(element)
            context.append( name )
    
    def debug_enums( self ):
        for name,namespace in self.enum_namespaces.items():
            print 'Namespace', namespace.namespace
            for enum in namespace:
                print '  ', enum
    
    def command( self, element, context=None ):
        """Parse command definition into structured format"""
        proto = element.find( 'proto' )
        if proto is not None:
            name = proto.find('name').text
            assert name, 'No name in command: %s'%(ET.tostring( element))
            return_type = self._type_decl( proto )
            assert return_type, 'No return type in command: %s'%(ET.tostring( element))
            arg_names = []
            arg_types = []
            for param in [x for x in element if x.tag == 'param']:
                arg_names.append( param.find( 'name' ).text)
                arg_types.append( self._type_decl( param ))
            aliases = []
            for alias in [x for x in element if x.tag == 'alias']:
                aliases.append( alias.get('name') )
            command = Command( name, return_type, arg_names, arg_types, aliases )
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
        self.dispatch( element, extension )
    def unused( self, element, context=None):
        pass
    def group( self, element, context=None):
        group = EnumGroup( element.get('name'))
        self.dispatch( element, group )
    
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
    def __init__( self, name, crep ):
        self.name = name 
        self.crep = crep 
    def __repr__( self ):
        return '%s = %s'%( self.name, self.crep,)

class Command( object ):
    def __init__( self, name, returnType, argNames, argTypes, aliases=None ):
        self.name =name 
        self.returnType = returnType 
        self.argNames = argNames 
        self.argTypes = argTypes
        self.aliases = aliases or []
    def __repr__( self ):
        return '%s %s( %s )'%( 
            self.returnType, 
            self.name, 
            ', '.join([
                '%s %s'%(typ,name) 
                for (typ,name) in zip( self.argTypes,self.argNames )
            ])
        )

# The order-dependent set of require/remove holding features/extensions
class Module( list ):
    """Base class for Features and Extensions"""
    feature = False
    def __init__( self, name ):
        self.name = name 

class Feature( Module ):
    feature = True
    NORMALIZERS = {
        'GL_VERSION_ES_CM_1_0': 'GL_ES_VERSION_1_0',
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
    
