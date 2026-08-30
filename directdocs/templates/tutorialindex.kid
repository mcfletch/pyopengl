<!DOCTYPE html>
<html xmlns:py="http://genshi.edgewall.org/">
  <head>
    <meta content="text/html; charset=utf-8" http-equiv="content-type" />
    <title>OpenGLContext Python Tutorials</title>
    <link rel="stylesheet" href="../style/modern.css" type="text/css" />
    <link rel="stylesheet" href="../style/tutorial.css" type="text/css" />
  </head>
<body>
    <header>
      <nav>
      <ul class="menu">
        <li><a href="/context/index.html">OpenGLContext</a></li>
        <li><a href="/context/documentation/index.html">Docs</a></li>
      </ul>
      </nav>
    <h1>OpenGLContext Python Tutorials</h1>
    </header>
<div py:def="path_children(path)" py:for="tutorial in path.children" class="tutorial">
	<a href="${tutorial.relative_link}" class="tutorial-link">${ tutorial.title }</a>
</div>

<section class="path" py:for="path in paths">
	<h2 class="path-name">${path.text}</h2>
	<div class="path-body">
		<div class="introduction" py:if="path.description">${path.description}</div>
		${path_children( path )}
	</div>
</section>
<footer>
      <nav>
      <ul class="menu">
        <li><a href="/context/index.html">OpenGLContext</a></li>
        <li><a href="/context/documentation/index.html">Docs</a></li>
      </ul>
      </nav>
    <div class="metadata">This document was generated from OpenGLContext ${version} on ${date}</div>
    <div class="clear-both"></div>
</footer>
</body>
</html>

