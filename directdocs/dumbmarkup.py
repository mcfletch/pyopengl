"""Simplistic wiki-like format parsing support"""
from __future__ import absolute_import
import re,os,sys,textwrap, datetime
import logging
import six
log = logging.getLogger( __name__ )

text_re = re.compile(
    r"""^[ \t]*?(''')(?P<commentary>.*?)(''')[ \t]*?$""",
    re.MULTILINE|re.I|re.DOTALL
)
block_splitter = re.compile(r"""\n[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
empty_line_matcher = re.compile(r"""[ \t]*\n""",re.MULTILINE|re.I|re.DOTALL)
#: ``[target link text]``, where the target has to look like a location -- a
#: scheme, a path, an anchor or a filename. Ordinary bracketed prose ("[--help
#: for the tunable knobs]") is left alone rather than becoming an invented link.
#: An optional ``class=name`` in front of the target puts that class on the
#: element, which is how a page floats one image against another.
markup_re = re.compile(
    r"""\[(?:class=(?P<cls>[\w-]+)[ ]+)?"""
    r"""(?P<url>(?:\w+://|[./#])[^ ]*|[^ ]+\.\w{2,4})[ ]+(?P<link_text>[^]]+)\]"""
    r"""|(?P<bald_url>https?\:\/\/[^ \t\n]+)"""
)
image_extensions = [ '.png','.jpg','.bmp','.tif' ]
dl = re.compile( r"""[ \t]*(?P<term>\w+)\W*[-][-]\W*(?P<def>.*)""" )

def format_docstring( docstring ):
    """Turn docstring into human commentary structures"""
    return Commentary( docstring )

def markup( text, child_function ):
    """Returns text, children"""

    new_text, children = "",[]
    offset = 0
    for match in markup_re.finditer( text ):
        if not offset:
            new_text = text[:match.start()]
        else:
            if children[-1].tail is None:
                children[-1].tail = text[offset:match.start()]
            else:
                children[-1].tail += text[offset:match.start()]
        offset = match.end()
        children.append( child_function( match ))
    if not offset:
        return text, children
    else:
        if children[-1].tail is None:
            children[-1].tail = text[offset:]
        else:
            children[-1].tail += text[offset:]
    return new_text, children

class Block( object ):
    """Block of text for presentation"""
    html_tag = 'div'
    html_class = ''
    def __init__( self, text=None, children=None, tail=None, cls=None ):
        """Initializes the block of text with given text"""
        self.text = text
        self.children = children
        self.tail = tail
        if cls:
            self.html_class = self.html_class + ' ' + cls 
        if self.text:
            self.text, children = self.markup( self.text )
            if not self.children:
                self.children = children
            else:
                self.children[:0] = children
    def markup( self, text ):
        """Returns text, children"""
        def child_function( match ):
            if match.group( 'url' ):
                url = match.group( 'url' )
                node_class = Anchor
                for suffix in image_extensions:
                    if url.endswith( suffix ):
                        node_class = Image
                return node_class(
                    match.group( 'link_text' ),
                    url,
                    cls=match.group( 'cls' ),
                )
            elif match.group( 'bald_url' ):
                url = match.group( 'bald_url' )
                return Anchor(
                    url,
                    url,
                )
            else:
                raise RuntimeError( "Unknown markup: %s", text )
        return markup( text, child_function )
    def append( self, value ):
        """Append given value to our content"""
        if isinstance( value, (str,six.text_type)):
            if self.children:
                last_child = self.children[-1]
                if last_child.tail:
                    last_child.tail += value
                else:
                    last_child.tail = value
            elif self.text:
                self.text += value
            else:
                self.text = value
            return True
        else:
            # is a node of some form...
            self.children.append( value )

class Grouping( Block ):
    def __init__( self,*args,**named ):
        super( Grouping, self ).__init__(*args,**named)
        if self.children is None:
            self.children = []

class Title( Block ):
    html_tag = 'h1'
    html_class = 'title'

def single_line( block ):
    """Whether a block is one line, ignoring trailing whitespace."""
    return len( block.strip().splitlines() ) == 1


def is_aligned( block ):
    """Whether a block's own spacing carries meaning.

    A table, a column of names against descriptions, a fragment of a shell
    session: all of them line up their continuation lines under something, and
    all of them read as nonsense once HTML has collapsed the runs of spaces that
    did the lining up. Detected by a line that is indented relative to the block
    once the block's common indent is removed.

    The first line of a block cut from a docstring begins right after the
    quotes, so it carries none of the indent its continuation lines do and
    cannot be part of the common prefix; the prefix is taken from the rest and
    applied to all of them.
    """
    lines = [line for line in block.splitlines() if line.strip()]
    if len( lines ) < 2:
        return False
    indent = min( indent_level( line ) for line in lines[1:] )
    return any( line[indent:][:1].isspace() for line in lines[1:] )


def indent_level( block ):
    """Number of characters of indent"""
    block = block.replace( '\t',' '*8)
    line = block.lstrip( ' ' )
    return len(block) - len(line)

class Commentary( Grouping ):
    """Used for human commentary"""
    html_tag = 'div'
    html_class = 'commentary'
    def __init__( self,text=None,*args,**named ):
        commentary = text
        text = None
        super( Commentary, self ).__init__(text,*args,**named)
        blocks = block_splitter.split( commentary )
        for block in blocks:
            level = indent_level( block )
            cls='indent-level-%s'%(level,)
            block = textwrap.dedent( block )
            if block.startswith( '*' ) or block.startswith( '-' ):
                ul = UL(cls=cls)
                li = None
                self.append( ul )
                for line in block.splitlines():
                    if line.startswith( '*' ) or line.startswith( '-'):
                        li = LI( line[1:].lstrip())
                        ul.append( li )
                    else:
                        if li:
                            li.append( line )
            elif dl.match( block ):
                dlist = DL( cls=cls )
                self.append( dlist )
                dd = None
                for line in block.splitlines():
                    match = dl.match( line )
                    if match:
                        dlist.append( DT( match.group('term')))
                        dd = DD( match.group('def'))
                        dlist.append( dd )
                    else:
                        if dd:
                            dd.append( line )
            elif single_line( block ) and block.startswith( '=' ) and block.endswith( '=' ):
                self.append( Title( block.strip( '=' ).strip(), cls=cls ))
            elif single_line( block ) and block.startswith( '_' ) and block.endswith( '_' ):
                title = Title( block.strip( '_' ).strip(), cls=cls )
                title.html_tag= 'h2'
                self.append( title )
            elif is_aligned( block ):
                self.append( Preformatted( block, cls=cls ))
            else:
                self.append( Paragraph( block,cls=cls ))

class Code( Block ):
    """Used for machine-executable code"""
    html_tag = 'div'
    html_class = 'code-sample'
    def markup( self, text ):
        return text, None
class CollapsedCode( Code ):
    html_class = 'code-sample collapsed'
class Paragraph( Block ):
    """Generic paragraph in commentary"""
    html_tag = 'div'
    html_class = 'paragraph'

class Preformatted( Block ):
    """A block whose own spacing is part of what it says.

    Rendered into a ``pre``, so the columns of a table and the indents of a
    sample survive; its text is not marked up, because a bracket or a bare URL
    inside aligned text is content rather than a link.
    """
    html_tag = 'pre'
    html_class = 'preformatted'
    def markup( self, text ):
        return text, None
class UL( Grouping ):
    """Unordered list in commentary"""
    html_tag = 'ul'
class LI( Block ):
    """Unordered list item in UL"""
    html_tag = 'li'

class DL( Grouping ):
    html_tag = 'dl'
class DT( Block ):
    html_tag = 'dt'
class DD( Block ):
    html_tag = 'dd'

class Anchor( Block ):
    """Simple url link/anchor value"""
    html_tag = 'a'
    def __init__( self, text, url, cls=None ):
        super( Anchor, self ).__init__( text, cls=cls )
        self.url = url
    def markup( self, text ):
        return self.text, []

class Image( Anchor ):
    html_tag = 'img'
