#!/usr/bin/env python
'''Hacked version of Pyglet's gengl that produces PyOpenGL-based modules

To use, you have to do an svn co of pyglet to get the "tools" directory,
add the package "wraptypes" to your site-packages and you should be able
to run this script.

Note: currently the AGL module can only be generated on OS-X, GLX can only
be generated on a GLX platform (e.g. Linux), WGL should generate anywhere
as I'm using Alex's hacked/derived wgl.h as the source for it.

TODO:
    This wrapper is missing a lot of the operations from the original
    openglgenerator module.  It's only appropriate for generating the
    platform-specific modules (GLX, WGL, AGL).  Eventually should port
    the code from the openglgenerator module to support creating the
    extensions and core GL modules.
'''
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
__docformat__ = 'restructuredtext'
__version__ = '$Id: gengl.py,v 1.3 2008/05/02 18:49:57 mcfletch Exp $'

import marshal
import optparse
import os.path
import urllib2
import sys
import textwrap
import re

# monkey-patching the tool to support argument names...
from wraptypes import ctypesparser
class CtypesFunction( ctypesparser.CtypesFunction ):
    def __init__(self, restype, parameters):
        if parameters and parameters[-1] == '...':
             parameters = parameters[:-1]
        self.argnames = [ self.argname(p.declarator) for p in parameters ]
        super( CtypesFunction, self ).__init__( restype, parameters )
    def argname( self, parameter ):
        if not getattr( parameter, 'pointer', None ):
            return parameter
        else:
            return self.argname( parameter.pointer )
ctypesparser.CtypesFunction = CtypesFunction

from wraptypes import wrap

script_dir = os.path.abspath(os.path.dirname(__file__))

GLEXT_ABI_H = 'http://oss.sgi.com/projects/ogl-sample/ABI/glext.h'
GLEXT_NV_H = 'http://developer.download.nvidia.com/opengl/includes/glext.h'
GLXEXT_ABI_H = 'http://oss.sgi.com/projects/ogl-sample/ABI/glxext.h'
GLXEXT_NV_H = 'http://developer.download.nvidia.com/opengl/includes/glxext.h'
WGLEXT_ABI_H = 'http://oss.sgi.com/projects/ogl-sample/ABI/wglext.h'
WGLEXT_NV_H = 'http://developer.download.nvidia.com/opengl/includes/wglext.h'

AGL_H = '/System/Library/Frameworks/AGL.framework/Headers/agl.h'
GL_H = '/usr/include/GL/gl.h'
GLU_H = '/usr/include/GL/glu.h'
GLX_H = '/usr/include/GL/glx.h'
WGL_H = os.path.join(script_dir, 'wgl.h')
OSMESA_H = '/usr/include/GL/osmesa.h'

CACHE_FILE = os.path.join(script_dir, '.gengl.cache')
_cache = {}


def load_cache():
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            _cache = marshal.load(open(CACHE_FILE, 'rb')) or {}
        except:
            pass
    _cache = {}

def save_cache():
    try:
        marshal.dump(_cache, open(CACHE_FILE, 'wb'))
    except:
        pass

def read_url(url):
    if url in _cache:
        return _cache[url]
    if os.path.exists(url):
        data = open(url).read()
    else:
        data = urllib2.urlopen(url).read()
    _cache[url] = data
    save_cache()
    return data

class GLWrapper(wrap.CtypesWrapper):
    requires = None
    requires_prefix = None

    def __init__(self, header, match_re):
        self.header = header
        self.match_re = match_re
        super(GLWrapper, self).__init__()
    def handle_declaration(self, declaration, filename, lineno):
        """Overridden solely to pass in the argument names"""
        t = wrap.get_ctypes_type(declaration.type, declaration.declarator)
        declarator = declaration.declarator
        if declarator is None:
            # XXX TEMPORARY while struct with no typedef not filled in
            return
        while declarator.pointer:
            declarator = declarator.pointer
        name = declarator.identifier
        if declaration.storage == 'typedef':
            self.handle_ctypes_type_definition(
                name, wrap.remove_function_pointer(t), filename, lineno)
        elif type(t) == CtypesFunction:
            # this is the line we override
            self.handle_ctypes_function(
                name, t.restype, t.argtypes, filename, lineno, t.argnames)
        elif declaration.storage != 'static':
            self.handle_ctypes_variable(name, t, filename, lineno)

    def print_preamble(self):
        import time
        print >> self.file, textwrap.dedent("""
            # This content is generated by %(script)s.
            # Wrapper for %(header)s
            from OpenGL import platform, constant
            from ctypes import *
            c_void = None
        """ % {
            'header': self.header,
            'date': time.ctime(),
            'script': __file__,
        }).lstrip()

    def libFromRequires( self, requires  ):
        return self.library or 'platform.GL'

    def handle_ctypes_function(self, name, restype, argtypes, filename, lineno, argnames):
        if self.does_emit(name, filename):
            self.emit_type(restype)
            for a in argtypes:
                self.emit_type(a)

            self.all_names.append(name)
            #print >> self.file, '# %s:%d' % (filename, lineno)
            print >> self.file, '''%(name)s = platform.createBaseFunction(
    %(name)r, dll=%(libname)s, resultType=%(returnType)s,
    argTypes=[%(argTypes)s],
    doc=%(documentation)r,
    argNames=%(argNames)r,
)'''%dict(
    name = name,
    libname = self.libFromRequires( self.requires  ),
    returnType = restype,
    argTypes = ', '.join([str(a) for a in argtypes]),
    documentation = self.documentation(
        name, argnames, argtypes, restype
    ),
    argNames = [str(x) for x in argnames],
)
            print >> self.file
    def documentation( self, name, argnames, args, returntype ):
        """Customisation point for documenting a given function"""
        return str("%s( %s ) -> %s"%(
            name,
            ", ".join(
                [ '%s(%s)'%( typ, name) for (typ,name) in zip(args,argnames) ]
            ),
            returntype,
        ))

    def handle_ifndef(self, name, filename, lineno):
        if (
            self.requires_prefix and
            name[:len(self.requires_prefix)] == self.requires_prefix
        ):
            self.requires = name[len(self.requires_prefix):]
            print >> self.file, '# %s (%s:%d)'  % \
                (self.requires, filename, lineno)
    def handle_ctypes_constant(self, name, value, filename, lineno):
        if self.does_emit( name, filename ):
            print >> self.file, '%(name)s = constant.Constant( %(name)r, %(value)r )'%locals()
            self.all_names.append(name)
    def does_emit(self, symbol, filename):
        base = super( GLWrapper, self ).does_emit( symbol, filename )
        if base:
            if self.match_re:
                if self.match_re.match( symbol ):
                    return True
                else:
                    return False
        return base

def progress(msg):
    print >> sys.stderr, msg

marker_begin = '# BEGIN GENERATED CONTENT (do not edit below this line)\n'
marker_end = '# END GENERATED CONTENT (do not edit above this line)\n'

class ModuleWrapper(object):
    def __init__(
        self, header, filename,
        prologue='', requires_prefix=None, system_header=None,
        match_re=None, library=None,
    ):
        self.header = header
        self.filename = filename
        self.prologue = prologue
        self.requires_prefix = requires_prefix
        self.system_header = system_header
        self.match_re = match_re
        self.library = library

    def wrap(self, dir):
        progress('Updating %s...' % self.filename)
        source = read_url(self.header)
        filename = os.path.join(dir, self.filename)

        prologue = []
        epilogue = []
        state = 'prologue'
        try:
            for line in open(filename):
                if state == 'prologue':
                    prologue.append(line)
                    if line == marker_begin:
                        state = 'generated'
                elif state == 'generated':
                    if line == marker_end:
                        state = 'epilogue'
                        epilogue.append(line)
                elif state == 'epilogue':
                    epilogue.append(line)
        except IOError:
            prologue = [marker_begin]
            epilogue = [marker_end]
            state = 'epilogue'
        if state != 'epilogue':
            raise Exception('File exists, but generated markers are corrupt '
                            'or missing')

        outfile = open(filename, 'w')
        print >> outfile, ''.join(prologue)
        wrapper = GLWrapper(self.header, self.match_re)
        if self.system_header:
            wrapper.preprocessor_parser.system_headers[self.system_header] = \
                source
        header_name = self.system_header or self.header
        wrapper.requires_prefix = self.requires_prefix
        wrapper.begin_output(outfile,
                             library=self.library,
                             emit_filenames=(header_name,))
        source = self.prologue + source
        wrapper.wrap(header_name, source)
        wrapper.end_output()
        print >> outfile, ''.join(epilogue)

modules = {
	'gl':
		ModuleWrapper(GL_H, 'gl.py'),
##	'glu':
##		ModuleWrapper(GLU_H, 'glu.py'),
##	'glext_arb':
##		ModuleWrapper(GLEXT_ABI_H, 'glext_arb.py',
##			requires_prefix='GL_', system_header='GL/glext.h',
##			prologue='#define GL_GLEXT_PROTOTYPES\n#include <GL/gl.h>\n'),
##	'glext_nv':
##		ModuleWrapper(GLEXT_NV_H, 'glext_nv.py',
##			requires_prefix='GL_', system_header='GL/glext.h',
##			prologue='#define GL_GLEXT_PROTOTYPES\n#include <GL/gl.h>\n'),
#    'glx':
#        ModuleWrapper(GLX_H, '_GLX.py',
#            requires_prefix='GLX_',
#            match_re = re.compile( 'glX|GLX' ),
#        ),
#    'glx_arb':
#        ModuleWrapper(GLXEXT_ABI_H, '_GLX_ARB.py', requires_prefix='GLX_',
#            system_header='GL/glxext.h',
#            prologue='#define GLX_GLXEXT_PROTOTYPES\n#include <GL/glx.h>\n',
#            match_re = re.compile( 'glX|GLX_' ),
#        ),
#    'glx_nv':
#        ModuleWrapper(GLXEXT_NV_H, '_GLX_NV.py', requires_prefix='GLX_',
#            system_header='GL/glxext.h',
#            prologue='#define GLX_GLXEXT_PROTOTYPES\n#include <GL/glx.h>\n',
#            match_re = re.compile( 'glX|GLX_' ),
#        ),
#    'agl':
#        ModuleWrapper(AGL_H, 'AGL.py'),
#    'wgl':
#        ModuleWrapper(WGL_H, '_WGL.py'),
#    'wgl_arb':
#        ModuleWrapper(WGLEXT_ABI_H, '_WGL_ARB.py', requires_prefix='WGL_',
#            prologue='#define WGL_WGLEXT_PROTOTYPES\n'\
#                     '#include "%s"\n' % WGL_H.encode('string_escape')),
#    'wgl_nv':
#        ModuleWrapper(WGLEXT_NV_H, '_WGL_NV.py', requires_prefix='WGL_',
#            prologue='#define WGL_WGLEXT_PROTOTYPES\n'\
#                     '#include "%s"\n' % WGL_H.encode('string_escape')),
#    'osmesa':
#        ModuleWrapper(OSMESA_H,'osmesa.py',requires_prefix='OSMESA_',
#            library = 'OSMESA',
#        ),
}


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('-D', '--dir', dest='dir',
                  help='output directory')
    op.add_option('-r', '--refresh-cache', dest='refresh_cache',
                  help='clear cache first', action='store_true')
    options, args = op.parse_args()

    if not options.refresh_cache:
        load_cache()
    else:
        save_cache()

    if not args:
        print >> sys.stderr, 'Specify module(s) to generate:'
        print >> sys.stderr, '  %s' % ' '.join(modules.keys())

    if not options.dir:
        options.dir = os.path.join(script_dir, os.path.pardir, 'OpenGL', 'raw')
    if not os.path.exists(options.dir):
        os.makedirs(options.dir)

    for arg in args:
        if arg not in modules:
            print >> sys.stderr, "Don't know how to make '%s'" % arg
            continue

        modules[arg].wrap(options.dir)
