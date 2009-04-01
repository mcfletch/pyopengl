<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<head>
    <title>PyOpenGL ${version} Function Reference</title>
    <link rel="stylesheet" href="./manpage.css" type="text/css" />
</head>
<body>

<h1>PyOpenGL ${version}</h1>
<ul class="toc"><li py:for="package in ref.package_names()">
    <a href="#${package}">${package} Reference</a>
</li><li>
    <a href="http://pyopengl.sourceforge.net/documentation/pydoc/OpenGL.html">PyOpenGL Package PyDoc</a> -- includes Python-specific helper modules and the OpenGL extension modules.
</li>
</ul>

<div py:for="(package,sections) in ref.packages()" class="reference">
    <h2 class="package-title"><a name="${package}"/>${package} Reference</h2>
    <table><tbody><tr ><th py:if="package=='GL'">Deprecation</th><th align="right">Function</th><th>Purpose</th></tr>
    <tr py:for="name,section in sections" valign="top" class="${['forward-compatible','deprecated'][bool(section.deprecated)]}">
        <th py:if="package=='GL'"><span py:if="section.deprecated">(DEPRECATED)</span></th>
        <th align="right" class="section-name">
            <a href="${ref.url(section)}">${name}</a>
        </th>
        <td class="purpose">${section.purpose}</td>
    </tr>
    </tbody></table>
</div>

</body>
</html>

