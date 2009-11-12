<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<div py:def="path_children(path)" py:for="tutorial in path.children" class="tutorial">
	<a href="${tutorial.relative_link}" class="tutorial-link">${ tutorial.title }</a>
</div>
<table width="100%" py:def="navtable(bottom=False)" class="navtable"><thead>
	<tr>
		<td width="8em;"/><th align="center"><a href="../">OpenGLContext Documentation</a></th><td width="8em;"/>
	</tr>
	<tr>
	<td><a py:if="prev" href="${prev.relative_link}">Previous</a><a py:if="not prev" href="index.xhtml">Index</a></td>
	<td align="center">Tutorial Paths</td>
	<td align="right"><a py:if="next" href="${next.relative_link}">Next</a><a py:if="not next" href="index.xhtml">Index</a></td>
	</tr>
	<tr class="meta-links" py:if="bottom">
		<td colspan="3">
		<a href="../documentation.html"><img src="../images/doc_icon.gif" title="" alt="Documentation" style="border: 0px solid ; width: 32px; height: 32px;"/></a> 
		<a href="http://pyopengl.sourceforge.net/context/"><img src="../images/context_logo_icon.png" title="" alt="OpenGLContext" style="border: 0px solid ; width: 32px; height: 32px;"/></a> 
		<a href="http://pyopengl.sourceforge.net/"><img title="" alt="PyOpenGL" src="../images/pyopengl_icon.jpg" style="border: 0px solid ; width: 32px; height: 32px;"/></a>
		<a href="http://sourceforge.net"><img src="http://sourceforge.net/sflogo.php?group_id=5988&amp;type=1" style="border: 0px solid ; width: 88px; height: 31px;" alt="SourceForge" title=""/></a>
		</td>
	</tr>
</thead></table>
<head>
    <title>OpenGLContext Python Tutorials</title>
    <link rel="stylesheet" href="./tutorial.css" type="text/css" />
</head>
<body>
${navtable()}
<div class="path">
	<?python 
	path = paths[0]
	?>
	<h1 class="path-name">Introduction to Shaders (Lighting)</h1>
	<div class="path-body">
		<div class="introduction">This is a low-level introductory tutorial path.  It is intended for those 
		who have either never done 3D graphics with OpenGL, or who have only done "legacy"
		OpenGL rendering (i.e. you learned OpenGL before about 2007).  It walks through the development 
		of low-level code to perform Blinn-Phong rendering of DirectionalLights, PointLights and SpotLights
		as well as the basics of geometric rendering (with Vertex Buffer Objects).
		</div>
		${path_children( path )}
	</div>
</div>
<div class="path">
	<?python 
	path = paths[1]
	?>
	<h1 class="path-name">${path.text}</h1>
	<div class="path-body">
		<div class="introduction">This is a high-level introductory tutorial path.  It is intended to 
		introduce the OpenGLContext/VRML97 scenegraph engine.  It demonstrates more involved 
		rendering tasks, but with far less detail than the Introduction to Shaders tutorial.  It does not 
		attempt to describe how the effects are achieved, just how to achieve them.
		</div>
		${path_children( path )}
	</div>
</div>
<div class="path">
	<?python 
	path = paths[2]
	?>
	<h1 class="path-name">${path.text}</h1>
	<div class="path-body">
		<div class="introduction">These tutorials are translations of the famous "NeHe" series of tutorials.
		These are low-level introductory tutorials which generally use the legacy OpenGL API.  The linked 
		original tutorials are very gentle and thorough.
		</div>
		${path_children( path )}
	</div>
</div>
<div py:for="path in paths[3:]" class="path">
	<h1 class="path-name">${path.text}</h1>
	<div class="path-body">
		${path_children( path )}
	</div>
</div>
<div class="metadata">This document was generated from OpenGLContext ${version} on ${date}</div>
<!-- by bzr branch http://bazaar.launchpad.net/%7Emcfletch/pyopengl/directdocs/ -->
${navtable(bottom=True)}
</body>
</html>

