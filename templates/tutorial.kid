<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<table width="100%" py:def="navtable(bottom=False)" class="navtable"><thead>
	<tr>
		<td width="8em;"/><th align="center"><a href="index.xhtml">OpenGLContext Python tutorials</a></th><td width="8em;"/>
	</tr>
	<tr>
	<td><a py:if="prev" href="${prev.relative_link}">Previous</a><a py:if="not prev" href="index.xhtml">Index</a></td>
	<td align="center">${path.text}: ${tutorial.title}</td>
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

<div py:def="children(node)" py:if="node.children" py:strip=""><div py:for="child in node.children" py:strip="">${convert(child)}</div></div>
<div py:def="node_content(node)" py:strip="">${node.text}${children(node)}</div>
<div py:def="convert( node )" py:strip="">
	<h1 py:if="node.html_tag == 'h1'" class="${node.html_class}">${node_content(node)}</h1>
	<div py:if="node.html_tag == 'div'" class="${node.html_class}">${node_content(node)}</div>
	<ul py:if="node.html_tag == 'ul'" class="${node.html_class}">${node_content(node)}</ul>
	<li py:if="node.html_tag == 'li'" class="${node.html_class}">${node_content(node)}</li>
	<a py:if="node.html_tag == 'a'" class="${node.html_class}" href="${node.url}">${node_content(node)}</a>
	<img py:if="node.html_tag == 'img'" class="${node.html_class} wiki" src="${node.url}" alt="${node.text}" />
	${node.tail}
</div>
<head>
    <title>${path.text}: ${tutorial.title}</title>
    <link rel="stylesheet" href="./tutorial.css" type="text/css" />
</head>
<body>
${navtable()}
${children(tutorial)}
${navtable(bottom=True)}
</body>
</html>

