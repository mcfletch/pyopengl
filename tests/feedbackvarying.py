"""Transliteration of https://open.gl/feedback into Python"""
from __future__ import print_function
import pygamegltest
from OpenGL.GL import *
from OpenGL.GL import shaders
vertex_shader = """#version 150 core
    in float inValue;
    out float outValue;

    void main() {
        outValue = sqrt(inValue);
    }
"""

@pygamegltest.pygametest(name="Geometry Shader Test")
def main():
    program = shaders.compileProgram(
        shaders.compileShader([vertex_shader], GL_VERTEX_SHADER), 
    )

    buff = ctypes.c_char_p( b"outValue" )
    c_text = ctypes.cast(ctypes.pointer(buff), ctypes.POINTER(ctypes.POINTER(GLchar)))
    # modifies the state in the linking of the program
    glTransformFeedbackVaryings(program, 1, c_text, GL_INTERLEAVED_ATTRIBS);
    
    # so have to re-link
    glLinkProgram(program)
    glUseProgram(program);

    vao = glGenVertexArrays(1);
    glBindVertexArray(vao);

    data = (GLfloat * 5)(1.0, 2.0, 3.0, 4.0, 5.0)
    
    vbo = glGenBuffers(1);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(data), data, GL_STATIC_DRAW);

    inputAttrib = glGetAttribLocation(program, "inValue");
    glEnableVertexAttribArray(inputAttrib);
    # Note the need to cast 0 to a GLvoidp here!
    glVertexAttribPointer(inputAttrib, 1, GL_FLOAT, GL_FALSE, 0, GLvoidp(0));

    tbo = glGenBuffers(1);
    glBindBuffer(GL_ARRAY_BUFFER, tbo);
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(data), None, GL_STATIC_READ);

    glEnable(GL_RASTERIZER_DISCARD);

    glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo);

    glBeginTransformFeedback(GL_POINTS);
    glDrawArrays(GL_POINTS, 0, len(data));
    glEndTransformFeedback();

    glDisable(GL_RASTERIZER_DISCARD);

    glFlush();

    feedback = (GLfloat*len(data))()
    glGetBufferSubData(GL_TRANSFORM_FEEDBACK_BUFFER, 0, ctypes.sizeof(feedback), feedback);

    for value in feedback:
        print(value)

if __name__ == "__main__":
    main()
