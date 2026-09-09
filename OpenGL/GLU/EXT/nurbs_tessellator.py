'''GLU extension EXT.nurbs_tessellator
'''
from OpenGL import extensions
# The GLU_EXT_nurbs_tessellator names are GLU constants and live with the
# rest of them.  They carry the values the extension specification gives
# (GLU_NURBS_BEGIN_EXT 100164 and its fellows), which are the values GLU
# 1.3 promoted them to, so the EXT spelling and the core one agree.
from OpenGL.raw.GLU import constants

GLU_NURBS_BEGIN_EXT = constants.GLU_NURBS_BEGIN_EXT
GLU_NURBS_VERTEX_EXT = constants.GLU_NURBS_VERTEX_EXT
GLU_NURBS_COLOR_EXT = constants.GLU_NURBS_COLOR_EXT
GLU_NURBS_TEX_COORD_EXT = constants.GLU_NURBS_TEX_COORD_EXT
GLU_NURBS_END_EXT = constants.GLU_NURBS_END_EXT
GLU_NURBS_BEGIN_DATA_EXT = constants.GLU_NURBS_BEGIN_DATA_EXT
GLU_NURBS_VERTEX_DATA_EXT = constants.GLU_NURBS_VERTEX_DATA_EXT
GLU_NURBS_NORMAL_DATA_EXT = constants.GLU_NURBS_NORMAL_DATA_EXT
GLU_NURBS_COLOR_DATA_EXT = constants.GLU_NURBS_COLOR_DATA_EXT
GLU_NURBS_TEX_COORD_DATA_EXT = constants.GLU_NURBS_TEX_COORD_DATA_EXT
GLU_NURBS_END_DATA_EXT = constants.GLU_NURBS_END_DATA_EXT
GLU_NURBS_MODE_EXT = constants.GLU_NURBS_MODE_EXT
GLU_NURBS_TESSELLATOR_EXT = constants.GLU_NURBS_TESSELLATOR_EXT
GLU_NURBS_RENDERER_EXT = constants.GLU_NURBS_RENDERER_EXT


def gluInitNurbsTessellatorEXT():
    '''Return boolean indicating whether this module is available'''
    return extensions.hasGLUExtension('GLU_EXT_nurbs_tessellator')
