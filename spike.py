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
	def __init__( self,name, section ):
		self.name = name
		self.section = section
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
	def __init__( self, names, description ):
		self.names = names 
		self.description = description
	def __repr__( self ):
		result = []
		return '\t\t%s -- %s'%( ', '.join(self.names), self.description )

class Reference( object ):
	"""Overall reference text"""
	def __init__( self ):
		self.sections = {}
		self.functions = {}
		self.constants = {}
	def append( self, section ):
		"""Add the given section to our tables"""
		self.sections[section.id] = section
		for function in section.refnames.values():
			self.functions[ function.name ] = function 


class RefSect( object ):
	query_namespace = {
		'd':DOCBOOK_NS,
		'm':MML_NS,
	}
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
				if item.tail:
					typ += item.tail
			try:
				paramresults.append( (typ,paramname))
			except NameError, err:
				pass
		try:
			refname = self.refnames[ funcname ]
		except KeyError, err:
			err.args += (self.refnames.keys(),)
			raise
		refname.return_value = return_value
		refname.params = paramresults
	def process_variablelist( self, node ):
		"""Process a variable list into annotations"""
		set = []
		for entry in node:
			terms = []
			description = ''
			for item in entry:
				if item.tag.endswith( 'term' ):
					value = "".join( [x.text.strip() for x in item.iterdescendants() if x.text] )
					terms.append(value)
				else:
					description = item	
			set.append( VariableRef(terms,description))

		self.varrefs.extend( set )

	def process( self, tree ):
		processors = {
		}
		for function in dir(self):
			if function.startswith( 'process_' ):
				key = '{%s}%s'%(DOCBOOK_NS,function[8:])
				value = getattr( self, function )
				processors[key ] = value
		self.id = tree[0].get('id')
		self.title = tree[0].xpath( './/d:refmeta/d:refentrytitle', self.query_namespace )[0].text
		self.refnames = dict([(x.text,RefName(x.text,self)) for x in tree[0].xpath( './/d:refnamediv/d:refname', self.query_namespace )])
		self.purpose = tree[0].xpath( './/d:refnamediv/d:refpurpose',self.query_namespace)[0].text
		for func_prototype in tree[0].xpath( './/d:refsynopsisdiv/d:funcsynopsis/d:funcprototype', self.query_namespace ):
			self.process_funcprototype( func_prototype )
		processed_sections = {}
		for section in tree[0].xpath( './/d:refsect1', self.query_namespace):
			id = section.get( 'id' )
			if id.endswith( '-parameters' ):
				for varlist in section.xpath( './d:variablelist',self.query_namespace):
					self.process_variablelist( varlist )
			processed_sections[ id ] = True 

		#for element in tree.iterdescendants():
		#	if element.tag in processors:
		#		processors[element.tag]( element )
		#	else:
		#		'no processor for', element.tag
		


def load_file( filename ):
	data = WRAPPER%(open(filename).read())
	return ET.XML( data )

if __name__ == "__main__":
	files = glob.glob( 'original/GL/*.xml' ) + glob.glob( 'original/GLUT/*.xml' ) + glob.glob( 'original/GLE/*.xml' ) 
	files.sort()
	ref = Reference()
	for path in files:
		#print 'loading', path
		tree = load_file( path )
		r = RefSect( )
		r.process( tree )
		ref.append( r )
	
		print r.id,r.title,r.purpose
		for name,spec in r.refnames.items():
			print '\t', name 
			print '\t\t',spec
		for varref in r.varrefs:
			print varref

