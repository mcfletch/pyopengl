<?python
def ref_name( docbook ):
    """One section (glDrawTransformFeedbackStream) has a non-standard reference form"""
    if len(docbook):
        return docbook[0].text 
    else:
        return docbook.text 
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<table py:def="nav_table()" width="100%"><tbody><tr><td align="left">
<a id="nav-previous" py:if="section.previous" href="${ref.url(section.previous)}">Previous: ${section.previous.title}</a></td>
<td align="center">
<a id="nav-up" href="./index.xhtml#${section.package}">Table of Contents (${section.package})</a>
</td>
<td align="right">
<a id="nav-next" py:if="section.next" href="${ref.url(section.next)}">Next: ${section.next.title}</a>
</td>
</tr></tbody></table>

<div py:def="contents( docbook )" py:strip="">${docbook.text}${[convert(x) for x in docbook]}</div>
<div py:def="convert( docbook )" py:strip="">
    <?python
#print docbook, docbook[:]
approach = 'para'
basetag = docbook.tag.split( "}" )[1]
approach_set = {
    'citerefentry':'crossref',
    'constant':'span',
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
    'ulink':'extref',
    'parameter': 'paramref',
}
approach = approach_set.get( basetag, 'para' )

?>
    <div py:if="approach=='para'" class="${basetag}">${contents(docbook)}</div>
    <span py:if="approach=='span'" class="${basetag}">${contents(docbook)}</span>
    <a class="crossref" py:if="approach=='crossref'" py:strip="not ref.get_crossref(ref_name(docbook),section=section)"
        href="${ref.url(ref.get_crossref(ref_name(docbook),section=section))}"
    >${ref_name(docbook)}</a>
    <a class="function" py:if="approach=='function'" py:strip="not ref.get_crossref(ref_name(docbook),section=section)"
        href="${ref.url(ref.get_crossref(ref_name(docbook),section=section))}"
    >${ref_name(docbook)}</a>
    <a class="extref" py:if="approach=='extref'"
        href="${docbook.get('url')}"
    >${docbook.text}</a>
    <a class="parameter" py:if="approach=='paramref'"
        href="#param-${docbook.text}"
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
    <a name="py-${function.name}"/>
    <span class="py-function">${function.name}</span>( ${paramlist(function)} )
    <span py:if="function.return_value">-&gt; ${function.return_value}</span>
    <pre class="pydoc" py:if="function.docstring" py:content="function.docstring"/>
</div>
<span py:def="paramlist( function )" class="parameter-list">
    <span py:for="i,param in enumerate(function.parameters)" class="param-def">
        <span py:if="param.varargs" py:strip="">*</span>
        <span py:if="param.varnamed" py:strip="">**</span>
        <span py:if="param.data_type" py:strip="">${param.data_type}( </span>
            <a href="#param-${param.name}" class="parameter">${param.name}</a>
        <span py:if="param.data_type" py:strip="">)</span>
        <span py:if="param.has_default" py:strip=""> = ${repr(param.default)}</span>
        <span py:strip="" py:if="i &lt; len(function.parameters)-1">, </span>
    </span>
</span>
<div py:def="csignature( function )" class="c-signature">
    <a name="c-${function.name}"/>
    <span class="c-function">${function.name}</span>(${paramlist(function)})-&gt; ${function.return_value}
</div>
<div py:def="format_samples( sample_set )" class="py-samples">
    <div py:for="(key,samples) in sample_set" py:strip="">
        <div class="sample-key">${key}</div>
        <div py:strip="" py:for="sample in samples" py:replace="format_sample( sample )" />
    </div>
</div>
<div py:def="format_sample( sample )" class="py-sample">
    <span class="sample-project">${sample.projectName}</span>
    <a href="${sample.url}" title="${sample.lineText}">${sample.deltaPath}</a> 
    Lines: <span class="sample-lines">${", ".join([str(x[0]) for x in sample.positions[:20]])}<span py:if="len(sample.positions)&gt;20" py:strip="">...</span></span>
</div>
<head>
    <title>${section.title} : PyOpenGL ${version} ${section.package} Man Pages</title>
    <link rel="stylesheet" href="./manpage.css" type="text/css" />
</head>
<body>
${nav_table()}
<h1>${section.title}</h1>
<div class="content">
    <div class="purpose">${ section.purpose }</div>
    <div class="deprecation-warning" py:if="section.deprecated">
        <h2>Deprecation Notice</h2>
        <div class="deprecation-description">
            Note that this function has been marked deprecated in the OpenGL 3.0 specification.
            You should not be using this function in new code, though it will likely be supported
	    by most implementations via the GL_ARB_compatibility extension.
            For more information on OpenGL 3.x deprecations, see the 
	    <a href="http://pyopengl.sourceforge.net/documentation/deprecations.html">deprecations page</a>.
        </div>
    </div>
    <div class="signatures">
        <h2>Signature</h2>
        <div py:for="(name,function) in sorted( section.functions.items())" class="signature">
            ${csignature( function )}
            <div py:for="(name,pyfunc) in sorted(function.python.items())" py:strip="">
                <div py:replace="pysignature(pyfunc,name)"/>
            </div>
        </div>
        <div py:if="section.varrefs" py:strip="">
            <h2>Parameters</h2>
            <table><tbody>
                <tr><th align="right">Variables</th><th>Description</th></tr>
                <tr py:for="varref in section.varrefs" class="varref" valign="top">
                    <th align="right">
                        <a name="param-${name}" py:for="name in varref.names"/>
                        ${", ".join(varref.names)}
                    </th>
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
    <div class="samples-section" py:if="section.samples">
        <h2>Sample Code References</h2>
        <p>The following code samples have been found which appear to reference the 
        functions described here.  Take care that the code may be old, broken or not 
        even use PyOpenGL.</p>
        ${format_samples( section.samples ) }
    </div>
</div>
<div class="copyright-notice">
    <h2>Copyright Notices</h2>
    <div py:if="section.package in ('GL','GLU')">
        This documentation is based on documentation licensed under the 
        <a href="http://oss.sgi.com/projects/FreeB/">SGI Free Software License B</a>.
    </div>
</div>
${nav_table()}
<script type="text/javascript"
   src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
</body>
</html>
