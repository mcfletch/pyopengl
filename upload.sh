#! /bin/bash

rsync -avP -e ssh manual-3.0/* mcfletch,pyopengl@web.sourceforge.net:htdocs/documentation/manual-3.0/
