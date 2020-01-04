#! /usr/bin/env python3
"""Generates the PyOpenGL reference documentation"""
from __future__ import absolute_import
from __future__ import print_function
import glob, os, datetime, subprocess, re, sys
#import elementtree.ElementTree as ET
import lxml.etree as ET
from genshi.template import TemplateLoader
import logging
import six
log = logging.getLogger( 'generate' )

from directdocs.model import Function, Parameter, ParameterReference
from directdocs import model,references
from OpenGL import __version__
from OpenGL._bytes import as_8_bit
from OpenGL import GL, GLU, GLUT, GLE,GLX

loader = TemplateLoader([os.path.join(os.path.dirname( __file__ ), 'templates')])

OUTPUT_DIRECTORY = 'manual-%s'%(model.MAJOR_VERSION,)

IMPORTED_PACKAGES = [GL,GLU,GLUT,GLE,GLX]
PACKAGES = ['GL','GLU','GLUT','GLE','GLX']

DOCBOOK_NS = 'http://docbook.org/ns/docbook'
MML_NS = "http://www.w3.org/1998/Math/MathML"
XML_NS = "http://www.w3.org/XML/1998/namespace"
LINK_NS = "http://www.w3.org/1999/xlink"

WRAPPER = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book SYSTEM "test" [ <!ENTITY nbsp " "> ]>

<book
    xmlns="%s"
    xmlns:mml="%s"
    xmlns:xlink="%s"
>
%%s
</book>"""%tuple( as_8_bit(x) for x in [DOCBOOK_NS, MML_NS, LINK_NS ] )

IMPLEMENTATION_MODULES = [
    # modules which contain external API entry points...
    ('error','GL-specific error classes'),
    ('extensions','Utility code for accessing OpenGL extensions, including the "alternate" mechanism'),
    ('plugins','Trivial plugin mechanism, used to register new data-types'),
    ('arrays.vbo','Convenience module providing a Vertex Buffer Object abstraction layer'),
    ('GL.shaders','Convenience module providing a GLSL Shader abstraction layer (alternate declarations, convenience functions)'),
    #'Tk','GLX',
]


class Reference( model.Reference ):
    """Reference class with doc-set-specific coding"""
    def get_crossref( self, title, volume=None,section=None ):
        if volume is None:
            volume = '3G'
        key = '%s.%s'%(title,volume)
        if '(' in title:
            title = title.split('(')[0]
        if key in self.sections:
            return self.sections[key]
        elif title in self.section_titles:
            return self.section_titles[ title ]
        elif title in self.functions:
            return self.functions[title]
        elif title.startswith( 'glX') or title.startswith( 'wgl' ):
            print('Reference to', title, 'in', getattr(section,'title','Unknown'))
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
            return './%s.html'%(target.title,)
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
        if not self.id:
            # newer files use a prefixed "id" attribute...
            self.id = tree[0].get('{http://www.w3.org/XML/1998/namespace}id')
        assert self.id
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
            id = section.get( 'id' ) or section.get( '{%s}id'%(XML_NS))
            if id and '-parameters' in id or id.startswith('parameters'):
                for varlist in section.xpath( './d:variablelist',namespaces=self.query_namespace):
                    self.process_variablelist( varlist )
            elif id and id.endswith( '-see_also' ):
                for entry in section.xpath( './/d:citerefentry',namespaces=self.query_namespace):
                    title,volume = entry[0].text, entry[1].text
                    self.see_also.append( (title,volume) )
            elif id:
                self.discussions.append(section)
            elif not id:
                log.warn( 'Found reference section without id: %s', list(section.items()) )
                self.discussions.append( section )
                continue
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
            if not (param.tag.endswith( '}void' ) or (param.text or '').strip() == 'void' ):
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
                except Exception as err:
                    print('Failure retrieving parameter:', str(param))
        try:
            function = self.functions[ funcname ]
        except KeyError as err:
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

HEADER_KILLER = re.compile( b'[<][!]DOCTYPE.*?[>]', re.MULTILINE|re.DOTALL )
def strip_bad_header( data ):
    """Header in the xml files declared from opengl.org doesn't declare namespaces but files use them"""
    match = HEADER_KILLER.search( data )
    if not match: # GLUT and GLE don't have this...
        return data
    return data[match.end():]
       

def load_file( filename ):
    data = WRAPPER%(strip_bad_header(open(filename,'rb').read()))
    # data = open(filename).read()
    parser = ET.ETCompatXMLParser(resolve_entities=False)
    try:
        return filter_comments( ET.XML( data, parser ) )
    except Exception as err:
        log.error( "Failure loading file: %r", filename )
        raise

def filter_comments( tree ):
    for element in tree:
        if isinstance(element.tag, (str,six.text_type)):
            filter_comments( element )
        else:
            tree.remove( element )
    return tree

def init_output( ):
    if not os.path.isdir( OUTPUT_DIRECTORY ):
        print('Creating new manual directory: %s'%(OUTPUT_DIRECTORY ))
        os.mkdir( OUTPUT_DIRECTORY )
    for file in os.listdir( 'output' ):
        src = os.path.join( 'output', file )
        dst = os.path.join( OUTPUT_DIRECTORY, file )
        if os.path.exists( dst ):
            os.remove( dst )
        os.link( src, dst )


def api_entry_point(name):
    for prefix in ['glu','glX','gl']:
        if name.startswith(prefix):
            return prefix 
    return None

        
REDIRECT = '''<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="refresh" content="1;url=%(base)s" />
</head>
<body>
    The content for this page has moved to <a href="%(base)s">HTML</a>.
</body>
</html>'''

def main():
    limit_to = sys.argv[1:]
    init_output()

    log.info( 'Loading references' )
    if os.path.isfile( references.CACHE_FILE ):
        import pickle
        samples = pickle.loads( open(references.CACHE_FILE,'rb').read())
    else:
        log.warn( """Loading references directly, run ./references.py to pre-generate""" )
        samples = references.loadData()
    base_names = set()
    files = []
    for package in ['gl4','gl2.1','eg3.1','es3.0','es3','es2.0','es1.1']:
        for filename in glob.glob('OpenGL-Refpages/%s/*.xml'%(package,)):
            base = os.path.basename(filename)
            api = api_entry_point(base)
            if api:
                if limit_to:
                    allowed = False
                    for filter in limit_to:
                        if filter in base:
                            allowed=True 
                    if not allowed:
                        continue
                if base not in base_names:
                    base_names.add(base)
                    files.append((api.upper(),filename))
                else:
                    log.info("%s exists in multiple apis", base)
    for section in ['GLUT','GLE']:
        for filename in glob.glob('original/%(section)s/*.xml'%locals()):
            files.append((section,filename))
    files = sorted(files)[::-1]
    ref = Reference()
    for package,path in files:
        log.info( 'Loading: %s', path )
        #print 'loading', path
        try:
            tree = load_file( path )
        except (Exception,ET.XMLSyntaxError) as err:
            err.args += (path,)
            raise
        else:
            r = RefSect( package, ref )
            r.process( tree )
            ref.append( r )
            r.get_samples( samples )
    log.info( 'Checking cross-references' )
    ref.check_crossrefs()
    # now generate some files...
    log.info( 'Generating index' )
    stream = loader.load(
        'index.kid',
    ).generate(
        ref=ref,
        date=datetime.datetime.now().isoformat(),
        version=__version__,
        implementation_module_names = IMPLEMENTATION_MODULES,
    )
    data = stream.render('html')
    open( os.path.join(OUTPUT_DIRECTORY,'index.html'), 'w').write( data )
    base = 'index.html'

    for name,section in sorted(ref.sections.items()):
        output_file = os.path.join( OUTPUT_DIRECTORY,ref.url(section))
        log.warn( 'Generating: %s -> %s',name, output_file )
        # log.info( 'Input xml: %s', ET.tostring(section.reference))
        stream = loader.load(
            'section.kid',
        ).generate(
            ref=ref,
            section=section,
            date=datetime.datetime.now().isoformat(),
            version=__version__,
        )
        data = stream.render('html')
        data = data.encode('utf-8')
        open(
            output_file, 'wb'
        ).write( data )
        

    # Now store out references for things which want to do Python: refsect
    # lookups...
    mapping = {}
    for sectname,section in ref.sections.items():
        for function in section.functions.keys():
            mapping[function] = ref.url( section )
        for pyname in section.py_functions.keys():
            if pyname in mapping:
                log.warn( 'Duplicate python function name: %s', pyname )
            mapping[pyname] = ref.url( section )
    data = pickle.dumps( mapping )
    open( '.pyfunc-urls.pkl','wb').write( data )

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    main()
