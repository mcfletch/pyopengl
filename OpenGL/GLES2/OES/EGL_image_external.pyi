"""OpenGL.GLES2.OES.EGL_image_external -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_REQUIRED_TEXTURE_IMAGE_UNITS_OES: int
GL_SAMPLER_EXTERNAL_OES: int
GL_TEXTURE_BINDING_EXTERNAL_OES: int
GL_TEXTURE_EXTERNAL_OES: int

def glEGLImageTargetTexture2DOES(target: int, image: Any) -> None: ...

def glInitEglImageExternalOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
