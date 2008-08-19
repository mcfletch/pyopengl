<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<div py:def="contents( docbook )" py:strip="">${docbook.text}${[convert(x) for x in docbook]}</div>
<div py:def="convert( docbook )" py:strip="">
	<?python
approach = 'para'
basetag = docbook.tag.split( "}" )[1]
approach_set = {
	'citerefentry':'crossref',
	'constant':'span',
	'parameter':'span',
	'informaltable': 'table',
	'emphasis':'span',
	'colspec':'',
	'function':'function',
	'inlineequation':'expand',
	'refsect1':'expand',
	'math':'copy',
	'title':'heading',
	'variablelist':'dl',
	'term':'dt',
	'listitem':'dd',
}
approach = approach_set.get( basetag, 'para' )
?>
	<div py:if="approach=='para'" class="${basetag}">${contents(docbook)}</div>
	<span py:if="approach=='span'" class="${basetag}">${contents(docbook)}</span>
	<a class="crossref" py:if="approach=='crossref'" py:strip="not ref.get_crossref(docbook[0].text,docbook[1].text,section=section)"
		href="${ref.url(ref.get_crossref(docbook[0].text,docbook[1].text,section=section))}"
	>${docbook[0].text}</a>
	<a class="function" py:if="approach=='function'" py:strip="not ref.get_crossref(docbook.text,section=section)"
		href="${ref.url(ref.get_crossref(docbook.text,section=section))}"
	>${docbook.text}</a>
	<table py:if="approach=='table'" class="${basetag}"><tbody>
		<div py:for="component in docbook[0]" py:strip="">
			<div py:if="component.tag.endswith( '}thead')" py:strip="">
				<tr py:for="row in component" valign="top">
					<th py:for="entry in row">${contents(entry)}</th>
				</tr>
			</div>

			<div py:if="component.tag.endswith( '}tbody')" py:strip="">
				<tr py:for="row in component" valign="top">
					<td py:for="entry in row">${contents(entry)}</td>
				</tr>
			</div>
		</div>
	</tbody></table>
	<div py:if="approach=='expand'" py:strip="">${[convert(x) for x in docbook]}</div>
	<div py:if="approach=='copy'" py:strip="">${docbook}</div>
	<h2 py:if="approach=='heading'" class="${basetag}">${contents(docbook)}</h2>
	<dd py:if="approach=='dd'" class="${basetag}">${contents(docbook)}</dd>
	<dl py:if="approach=='dl'" class="${basetag}">${contents(docbook)}</dl>
	<dt py:if="approach=='dt'" class="${basetag}">${contents(docbook)}</dt>
	${(docbook.tail or '').strip()}
</div>
<div py:def="pysignature( function,name=None )" class="py-signature">
	<?python
	if name is None:
		name = function.__name__
	if hasattr( function, 'pyConverterNames' ):
		argNames = function.pyConverterNames
	else:
		argNames = getattr( function, 'argNames', ()) or ()
	?>
	${name}( 
		
		<span py:for="(i,name) in enumerate(argNames)" class="parameter"
		>
			${name},
		</span>
	) <span py:if="function.restype">-&gt; ${function.restype}</span>
</div>
<div py:def="csignature( function )" class="c-signature">
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
	<link rel="stylesheet" href="./manpage.css" type="text/css" />
</head>
<body>

<table width="100%"><tbody><tr><td align="left">
<a id="nav-previous" py:if="section.previous" href="${ref.url(section.previous)}">Previous: ${section.previous.title}</a></td>
<td align="center">
<a id="nav-up" href="./index.html">Table of Contents</a>
</td>
<td align="right">
<a id="nav-next" py:if="section.next" href="${ref.url(section.next)}">Next: ${section.next.title}</a>
</td>
</tr></tbody></table>

<h1>${section.title}</h1>
<div class="purpose">${ section.purpose }</div>

<div class="signatures">
	<h2>Signature</h2>
	<div py:for="(name,function) in sorted( section.refnames.items())" class="signature">
		${csignature( function )}
		<div py:for="(name,pyfunc) in sorted(function.python.items())" py:strip="">
			<div py:if="hasattr(pyfunc,'restype')" py:replace="pysignature(pyfunc,name)"/>
		</div>
	</div>
	<div py:if="section.varrefs" py:strip="">
		<h2>Parameters</h2>
		<table><tbody>
			<tr><th align="right">Variables</th><th>Description</th></tr>
			<tr py:for="varref in section.varrefs" class="varref" valign="top">
				<th align="right">${", ".join(varref.names)}</th>
				<td>${convert(varref.description[0])}</td>
			</tr>
		</tbody></table>
	</div>
</div>
<div class="section" py:for="subsect in section.discussions" id="${subsect.get('id')}">
	${convert(subsect)}
</div>
<div class="see-also" py:if="section.see_also">
	<h2>See Also</h2>
	<span py:for="target in section.get_crossrefs( ref )" py:strip="">
		<a class="crossref" href="${ref.url(target)}">${target.name}</a>
	</span>
</div>

</body>
</html>

