import testdecorator
from OpenGL.GL import *
import checkutils


def drawOneLine(x1, y1, x2, y2, width):
    glDisable(GL_LINE_SMOOTH)
    glLineWidth(width)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()


@testdecorator.gltest(size=(800, 600), name="linewidth")
def test_linewidth():
    glEnable(GL_BLEND)
    glClearColor(68 / 255.0, 68 / 255.0, 68 / 255.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glViewport(0, 0, 800, 600)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 800.0, 600.0, 0.0, 0.0, 1.0)
    for y in range(1, 20):
        drawOneLine(10, 20 * y + .5, 100, 20 * y + .5, y * .5)


if __name__ == "__main__":
    checkutils.run_check(test_linewidth)
