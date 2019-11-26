<!DOCTYPE html>
<html
    xmlns:py="http://genshi.edgewall.org/"
    xmlns:xi="http://www.w3.org/2001/XInclude">
<xi:include href="master.html" />

<ul class="menu" py:def="nav_table(context)">
    <li><a href="/context/index.html">OpenGLContext</a></li>
    <li><a href="/context/documentation/index.html">Docs</a></li>
    <li><a href="/context/documentation/tutorial/index.html">Tutorials</a></li>
    <li><a py:if="prev" href="${prev.relative_link}">Previous</a><a py:if="not prev" href="index.html">Index</a></li>
    <li><a py:if="next" href="${next.relative_link}">Next</a><a py:if="not next" href="index.html">Index</a></li>
</ul>
<head>
    <title>${path.text}: ${tutorial.title}</title>
    <link rel="stylesheet" href="../style/modern.css" type="text/css" />
    <link rel="stylesheet" href="../style/tutorial.css" type="text/css" />
</head>
<body class="openglcontext-tutorial">
    <header>
    ${nav_table(tutorial)}
    <h1>${path.text}: ${tutorial.title}</h1>
    </header>
    <section>
    ${children(tutorial)}
    </section>
<footer>
    ${nav_table(tutorial)}
<div class="source-reference">This code-walkthrough tutorial is generated from the ${tutorial.filename} script in the 
OpenGLContext source distribution.</div>
      <div class="clear-both"><br></br></div>
</footer>

</body>
</html>

