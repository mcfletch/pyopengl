"""Provides the common meta-data for the various setup scripts"""
import os
metadata = dict(
    version = [
        (line.split('=')[1]).strip().strip('"').strip("'")
        for line in open(os.path.join('OpenGL','version.py'))
        if line.startswith( '__version__' )
    ][0],
    author = 'Mike C. Fletcher',
    author_email = 'mcfletch@vrplumber.com',
    url = 'http://pyopengl.sourceforge.net',
    license = 'BSD',
    download_url = "http://sourceforge.net/projects/pyopengl/files/PyOpenGL/",
    keywords = 'Graphics,3D,OpenGL,GLU,GLUT,GLE,GLX,EXT,ARB,Mesa,ctypes',
    classifiers = [
        """License :: OSI Approved :: BSD License""",
        """Programming Language :: Python""",
        """Topic :: Multimedia :: Graphics :: 3D Rendering""",
        """Topic :: Software Development :: Libraries :: Python Modules""",
        """Intended Audience :: Developers""",
    ],
)