<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<head>
    <title>PyOpenGL ${version} Function Reference</title>
</head>
<body>

<h1>PyOpenGL ${version}</h1>
<table><tbody><tr ><th align="right">Function</th><th>Purpose</th></tr>
<tr py:for="name,function in sorted(ref.functions.items())" valign="top">
	<th align="right" class="function_name">
		<a href="${ref.url(function)}">${name}</a>
	</th>
	<td class="purpose">${function.section.purpose}</td>
</tr>
</tbody></table>

</body>
</html>

