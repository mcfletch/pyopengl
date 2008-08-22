#! /usr/bin/env python
"""Incredibly stupid little script to tar up the content and upload it"""
from directdocs import model
OUTPUT_DIRECTORY = 'manual-%s'%(model.MAJOR_VERSION,)

def main():
	tarfile = 'manual-%s.tar'%__version__
	gzfile = tarfile + '.gz'
	output = OUTPUT_DIRECTORY
	os.system(
		'tar -cvf %(tarfile)s %(output)s'%locals()
	)
	os.system(
		'gzip %(tarfile)s'%locals()
	)
	target = 'mcfletch@shell.sf.net:/home/groups/p/py/pyopengl/htdocs/documentation'
	os.system( 
		'scp %(gzfile)s %(target)s'%locals()
	)
	print '%(gzfile)s copied to %(target)s'%locals()
if __name__ == "__main__":
	main()
