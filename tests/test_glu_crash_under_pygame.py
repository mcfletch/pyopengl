if __name__ == "__main__":
    import pygame
    pygame.init()
    screen = pygame.display.set_mode([800, 600], pygame.OPENGL | pygame.DOUBLEBUF)
    from OpenGL.GL import *
    from OpenGL.GLU import *