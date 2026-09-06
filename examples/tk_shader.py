#! /usr/bin/env python3
"""A shaded triangle in a Tkinter window, drawn with a GLSL 3.30 program.

What it shows: `OpenGL.Tk.GLFrame` is an ordinary `tkinter.Frame` with an
OpenGL context of its own, and the context is a **core profile**, so the modern
pipeline -- a shader program, a vertex array object, a uniform matrix -- is
available in a Tk application without any Tcl extension.

    python examples/tk_shader.py

Drag the window's corner to resize it; the triangle keeps turning.
"""

import ctypes
import math
import tkinter
from tkinter import ttk

from OpenGL.GL import (
    GL_ARRAY_BUFFER, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_FALSE,
    GL_FLOAT, GL_FRAGMENT_SHADER, GL_STATIC_DRAW, GL_TRIANGLES, GL_TRUE,
    GL_VERSION, GL_VERTEX_SHADER, glBindBuffer, glBindVertexArray,
    glBufferData, glClear, glClearColor, glDrawArrays, glEnableVertexAttribArray,
    glGenBuffers, glGenVertexArrays, glGetString, glGetUniformLocation,
    glUniformMatrix4fv, glUseProgram, glVertexAttribPointer,
)
from OpenGL.GL import shaders
from OpenGL.Tk import GLFrame, TkContextError

VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColour;
uniform mat4 transform;
out vec3 colour;
void main() {
    colour = aColour;
    gl_Position = transform * vec4(aPosition, 1.0);
}"""

FRAGMENT_SHADER = """#version 330 core
in vec3 colour;
out vec4 fragment;
void main() { fragment = vec4(colour, 1.0); }"""

#: Position and colour per corner, interleaved.
TRIANGLE = (
    -0.6, -0.5, 0.0,  1.0, 0.2, 0.2,
     0.6, -0.5, 0.0,  0.2, 1.0, 0.2,
     0.0,  0.6, 0.0,  0.2, 0.4, 1.0,
)

#: Milliseconds between frames.
INTERVAL = 16


class Triangle(GLFrame):
    """A turning triangle, in whatever size the widget has been given"""

    angle = 0.0

    def initgl(self):
        """Build the program and the buffer, once, with the context current"""
        self.program = shaders.compileProgram(
            shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.transform = glGetUniformLocation(self.program, 'transform')

        # A vertex array object is core-profile only, which is the point: this
        # is the pipeline a Tk application could not reach before.
        self.array = glGenVertexArrays(1)
        glBindVertexArray(self.array)
        data = (ctypes.c_float * len(TRIANGLE))(*TRIANGLE)
        glBindBuffer(GL_ARRAY_BUFFER, glGenBuffers(1))
        glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(data), data, GL_STATIC_DRAW)
        stride = 6 * ctypes.sizeof(ctypes.c_float)
        for location, offset in ((0, 0), (1, 3 * ctypes.sizeof(ctypes.c_float))):
            glEnableVertexAttribArray(location)
            glVertexAttribPointer(location, 3, GL_FLOAT, GL_FALSE, stride,
                                  ctypes.c_void_p(offset))
        glBindVertexArray(0)
        glClearColor(0.08, 0.09, 0.12, 1.0)

    def redraw(self):
        """One frame"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.angle += 0.02
        cosine, sine = math.cos(self.angle), math.sin(self.angle)
        # Row-major, and glUniformMatrix4fv is told so with GL_TRUE.
        matrix = (ctypes.c_float * 16)(
            cosine, -sine, 0.0, 0.0,
            sine, cosine, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        )
        glUseProgram(self.program)
        glUniformMatrix4fv(self.transform, 1, GL_TRUE, matrix)
        glBindVertexArray(self.array)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glBindVertexArray(0)
        glUseProgram(0)


def main():
    root = tkinter.Tk()
    root.title('OpenGL in a Tk widget')

    view = Triangle(root, width=480, height=360)
    view.pack(fill='both', expand=True, padx=8, pady=(8, 0))

    reported = ttk.Label(root, text='')
    reported.pack(pady=4)
    ttk.Button(root, text='Quit', command=root.destroy).pack(pady=(0, 8))

    try:
        view.waitForMap()
    except TkContextError as error:
        # A driver may refuse the context asked for; a program that says so is
        # better than one that shows an empty frame.
        reported.configure(text='no OpenGL here: %s' % (error,))
    else:
        view.makeCurrent()
        reported.configure(text=glGetString(GL_VERSION).decode('ascii', 'replace'))
        view.startAnimation(INTERVAL)
    root.mainloop()


if __name__ == '__main__':
    main()
