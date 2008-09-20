# -*- mode: python -*-
a = Analysis([
	os.path.join(HOMEPATH,'support\\_mountzlib.py'),
	os.path.join(HOMEPATH,'support\\useUnicode.py'),
	'pkgresourcetest.py'],
	pathex=['P:\\OpenGL-ctypes\\src\\pyinstaller-sample'],
)
pyz = PYZ(a.pure - ['OpenGL'])
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\pyi.win32\pkgresourcetest', 'pkgresourcetest.exe'),
          debug=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT( exe,
               a.binaries, 
               a.zipfiles, #+ [('PyOpenGL-3.0.0b2-py2.5.egg','p:\\OpenGL-ctypes\\dist\\PyOpenGL-3.0.0b2-py2.5.egg','DATA'),],
               strip=False,
               upx=False,
               name=os.path.join('dist', 'pkgresourcetest'))
