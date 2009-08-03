<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<div py:def="path_children(path)" py:for="tutorial in path.children" class="tutorial">
	<a href="${tutorial.relative_link}" class="tutorial-link">${ tutorial.title }</a>
</div>
<table width="100%" py:def="navtable()" class="navtable"><thead>
	<tr>
		<td width="8em;"/><th align="center"><a href="../">OpenGLContext Documentation</a></th><td width="8em;"/>
	</tr>
	<tr>
	<td><a py:if="prev" href="${prev.relative_link}">Previous</a><a py:if="not prev" href="index.xhtml">Index</a></td>
	<td align="center">Paths</td>
	<td align="right"><a py:if="next" href="${next.relative_link}">Next</a><a py:if="not next" href="index.xhtml">Index</a></td>
	</tr>
</thead></table>
<head>
    <title>OpenGLContext Python Tutorials</title>
    <link rel="stylesheet" href="./tutorial.css" type="text/css" />
</head>
<body>
${navtable()}
<div py:for="path in paths" class="path">
	<h1 class="path-name">${path.text}</h1>
	${path_children( path )}
</div>
<div class="metadata">This document was generated from OpenGLContext ${version} on ${date}</div>
<!-- by bzr branch http://bazaar.launchpad.net/%7Emcfletch/pyopengl/directdocs/ -->
${navtable()}
</body>
</html>

