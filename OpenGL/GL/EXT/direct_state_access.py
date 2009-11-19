'''OpenGL extension EXT.direct_state_access

This module customises the behaviour of the 
OpenGL.raw.GL.EXT.direct_state_access to provide a more 
Python-friendly API

Overview (from the spec)
	
	This extension introduces a set of new "direct state access"
	commands (meaning no selector is involved) to access (update and
	query) OpenGL state that previously depended on the OpenGL state
	selectors for access.  These new commands supplement the existing
	selector-based OpenGL commands to access the same state.
	
	The intent of this extension is to make it more efficient for
	libraries to avoid disturbing selector and latched state.  The
	extension also allows more efficient command usage by eliminating
	the need for selector update commands.
	
	Two derivative advantages of this extension are 1) display lists
	can be executed using these commands that avoid disturbing selectors
	that subsequent commands may depend on, and 2) drivers implemented
	with a dual-thread partitioning with OpenGL command buffering from
	an application thread and then OpenGL command dispatching in a
	concurrent driver thread can avoid thread synchronization created by
	selector saving, setting, command execution, and selector restoration.
	
	This extension does not itself add any new OpenGL state.
	
	We call a state variable in OpenGL an "OpenGL state selector" or
	simply a "selector" if OpenGL commands depend on the state variable
	to determine what state to query or update.  The matrix mode and
	active texture are both selectors.  Object bindings for buffers,
	programs, textures, and framebuffer objects are also selectors.
	
	We call OpenGL state "latched" if the state is set by one OpenGL
	command but then that state is saved by a subsequent command or the
	state determines how client memory or buffer object memory is accessed
	by a subsequent command.  The array and element array buffer bindings
	are latched by vertex array specification commands to determine
	which buffer a given vertex array uses.  Vertex array state and pixel
	pack/unpack state decides how client memory or buffer object memory is
	accessed by subsequent vertex pulling or image specification commands.
	
	The existence of selectors and latched state in the OpenGL API
	reduces the number of parameters to various sets of OpenGL commands
	but complicates the access to state for layered libraries which seek
	to access state without disturbing other state, namely the state of
	state selectors and latched state.  In many cases, selectors and
	latched state were introduced by extensions as OpenGL evolved to
	minimize the disruption to the OpenGL API when new functionality,
	particularly the pluralization of existing functionality as when
	texture objects and later multiple texture units, was introduced.
	
	The OpenGL API involves several selectors (listed in historical
	order of introduction):
	
	  o  The matrix mode.
	
	  o  The current bound texture for each supported texture target.
	
	  o  The active texture.
	
	  o  The active client texture.
	
	  o  The current bound program for each supported program target.
	
	  o  The current bound buffer for each supported buffer target.
	
	  o  The current GLSL program.
	
	  o  The current framebuffer object.
	
	The new selector-free update commands can be compiled into display
	lists.
	
	The OpenGL API has latched state for vertex array buffer objects
	and pixel store state.  When an application issues a GL command to
	unpack or pack pixels (for example, glTexImage2D or glReadPixels
	respectively), the current unpack and pack pixel store state
	determines how the pixels are unpacked from/packed to client memory
	or pixel buffer objects.  For example, consider:
	
	  glPixelStorei(GL_UNPACK_SWAP_BYTES, GL_TRUE);
	  glPixelStorei(GL_UNPACK_ROW_LENGTH, 640);
	  glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 47);
	  glDrawPixels(100, 100, GL_RGB, GL_FLOAT, pixels);
	
	The unpack swap bytes and row length state set by the preceding
	glPixelStorei commands (as well as the 6 other unpack pixel store
	state variables) control how data is read (unpacked) from buffer of
	data pointed to by pixels.  The glBindBuffer command also specifies
	an unpack buffer object (47) so the pixel pointer is actually treated
	as a byte offset into buffer object 47.
	
	When an application issues a command to configure a vertex array,
	the current array buffer state is latched as the binding for the
	particular vertex array being specified.  For example, consider:
	
	  glBindBuffer(GL_ARRAY_BUFFER, 23);
	  glVertexPointer(3, GL_FLOAT, 12, pointer);
	
	The glBindBuffer command updates the array buffering binding
	(GL_ARRAY_BUFFER_BINDING) to the buffer object named 23.  The
	subsequent glVertexPointer command specifies explicit parameters
	for the size, type, stride, and pointer to access the position
	vertex array BUT ALSO latches the current array buffer binding for
	the vertex array buffer binding (GL_VERTEX_ARRAY_BUFFER_BINDING).
	Effectively the current array buffer binding buffer object becomes
	an implicit fifth parameter to glVertexPointer and this applies to
	all the gl*Pointer vertex array specification commands.
	
	Selectors and latched state create problems for layered libraries
	using OpenGL because selectors require the selector state to be
	modified to update some other state and latched state means implicit
	state can affect the operation of commands specifying, packing, or
	unpacking data through pointers/offsets.  For layered libraries,
	a state update performed by the library may attempt to save the
	selector state, set the selector, update/query some state the
	selector controls, and then restore the selector to its saved state.
	Layered libraries can skip the selector save/restore but this risks
	introducing uncertainty about the state of a selector after calling
	layered library routines.  Such selector side-effects are difficult
	to document and lead to compatibility issues as the layered library
	evolves or its usage varies.  For latched state, layered libraries
	may find commands such as glDrawPixels do not work as expected
	because latched pixel store state is not what the library expects.
	Querying or pushing the latched state, setting the latched state
	explicitly, performing the operation involving latched state, and
	then restoring or popping the latched state avoids entanglements
	with latched state but at considerable cost.
	
	EXAMPLE USAGE OF THIS EXTENSION'S FUNCTIONALITY
	
	Consider the following routine to set the modelview matrix involving
	the matrix mode selector:
	
	  void setModelviewMatrix(const GLfloat matrix[16])
	  {
	    GLenum savedMatrixMode;
	
	    glGetIntegerv(GL_MATRIX_MODE, &savedMatrixMode);
	    glMatrixMode(GL_MODELVIEW);
	    glLoadMatrixf(matrix);
	    glMatrixMode(savedMatrixMode);
	  }
	
	Notice that four OpenGL commands are required to update the current
	modelview matrix without disturbing the matrix mode selector.
	
	OpenGL query commands can also substantially reduce the performance
	of modern OpenGL implementations which may off-load OpenGL state
	processing to another CPU core/thread or to the GPU itself.
	
	An alternative to querying the selector is to use the
	glPushAttrib/glPopAttrib commands.  However this approach typically
	involves pushing far more state than simply the one or two selectors
	that need to be saved and restored.  Because so much state is
	associated with a given push/pop attribute bit, the glPushAttrib
	and glPopAttrib commands are considerably more costly than the
	save/restore approach.  Additionally glPushAttrib risks overflowing
	the attribute stack.
	
	The reliability and performance of layered libraries and applications
	can be improved by adding to the OpenGL API a new set of commands
	to access directly OpenGL state that otherwise involves selectors
	to access.
	
	The above example can be reimplemented more efficiently and without
	selector side-effects:
	
	  void setModelviewMatrix(const GLfloat matrix[16])
	  {
	    glMatrixLoadfEXT(GL_MODELVIEW, matrix);
	  }
	
	Consider a layered library seeking to load a texture:
	
	  void loadTexture(GLint texobj, GLint width, GLint height,
	                   void *data)
	  {
	    glBindTexture(GL_TEXTURE_2D, texobj);
	    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8,
	                 width, height, GL_RGB, GL_FLOAT, data);
	  }
	
	The library expects the data to be packed into the buffer pointed
	to by data.  But what if the current pixel unpack buffer binding
	is not zero so the current pixel unpack buffer, rather than client
	memory, will be read?  Or what if the application has modified
	the GL_UNPACK_ROW_LENGTH pixel store state before loadTexture
	is called?  
	
	We can fix the routine by calling glBindBuffer(GL_PIXEL_UNPACK_BUFFER,
	0) and setting all the pixel store unpack state to the initial state
	the loadTexture routine expects, but this is expensive.  It also risks
	disturbing the state so when loadTexture returns to the application,
	the application doesn't realize the current texture object (for
	whatever texture unit the current active texture happens to be) and
	pixel store state has changed.
	
	We can more efficiently implement this routine without disturbing
	selector or latched state as follows:
	
	  void loadTexture(GLint texobj, GLint width, GLint height,
	                   void *data)
	  {
	    glPushClientAttribDefaultEXT(GL_CLIENT_PIXEL_STORE_BIT);
	    glTextureImage2D(texobj, GL_TEXTURE_2D, 0, GL_RGB8,
	                     width, height, GL_RGB, GL_FLOAT, data);
	    glPopClientAttrib();
	  }
	
	Now loadTexture does not have to worry about inappropriately
	configured pixel store state or a non-zero pixel unpack buffer
	binding.  And loadTexture has no unintended side-effects for
	selector or latched state (assuming the client attrib state does
	not overflow).

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/EXT/direct_state_access.txt
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions, wrapper
from OpenGL.GL import glget
import ctypes
from OpenGL.raw.GL.EXT.direct_state_access import *
### END AUTOGENERATED SECTION