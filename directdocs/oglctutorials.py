#! /usr/bin/env python
"""Generate the OpenGLContext shader tutorials from '''-string marked-up source code"""
from __future__ import absolute_import
from __future__ import print_function
import re,os,sys,textwrap, datetime
from genshi.template import TemplateLoader
import logging
from six.moves import range
log = logging.getLogger( 'tutorials' )
from .dumbmarkup import *

loader = TemplateLoader([os.path.join(os.path.dirname( __file__ ), 'templates')])

text_re = re.compile(
    r"""^[ \t]*?(''')(?P<commentary>.*?)(''')[ \t]*?$""",
    re.MULTILINE|re.I|re.DOTALL
)
block_splitter = re.compile(r"""\n[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
empty_line_matcher = re.compile(r"""[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
markup_re = re.compile(
    r"""\[(?P<url>[^ ]+)[ ]+(?P<link_text>[^]]+)\]"""
)
image_extensions = [ '.png','.jpg','.bmp','.tif' ]

import OpenGLContext
test_dir = os.path.join(
    os.path.dirname( OpenGLContext.__file__ ),
    '..',
    'tests',
)

OUTPUT_DIRECTORY=os.path.join(
    os.path.dirname( OpenGLContext.__file__ ),
    '..',
    'docs',
    'tutorials',
)
if not os.path.isdir( OUTPUT_DIRECTORY ):
    os.makedirs( OUTPUT_DIRECTORY )

class TutorialPath( Grouping ):
    """Path through a series of tutorials"""
    def generate_children( self ):
        first = self.children
        for i in range( len(first)):
            next = prev = None
            if i > 0:
                prev = first[i-1]
            if i < len(first)-1:
                next = first[i+1]
            generate( first[i], next=next,prev=prev, path=self )

REDIRECT = '''<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="refresh" content="1;url=%(base)s" />
</head>
<body>
    The content for this page has moved to <a href="%(base)s">HTML</a>.
</body>
</html>'''

def redirect( newfile, old_file=None ):
    if old_file is None:
        old_file = os.path.splitext( newfile )[0] + '.xhtml'
    base = os.path.basename( newfile )
    open( old_file, 'w' ).write(REDIRECT%locals())
    

            
class Tutorial( Grouping ):
    html_tag = 'body'
    html_class = 'tutorial'
    @property
    def title( self ):
        """find our first title descendant"""
        for item in self.children:
            if isinstance( item, Commentary ):
                for child in item.children:
                    if isinstance( child, Title ):
                        return child.text
        return "No title found"
    def set_file( self, filename ):
        base = os.path.basename( filename )
        self.filename = base
        root = os.path.splitext( base )[0]
        self.html_file = os.path.join(
            OUTPUT_DIRECTORY, '%s.html'%(root)
        )
        self.relative_link = '%s.html'%( root, )

def generate_index( paths ):
    """Generate index file for given paths"""
    next = paths[0].children[0]
    prev = paths[-1].children[-1]

    stream = loader.load(
        'tutorialindex.kid'
    ).generate(
        paths=paths,
        next = next,
        prev = prev,
        date=datetime.datetime.now().strftime( '%Y-%m-%d' ),
        version = OpenGLContext.__version__,
    )
    data = stream.render( 'html' )
    html_file = os.path.join( OUTPUT_DIRECTORY, 'index.html' )
    print('writing', html_file)
    open( html_file, 'w').write( data )
    redirect( html_file )

def generate( tutorial, prev=None, next=None, path=None ):
    stream = loader.load(
        'tutorial.kid',
    ).generate(
        tutorial = tutorial,
        date=datetime.datetime.now().isoformat(),
        path = path,
        prev=prev,
        next=next,
    )
    data = stream.render( 'html' )
    print('writing', tutorial.html_file)
    open( tutorial.html_file, 'w').write( data )
    redirect( tutorial.html_file )

def parse_file( filename ):
    text = open( filename ).read().replace( '\r\n','\n' )
    tutorial = Tutorial()
    tutorial.set_file( filename )
    offset = 0
    for match in text_re.finditer( text ):
        py_text = text[ offset: match.start()]
        empty_match = empty_line_matcher.match( py_text )
        if empty_match:
            py_text = py_text[empty_match.end():]
        if py_text.strip():
            if py_text.lstrip().startswith( '#collapse' ):
                code = CollapsedCode( '\n'.join(py_text.splitlines()[1:] ))
            else:
                code = Code( py_text )
            tutorial.append( code )
        if match.group( 'commentary' ).strip():
            tutorial.append(
                Commentary( match.group('commentary') )
            )
        offset = match.end()
    if text[offset:].strip():
        tutorial.append( Code( text[ offset:] ) )
    return tutorial

if __name__ == "__main__":
    shaders = TutorialPath(
        "Introduction to Shaders",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'shader_intro.py',
                'shader_1.py',
                'shader_2.py',
                'shader_3.py',
                'shader_4.py',
                'shader_5.py',
                'shader_6.py',
                'shader_7.py',
                'shader_8.py',
                'shader_9.py',
                'shader_10.py',
                'shader_11.py',
                'shader_12.py',
                'shader_instanced.py',
            ]
        ]
    )
    matrices = TutorialPath(
        "Transformations and Matrices",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'transforms_1.py',
            ]
        ]
    )
    effects = TutorialPath(
        "Depth-map Shadows",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'shadow_1.py',
                'shadow_2.py',
            ]
        ],
    )
    nodes = TutorialPath(
        "Scenegraph Nodes",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'lightobject.py',
                'molehill.py',
                'nurbsobject.py',
                'particles_simple.py',
            ]
        ]
    )
    nehe = TutorialPath(
        "NeHe Translations",
        children =[
            parse_file( os.path.join( test_dir,name ))
            for name in [
                'nehe1.py',
                'nehe2.py',
                'nehe3.py',
                'nehe4.py',
                'nehe5.py',
                'nehe6.py',
                'nehe7.py',
                'nehe8.py',
                'nehe6_timer.py',
                'nehe6_multi.py',
                'glprint.py',
            ]
        ]
    )
    paths = [shaders,matrices,nodes,effects,nehe]
    generate_index( paths = paths )
    for path in paths:
        path.generate_children()

