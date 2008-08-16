<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<div py:def="signature( function )" class="signature">
	<a name="${function.name}"/>
	${function.name}(
		<span py:for="i,(typ,name) in enumerate(function.params)" class="parameter"
		>${typ}( 
			<span class="param-name">${name}</span>
		)<span py:strip="" py:if="i &lt; len(function.params)-1">, </span></span>
		)-&gt; ${function.return_value}
</div>
<head>
    <title>PyOpenGL ${version} : ${section.title} </title>
</head>
<body>

<a py:if="section.previous" href="${ref.url(section.previous)}">Previous: ${section.previous.title}</a>
<a href="./index.html">Table of Contents</a>
<a py:if="section.next" href="${ref.url(section.next)}">Next: ${section.next.title}</a>

<h1>${section.title}</h1>
<h2 class="purpose">${ section.purpose }</h2>

<div class="c-specifications">
	<h2>C Specification</h2>
	<div py:for="(name,function) in sorted( section.refnames.items())">
		${signature( function )}
	</div>
</div>
<div class="see-also" py:if="section.see_also">
	<h2>See Also</h2>
	<span py:for="target in section.get_crossrefs( ref )">
		<a href="${ref.url(target)}">${target.name}</a>
	</span>
</div>

</body>
</html>

