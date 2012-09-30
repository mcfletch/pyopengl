#! /bin/bash

rsync -avP -e ssh ./* mcfletch,pyopengl@web.sourceforge.net:htdocs/
