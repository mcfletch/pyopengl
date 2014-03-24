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

<section class="path">
    <?python 
    path = paths[0]
    ?>
    <h2 class="path-name">Introduction to Shaders (Lighting)</h2>
    <div class="path-body">
        <div class="introduction">This is a low-level introductory tutorial path.  It is intended for those 
        who have either never done 3D graphics with OpenGL, or who have only done "legacy"
        OpenGL rendering (i.e. you learned OpenGL before about 2007).  It walks through the development 
        of low-level code to perform Blinn-Phong rendering of DirectionalLights, PointLights and SpotLights
        as well as the basics of geometric rendering (with Vertex Buffer Objects).
        </div>
        ${path_children( path )}
    </div>
</section>

<section class="path">
	<?python 
	path = paths[1]
	?>
	<h2 class="path-name">${path.text}</h2>
	<div class="path-body">
		<div class="introduction">This is a high-level introductory tutorial path.  It is intended to 
		introduce the OpenGLContext/VRML97 scenegraph engine.  It demonstrates more involved 
		rendering tasks, but with far less detail than the Introduction to Shaders tutorial.  It does not 
		attempt to describe how the effects are achieved, just how to achieve them.
		</div>
		${path_children( path )}
	</div>
</section>
<section class="path">
	<?python 
	path = paths[2]
	?>
	<h2 class="path-name">${path.text}</h2>
	<div class="path-body">
		<div class="introduction">These tutorials describe how to setup modern shadow-map-based shadow-casting.
        These are fairly advanced tutorials which assume you are comfortable with OpenGL.
		</div>
		${path_children( path )}
	</div>
</section>
<section class="path">
	<?python 
	path = paths[3]
	?>
	<h2 class="path-name">${path.text}</h2>
	<div class="path-body">
		<div class="introduction">These tutorials are translations of the famous "NeHe" series of tutorials.
		These are low-level introductory tutorials which generally use the legacy OpenGL API.  The linked 
		original tutorials are very gentle and thorough.
		</div>
		${path_children( path )}
	</div>
</section>
<section class="path" py:for="path in paths[4:]">
	<h2 class="path-name">${path.text}</h2>
	<div class="path-body">
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

