;REM Batch file to compile GLE as a DLL using Toolkit compiler
;REM Copy to the GLE source directory, i.e.:
;REM 
;REM 	cp buildgledll.bat \csrc\gle-3.1.0\src\
;REM 	vc7.bat
;REM 	buildgledll.bat
;REM 
;REM  Now put the DLL somewhere useful, such as \winnt\system32
;REM 
;REM 	cp gle32.dll \WINNT\system32
;REM 
;REM  Though realistically, we want to package it for regular users

rm *.obj
rm *.dll
cp ..\ms-visual-c\config.h ..\
cp ..\ms-visual-c\config.h .\
cl -c /D"WIN32" /D "_WINDLL" /Gd /MD *.c
link /EXPORT:gleExtrusion /EXPORT:gleGetNumSides /EXPORT:gleSetJoinStyle /EXPORT:glePolyCylinder /EXPORT:gleSpiral /EXPORT:gleSetNumSides /EXPORT:uview_direction /EXPORT:gleScrew /EXPORT:gleHelicoid /EXPORT:gleToroid /EXPORT:urot_omega /EXPORT:rot_about_axis /EXPORT:gleExtrusion /EXPORT:gleTextureMode /EXPORT:urot_prince /EXPORT:rot_prince /EXPORT:gleSuperExtrusion /EXPORT:urot_about_axis /EXPORT:rot_omega /EXPORT:gleLathe /EXPORT:gleGetJoinStyle /EXPORT:glePolyCone /EXPORT:rot_axis /EXPORT:uviewpoint /EXPORT:gleTwistExtrusion /EXPORT:urot_axis /LIBPATH:"C:\Program Files\Microsoft Platform SDK\Lib" /DLL /OUT:opengle32.dll opengl32.lib glu32.lib *.obj
