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
#                    print 'Expand', element.tag
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
        elif context is not None:
            print 'Not none but not a namespace'
#        else:
#            print 'Need to handle requires too'
    
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
            if name == 'glVertex4iv':
                import pdb
                pdb.set_trace()
            return_type = self._type_decl( proto )
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

class EnumNamespace( list ):
    def __init__( self, namespace, *args ):
        self.namespace = namespace 
        super( EnumNamespace, self ).__init__(*args)
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
class Feature( list ):
    def __init__( self, api, name, number ):
        self.api = api 
        self.name = name 
        self.number = number 
        super( Feature, self ).__init__()
class Extension( list ):
    def __init__(self, name, apis ):
        self.name = name 
        self.apis = apis # only available for these APIs
        super( Extension, self ).__init__()
class Require( list ):
    def __init__( self, profile=None, comment=None ):
        self.profile = profile 
        self.comment = comment 
        super( Require, self ).__init__()
class Remove( list ):
    def __init__( self, profile=None, comment=None ):
        self.profile = profile 
        self.comment = comment 
        super( Remove, self ).__init__()

def parse( xmlfile ):
    registry = Registry()
    registry.load( ET.fromstring( open( xmlfile ).read()) )
    return registry 


if __name__ == "__main__":
    registry = parse( sys.argv[1] )
    #registry.debug_types()
    #registry.debug_enums()
    registry.debug_commands()
    
