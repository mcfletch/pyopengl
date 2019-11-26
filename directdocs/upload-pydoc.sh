#! /bin/bash

rsync -avP -e ssh pydoc/* mcfletch,pyopengl@web.sourceforge.net:htdocs/documentation/pydoc/
