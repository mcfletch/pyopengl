#! /usr/bin/env python
"""Generates the PyOpenGL reference documentation"""
import glob, os, datetime
#import elementtree.ElementTree as ET
import lxml.etree as ET
import kid, logging 
log = logging.getLogger( 'generate' )

from directdocs.model import Function, Parameter, ParameterReference
from directdocs import model,references
from OpenGL import __version__
from OpenGL import GL, GLU, GLUT, GLE,GLX

OUTPUT_DIRECTORY = 'manual-%s'%(model.MAJOR_VERSION,)

IMPORTED_PACKAGES = [GL,GLU,GLUT,GLE,GLX]
PACKAGES = ['GL','GLU','GLUT','GLE','GLX']

DOCBOOK_NS = 'http://docbook.org/ns/docbook'
MML_NS = "http://www.w3.org/1998/Math/MathML"

WRAPPER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book SYSTEM "test" [ <!ENTITY nbsp " "> ]>

<book 
    xmlns="%s"
    xmlns:mml="%s">
%%s
</book>"""%( DOCBOOK_NS, MML_NS )

class Reference( model.Reference ):
    """Reference class with doc-set-specific coding"""
    def get_crossref( self, title, volume=None,section=None ):
        if volume is None:
            volume = '3G'
        key = '%s.%s'%(title,volume)
        if '(' in title:
            title = title.split('(')[0]
        if self.sections.has_key( key ):
            return self.sections[key]
        elif self.section_titles.has_key( title ):
            return self.section_titles[ title ]
        elif self.functions.has_key( title ):
            return self.functions[title]
        elif title.startswith( 'glX') or title.startswith( 'wgl' ):
            print 'Reference to', title, 'in', getattr(section,'title','Unknown')
            return None
        else:
            # try a linear scan for suffixed version...
            for name in self.functions.keys():
                if self.suffixed_name( name, title ) or self.suffixed_name( title,name ):
                    return self.functions[name]
            return None
            raise KeyError( 'Function %s referenced from %s not found'%(key, getattr(section,'title','Unknown') ))
    def url( self, target ):
        if isinstance( target, RefSect ):
            return './%s.xhtml'%(target.title,)
        elif isinstance( target, model.PyFunction ):
            return '%s#py-%s'%(self.url(target.section),target.name)
        elif isinstance( target, Function ):
            return '%s#c-%s'%(self.url(target.section),target.name)
        raise ValueError( """Don't know how to create url for %r"""%(target,))
    def package_names( self ):
        return PACKAGES
    def modules( self ):
        return IMPORTED_PACKAGES

class RefSect( model.RefSect ):
    query_namespace = {
        'd':DOCBOOK_NS,
        'm':MML_NS,
    }
    def process( self, tree ):
        processors = {
        }
        for function in dir(self):
            if function.startswith( 'process_' ):
                key = '{%s}%s'%(DOCBOOK_NS,function[8:])
                value = getattr( self, function )
                processors[key ] = value
        self.id = tree[0].get('id')
        self.title = self.name = tree[0].xpath( 
            './/d:refmeta/d:refentrytitle', 
            namespaces=self.query_namespace 
        )[0].text
        self.functions = dict([
            (x.text,Function(x.text,self))
            for x in tree[0].xpath( 
                './/d:refnamediv/d:refname', 
                namespaces=self.query_namespace 
            )
        ])
        self.purpose = tree[0].xpath( 
            './/d:refnamediv/d:refpurpose',namespaces=self.query_namespace
        )[0].text
        for func_prototype in tree[0].xpath(
            './/d:refsynopsisdiv/d:funcsynopsis/d:funcprototype',
            namespaces=self.query_namespace 
        ):
            self.process_funcprototype( func_prototype )
        processed_sections = {}
        for section in tree[0].xpath( './/d:refsect1', namespaces=self.query_namespace):
            id = section.get( 'id' )
            if '-parameters' in id or id == 'parameters':
                for varlist in section.xpath( './d:variablelist',namespaces=self.query_namespace):
                    self.process_variablelist( varlist )
            elif id.endswith( '-see_also' ):
                for entry in section.xpath( './/d:citerefentry',namespaces=self.query_namespace):
                    title,volume = entry[0].text, entry[1].text
                    self.see_also.append( (title,volume) )
            else:
                self.discussions.append( section )
            processed_sections[ id ] = True
        # global search for referenced constants...
        for item in tree[0].xpath( './/d:constant', namespaces=self.query_namespace ):
            self.constants[ item.text.strip() ] = True

        #for element in tree.iterdescendants():
        #   if element.tag in processors:
        #       processors[element.tag]( element )
        #   else:
        #       'no processor for', element.tag
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
        self.functions[ node.text ] = Function(node.text.strip())
    def process_funcprototype( self, node ):
        funcdef = node[0]
        params = node[1:]
        return_value = funcdef.text.strip()
        for child in funcdef:
            funcname = child.text
        paramresults = []
        for param in params:
            if not param.tag.endswith( '}void' ):
                typ = param.text 
                for item in param:
                    paramname = item.text 
                    if item.tail:
                        typ += item.tail
                try:
                    paramresults.append( Parameter(
                        data_type = typ,
                        name = paramname
                    ))
                except Exception, err:
                    print 'Failure retrieving parameter:', str(param)
        try:
            function = self.functions[ funcname ]
        except KeyError, err:
            function = Function(funcname,self)
            self.functions[ funcname ] = function
#           err.args += (self.functions.keys(),)
#           log.warn( """Unable to process function prototype for %r (current keys: %s)""", funcname, self.functions.keys() )
        function.return_value = return_value
        function.parameters = paramresults
        for param in paramresults:
            param.function = function
    def process_variablelist( self, node ):
        """Process a variable list into annotations"""
        set = []
        for entry in node:
            terms = []
            description = ''
            for item in entry:
                if item.tag.endswith( 'term' ):
                    value = [
                        x.text.strip() 
                        for x in item.iterdescendants() 
                        if (x.text and x.tag.endswith( '}parameter' ))
                    ]
                    terms.extend(value)
                else:
                    description = item  
            set.append( ParameterReference(terms,description))

        self.varrefs.extend( set )

def load_file( filename ):
    data = WRAPPER%(open(filename).read())
    try:
        return filter_comments( ET.XML( data ) )
    except Exception, err:
        log.error( "Failure loading file: %r", filename )
        raise

def filter_comments( tree ):
    for element in tree:
        if isinstance(element.tag, (str,unicode)):
            filter_comments( element )
        else:
            tree.remove( element )
    return tree

def init_output( ):
    if not os.path.isdir( OUTPUT_DIRECTORY ):
        print 'Creating new manual directory: %s'%(OUTPUT_DIRECTORY )
        os.mkdir( OUTPUT_DIRECTORY )
        for file in os.listdir( 'output' ):
            src = os.path.join( 'output', file )
            dst = os.path.join( OUTPUT_DIRECTORY, file )
            os.link( src, dst )


def main():
    init_output()
    
    if os.path.isfile( references.CACHE_FILE ):
        import pickle
        samples = pickle.loads( open(references.CACHE_FILE).read())
    else:
        log.warn( """Loading references directly, run ./references.py to pre-generate""" )
        samples = references.loadData()
    files = []
    for package in PACKAGES:
        files.extend(
            [(package,x) for x in glob.glob( 'original/%s/*.xml'%package )]
        )
    files.sort()
    ref = Reference()
    for package,path in files:
        #print 'loading', path
        try:
            tree = load_file( path )
        except Exception, err:
            err.args += (path,)
            raise
        r = RefSect( package, ref )
        r.process( tree )
        ref.append( r )
        r.get_samples( samples )
    ref.check_crossrefs()
    # now generate some files...
    serial = kid.XHTMLSerializer( decl=True )
    template = kid.Template( 
        file='templates/index.kid', 
        ref=ref, 
        date=datetime.datetime.now().isoformat(),
        version=__version__,
    )
    data = template.serialize( output=serial )
    open( os.path.join(OUTPUT_DIRECTORY,'index.xhtml'), 'w').write( data )

    for name,section in ref.sections.items():
        template = kid.Template(
            file = 'templates/section.kid',
            ref=ref,
            section=section,
            date=datetime.datetime.now().isoformat(),
            version=__version__,
        )
        data = template.serialize( output=serial )
        open( 
            os.path.join( OUTPUT_DIRECTORY,ref.url(section)), 'w'
        ).write( data )

if __name__ == "__main__":
    import logging 
    logging.basicConfig()
    main()

