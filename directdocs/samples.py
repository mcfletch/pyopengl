#! /usr/bin/env python3
"""Downloads project source checkouts for integration as samples"""
from __future__ import absolute_import
from __future__ import print_function
import os, subprocess
SAMPLE_DIRECTORY = '.samples'

class BaseSource( object ):
    def __init__( self, root, project=None, dirname=None ):
        self.root = root 
        self.project = project 
        if dirname is None:
            dirname = project
        self.dirname = dirname 
    def checkout( self ):
        command = self.checkout_command
        print(command)
        subprocess.check_output(command,shell=True)
    def update( self ):
        if os.path.exists( self.dirname ):
            cwd = os.getcwd()
            try:
                os.chdir( self.dirname )
                command = self.update_command
                print(command)
                subprocess.check_output(command,shell=True)
            finally:
                os.chdir( cwd )
        else:
            self.checkout()


class CVSSource( BaseSource ):
    @property
    def checkout_command( self ):
        assert self.project 
        assert self.root 
        assert self.dirname
        return 'cvs -d%s co -d%s %s'%(
            self.root, self.dirname, self.project, 
        )
    @property 
    def update_command( self ):
        return 'cvs up -C'
class SVNSource( BaseSource ):
    @property
    def checkout_command( self ):
        assert self.root 
        assert self.dirname
        return 'svn co %s %s'%(
            self.root, self.dirname,
        )
    @property 
    def update_command( self ):
        return 'svn up'

class BZRSource( BaseSource ):
    @property
    def checkout_command( self ):
        assert self.root 
        assert self.dirname
        return 'bzr checkout --lightweight %s %s'%(
            self.root, self.dirname,
        )
    @property 
    def update_command( self ):
        return 'bzr update'

class HgSource( BaseSource ):
    @property 
    def checkout_command( self ):
        assert self.root 
        assert self.dirname 
        return 'hg clone %s %s'%(
            self.root, self.dirname,
        )
    @property
    def update_command( self ):
        """Note: requires enabling the fetch extension (sigh)"""
        return 'hg pull && hg update'

class GITSource( BaseSource ):
    @property
    def checkout_command( self ):
        assert self.root 
        assert self.dirname
        return 'git clone %s %s'%(
            self.root, self.dirname,
        )
    @property 
    def update_command( self ):
        return 'git pull'


checkouts = [
    GITSource(
        'https://github.com/mcfletch/openglcontext.git',
        'OpenGLContext',
    ),
    GITSource(
        'https://github.com/mcfletch/pyopengl-demo.git',
        'PyOpenGL-Demo',
    ),
    # CVSSource(
    #     ':pserver:anonymous@glinter.cvs.sourceforge.net:/cvsroot/glinter',
    #     'Glinter',
    # ),
    # CVSSource(
    #     ':pserver:anonymous@pybzedit.cvs.sourceforge.net:/cvsroot/pybzedit',
    #     'pybzedit',
    # ),
    # CVSSource(
    #     ':pserver:anonymous@pyui.cvs.sourceforge.net:/cvsroot/pyui',
    #     'PyUIcvs',
    #     'pyui',
    # ),
    GITSource(
        'https://github.com/Ripsnorta/pyui2.git',
        'pyui2',
    ),
    # SVNSource(
    #     'https://svn.code.sf.net/p/pymmlib/code/trunk',
    #     'pymmlib',
    # ),
    GITSource(
        'https://github.com/masci/mmLib.git',
        dirname = 'mmlib',
    ),
#    SVNSource(
#        'http://visionegg.org/svn/trunk/visionegg',
#        dirname = 'visionegg',
#    ),
    GITSource(
        'git://github.com/visionegg/visionegg.git',
        dirname = 'visionegg',
    ),
    GITSource(
        'git://github.com/tito/pymt.git',
        dirname = 'pymt',
    ),
    GITSource(
        'git://github.com/rossant/galry.git',
        dirname = 'galry',
    ),
#    SVNSource(
#        'http://svn.gnome.org/svn/gnome-games/trunk/glchess',
#        dirname = 'glchess',
#    ),
    GITSource(
        'https://github.com/sparkslabs/kamaelia.git',
        dirname = 'kamaelia',
    ),
    GITSource(
        'https://github.com/philippTheCat/pyggel.git',
        dirname = 'pyggel',
    ),
    GITSource(
        'https://github.com/RyanHope/PyGL2D.git',
        dirname = 'pygl2d',
    ),
    BZRSource(
        'https://code.launchpad.net/~bebraw/scocca/devel',
        dirname = 'scocca',
    ),
    GITSource(
        'https://github.com/tartley/gltutpy.git',
        dirname = 'gltutpy',
    ),
    GITSource(
        'https://github.com/tartley/algorithmic-generation-of-opengl-geometry.git',
        dirname = 'agog',
    ),
    GITSource(
        'https://github.com/tartley/gloopy.git',
        dirname = 'gloopy',
    ),
    GITSource(
        'https://github.com/almarklein/visvis',
        dirname = 'visvis',
    ),
    HgSource(
        'https://bitbucket.org/rndblnch/opengl-programmable/',
        dirname = 'programmable',
    ),
    GITSource(
        'https://github.com/mmatl/pyrender.git',
        dirname='pyrender',
    ),
    # pymol # not pyopengl AFAICS
    # {LGPL} mirra # no online view of code AFAICS
    # soccerbots http://soccerbots.googlecode.com/svn/
    # enough http://enough.googlecode.com/svn/ trunk/
    # flyback http://flyback.googlecode.com/svn/ trunk/
    # threeDS
    # pyODE (examples)
    # Dice3DS (BSD) 
    # KeyJnote (GPL)
    # PyGauntlet (GPL) http://pygauntlet.googlecode.com/svn
    # LPhoto (GPL) lphoto_2.0.42-0.0.0.45.lindows0.1.tar.gz
    # http://crystaltowers.googlecode.com/svn/ trunk/
    ### beryl-mesa-0.1.4.tar.bz2
    ### Mesa source distribution mesa/glapi 
    
]

if __name__ == "__main__":
    if not os.path.exists(SAMPLE_DIRECTORY):
        os.makedirs(SAMPLE_DIRECTORY)
    os.chdir( '.samples' )
    for checkout in checkouts:
        print(('Project:', checkout.dirname))
        checkout.update()
    
