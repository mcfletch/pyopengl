<!DOCTYPE html>
<?python
from genshi.input import ET
def ref_name( docbook ):
    """One section (glDrawTransformFeedbackStream) has a non-standard reference form"""
    if len(docbook):
        return docbook[0].text 
    else:
        return docbook.text 
need_math_render = []
?>
<html xmlns:py="http://genshi.edgewall.org/">
<ul class="menu" py:def="nav_table()">
    <li><a href="../../index.html">Home</a></li>
    <li><a href="../index.html">Docs</a></li>
    <li><a href="../installation.html">Install</a></li>
    <li><a href="./index.html#${section.package}">${section.package}</a></li>
</ul>
<div py:def="contents( docbook )" py:strip="">${docbook.text}<div py:for="x in docbook" py:strip="">${convert(x)}</div></div>
<div py:def="convert( docbook )" py:strip="">
    <?python
#print docbook, docbook[:]
approach = 'para'
if docbook.tag.startswith( '{http://www.w3.org/1998/Math/MathML}' ):
    need_math_render.append( True )
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
if approach == 'copy':
    copy = ET( docbook )
?>
    <div py:if="approach=='copy'" py:strip="">${copy}</div>
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
    <div py:if="approach=='expand'" py:strip=""><div py:for="x in docbook" py:strip="">${convert(x)}</div></div>
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
        <div py:strip="" py:for="sample in samples"><div py:replace="format_sample( sample )" /></div>
    </div>
</div>
<div py:def="format_sample( sample )" class="py-sample">
    <span class="sample-project">${sample.projectName}</span>
    <a href="${sample.url}" title="${sample.lineText}">${sample.deltaPath}</a> 
    <?python 
    sample_lines = ", ".join([str(x[0]) for x in sample.positions[:20]])
    ?>
    Lines: <span class="sample-lines">${sample_lines}<span py:if="len(sample.positions)&gt;20" py:strip="">...</span></span>
</div>
<head>
    <title>${section.title} : PyOpenGL ${version} ${section.package} Man Pages</title>
    <link rel="stylesheet" href="./manpage.css" type="text/css" />
    <link rel="stylesheet" href="./modern.css" type="text/css" />
</head>
<body>
<header>
    ${nav_table()}
    <h1>${section.title}</h1>
</header>
<main class="content">
    <section class="purpose">${ section.purpose }</section>
    <section class="signatures">
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
    </section>
    <section class="section" py:for="subsect in section.discussions" id="${subsect.get('id')}">
        ${ convert(subsect) }
    </section>
    <section class="see-also" py:if="section.see_also">
        <h2>See Also</h2>
        <span py:for="target in section.get_crossrefs( ref )" py:strip="">
            <a class="crossref" href="${ref.url(target)}">${target.name}</a>
        </span>
    </section>
    <section class="samples-section" py:if="section.samples">
        <h2>Sample Code References</h2>
        <p>The following code samples have been found which appear to reference the 
        functions described here.  Take care that the code may be old, broken or not 
        even use PyOpenGL.</p>
        ${format_samples( section.samples ) }
    </section>
</main>
<section class="copyright-notice">
    <h2>Copyright Notices</h2>
    <div py:if="section.package in ('GL','GLU')">
        This documentation is based on documentation licensed under the 
        <a href="http://oss.sgi.com/projects/FreeB/">SGI Free Software License B</a>.
    </div>
</section>
<section class="mathjax-note" py:if="need_math_render">
    <h2>MathML Rendering</h2>
    <div><a href="http://www.mathjax.org/">
    <img title="Powered by MathJax"
        src="http://www.mathjax.org/badge.gif"
        border="0" alt="Powered by MathJax" /></a></div>
    <script py:if="need_math_render" type="text/javascript"
       src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
</section>
<footer>
${nav_table()}
<div class="clear-both"></div>
</footer>
</body>
</html>
