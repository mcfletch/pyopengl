#! /usr/bin/env python
import glob, os
#import elementtree.ElementTree as ET
import lxml.etree as ET

DOCBOOK_NS = 'http://docbook.org/ns/docbook'
MML_NS = "http://www.w3.org/1998/Math/MathML"

WRAPPER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book SYSTEM "test" [ <!ENTITY nbsp " "> ]>

<book 
	xmlns="%s"
	xmlns:mml="%s">
%%s
</book>"""%( DOCBOOK_NS, MML_NS )

class RefName( object ):
	def __init__( self,name ):
		self.name = name
	def __repr__( self ):
		return '%s( %s ) -> %s'%(
			self.name, 
			self.params,
			self.return_value,
		)
	name = None
	return_value = None 
	params = None 
class VariableRef( object ):
	def __init__( self ):
		self.names = {}
	description = None

class Reference( object ):
	id = None 
	title = None
	purpose = None
	def __init__( self ):
		self.refnames = {}
		self.varrefs = []
	def process_refentry( self, node ):
		if not self.id:
			self.id = node.get( 'id' )
	def process_refentrytitle( self, node ):
		if not self.title:
			self.title = node.text
	def process_refpurpose( self, node ):
		if not self.purpose:
			self.purpose = node.text
	def process_refname( self, node ):
		self.refnames[ node.text ] = RefName(node.text.strip())
	def process_variablelist( self, node ):
		
	def process_funcprototype( self, node ):
		funcdef = node[0]
		params = node[1:]
		return_value = funcdef.text.strip()
		for child in funcdef:
			funcname = child.text
		paramresults = []
		for param in params:
			typ = param.text 
			for item in param:
				paramname = item.text 
			try:
				paramresults.append( (typ,paramname))
			except NameError, err:
				pass
		refname = self.refnames[ funcname ]
		refname.return_value = return_value
		refname.params = paramresults
	def by_twos( self, it ):
		iterator = iter( it )
		try:
			while True:
				yield iterator.next(),iterator.next()
		except StopIteration, err:
			pass
	def process_variablelist( self, node ):
		"""Process a variable list into annotations"""
		set = []
		for term,item in self.by_twos(node):
			
	def process( self, tree ):
		processors = {
		}
		for function in dir(self):
			if function.startswith( 'process_' ):
				key = '{%s}%s'%(DOCBOOK_NS,function[8:])
				value = getattr( self, function )
				processors[key ] = value
		for element in tree.iterdescendants():
			if element.tag in processors:
				processors[element.tag]( element )
			else:
				'no processor for', element.tag
		


def load_file( filename ):
	data = WRAPPER%(open(filename).read())
	return ET.XML( data )

if __name__ == "__main__":
	for path in glob.glob( 'original/GL/*.xml' ):
		#print 'loading', path
		tree = load_file( path )
		r = Reference( )
		r.process( tree )
		print r.title,r.purpose
		for name,spec in r.refnames.items():
			print '\t', name 
			print '\t\t',spec
