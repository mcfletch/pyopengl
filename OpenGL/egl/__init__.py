"""egl wrapper for PyOpenGL"""
# THIS FILE IS AUTO-GENERATED DO NOT EDIT!
from OpenGL import platform as _p
from OpenGL.khr import *
from OpenGL import khr as _cs
from OpenGL import arrays
from OpenGL.constant import IntConstant as _C
import ctypes

# Callback types, this is a hack to avoid making the 
# khr module depend on the platform or needing to change generator for now...
CALLBACK_TYPE = _p.PLATFORM.functionTypeFor( _p.PLATFORM.EGL )
_cs.EGLSetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )
_cs.EGLGetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )

EGL_DEFAULT_DISPLAY = EGLNativeDisplayType(None)
EGL_NO_CONTEXT = EGLContext(0)
EGL_NO_DISPLAY = EGLDisplay(0)
EGL_NO_SURFACE = EGLSurface(0)
EGL_DONT_CARE = -1

def _f( function ):
    return _p.createFunction( function,_p.EGL,None,False)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',1)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',1)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',1)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',1)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',1)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',1)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',1)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',1)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',0)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',0)
KHRONOS_SUPPORT_INT64=_C('KHRONOS_SUPPORT_INT64',1)
KHRONOS_SUPPORT_FLOAT=_C('KHRONOS_SUPPORT_FLOAT',1)
KHRONOS_MAX_ENUM=_C('KHRONOS_MAX_ENUM',0x7FFFFFFF)
WIN32_LEAN_AND_MEAN=_C('WIN32_LEAN_AND_MEAN',1)
EGL_VERSION_1_0=_C('EGL_VERSION_1_0',1)
EGL_VERSION_1_1=_C('EGL_VERSION_1_1',1)
EGL_VERSION_1_2=_C('EGL_VERSION_1_2',1)
EGL_VERSION_1_3=_C('EGL_VERSION_1_3',1)
EGL_VERSION_1_4=_C('EGL_VERSION_1_4',1)
EGL_FALSE=_C('EGL_FALSE',0)
EGL_TRUE=_C('EGL_TRUE',1)
EGL_SUCCESS=_C('EGL_SUCCESS',0x3000)
EGL_NOT_INITIALIZED=_C('EGL_NOT_INITIALIZED',0x3001)
EGL_BAD_ACCESS=_C('EGL_BAD_ACCESS',0x3002)
EGL_BAD_ALLOC=_C('EGL_BAD_ALLOC',0x3003)
EGL_BAD_ATTRIBUTE=_C('EGL_BAD_ATTRIBUTE',0x3004)
EGL_BAD_CONFIG=_C('EGL_BAD_CONFIG',0x3005)
EGL_BAD_CONTEXT=_C('EGL_BAD_CONTEXT',0x3006)
EGL_BAD_CURRENT_SURFACE=_C('EGL_BAD_CURRENT_SURFACE',0x3007)
EGL_BAD_DISPLAY=_C('EGL_BAD_DISPLAY',0x3008)
EGL_BAD_MATCH=_C('EGL_BAD_MATCH',0x3009)
EGL_BAD_NATIVE_PIXMAP=_C('EGL_BAD_NATIVE_PIXMAP',0x300A)
EGL_BAD_NATIVE_WINDOW=_C('EGL_BAD_NATIVE_WINDOW',0x300B)
EGL_BAD_PARAMETER=_C('EGL_BAD_PARAMETER',0x300C)
EGL_BAD_SURFACE=_C('EGL_BAD_SURFACE',0x300D)
EGL_CONTEXT_LOST=_C('EGL_CONTEXT_LOST',0x300E)
EGL_BUFFER_SIZE=_C('EGL_BUFFER_SIZE',0x3020)
EGL_ALPHA_SIZE=_C('EGL_ALPHA_SIZE',0x3021)
EGL_BLUE_SIZE=_C('EGL_BLUE_SIZE',0x3022)
EGL_GREEN_SIZE=_C('EGL_GREEN_SIZE',0x3023)
EGL_RED_SIZE=_C('EGL_RED_SIZE',0x3024)
EGL_DEPTH_SIZE=_C('EGL_DEPTH_SIZE',0x3025)
EGL_STENCIL_SIZE=_C('EGL_STENCIL_SIZE',0x3026)
EGL_CONFIG_CAVEAT=_C('EGL_CONFIG_CAVEAT',0x3027)
EGL_CONFIG_ID=_C('EGL_CONFIG_ID',0x3028)
EGL_LEVEL=_C('EGL_LEVEL',0x3029)
EGL_MAX_PBUFFER_HEIGHT=_C('EGL_MAX_PBUFFER_HEIGHT',0x302A)
EGL_MAX_PBUFFER_PIXELS=_C('EGL_MAX_PBUFFER_PIXELS',0x302B)
EGL_MAX_PBUFFER_WIDTH=_C('EGL_MAX_PBUFFER_WIDTH',0x302C)
EGL_NATIVE_RENDERABLE=_C('EGL_NATIVE_RENDERABLE',0x302D)
EGL_NATIVE_VISUAL_ID=_C('EGL_NATIVE_VISUAL_ID',0x302E)
EGL_NATIVE_VISUAL_TYPE=_C('EGL_NATIVE_VISUAL_TYPE',0x302F)
EGL_SAMPLES=_C('EGL_SAMPLES',0x3031)
EGL_SAMPLE_BUFFERS=_C('EGL_SAMPLE_BUFFERS',0x3032)
EGL_SURFACE_TYPE=_C('EGL_SURFACE_TYPE',0x3033)
EGL_TRANSPARENT_TYPE=_C('EGL_TRANSPARENT_TYPE',0x3034)
EGL_TRANSPARENT_BLUE_VALUE=_C('EGL_TRANSPARENT_BLUE_VALUE',0x3035)
EGL_TRANSPARENT_GREEN_VALUE=_C('EGL_TRANSPARENT_GREEN_VALUE',0x3036)
EGL_TRANSPARENT_RED_VALUE=_C('EGL_TRANSPARENT_RED_VALUE',0x3037)
EGL_NONE=_C('EGL_NONE',0x3038)
EGL_BIND_TO_TEXTURE_RGB=_C('EGL_BIND_TO_TEXTURE_RGB',0x3039)
EGL_BIND_TO_TEXTURE_RGBA=_C('EGL_BIND_TO_TEXTURE_RGBA',0x303A)
EGL_MIN_SWAP_INTERVAL=_C('EGL_MIN_SWAP_INTERVAL',0x303B)
EGL_MAX_SWAP_INTERVAL=_C('EGL_MAX_SWAP_INTERVAL',0x303C)
EGL_LUMINANCE_SIZE=_C('EGL_LUMINANCE_SIZE',0x303D)
EGL_ALPHA_MASK_SIZE=_C('EGL_ALPHA_MASK_SIZE',0x303E)
EGL_COLOR_BUFFER_TYPE=_C('EGL_COLOR_BUFFER_TYPE',0x303F)
EGL_RENDERABLE_TYPE=_C('EGL_RENDERABLE_TYPE',0x3040)
EGL_MATCH_NATIVE_PIXMAP=_C('EGL_MATCH_NATIVE_PIXMAP',0x3041)
EGL_CONFORMANT=_C('EGL_CONFORMANT',0x3042)
EGL_SLOW_CONFIG=_C('EGL_SLOW_CONFIG',0x3050)
EGL_NON_CONFORMANT_CONFIG=_C('EGL_NON_CONFORMANT_CONFIG',0x3051)
EGL_TRANSPARENT_RGB=_C('EGL_TRANSPARENT_RGB',0x3052)
EGL_RGB_BUFFER=_C('EGL_RGB_BUFFER',0x308E)
EGL_LUMINANCE_BUFFER=_C('EGL_LUMINANCE_BUFFER',0x308F)
EGL_NO_TEXTURE=_C('EGL_NO_TEXTURE',0x305C)
EGL_TEXTURE_RGB=_C('EGL_TEXTURE_RGB',0x305D)
EGL_TEXTURE_RGBA=_C('EGL_TEXTURE_RGBA',0x305E)
EGL_TEXTURE_2D=_C('EGL_TEXTURE_2D',0x305F)
EGL_PBUFFER_BIT=_C('EGL_PBUFFER_BIT',0x0001)
EGL_PIXMAP_BIT=_C('EGL_PIXMAP_BIT',0x0002)
EGL_WINDOW_BIT=_C('EGL_WINDOW_BIT',0x0004)
EGL_VG_COLORSPACE_LINEAR_BIT=_C('EGL_VG_COLORSPACE_LINEAR_BIT',0x0020)
EGL_VG_ALPHA_FORMAT_PRE_BIT=_C('EGL_VG_ALPHA_FORMAT_PRE_BIT',0x0040)
EGL_MULTISAMPLE_RESOLVE_BOX_BIT=_C('EGL_MULTISAMPLE_RESOLVE_BOX_BIT',0x0200)
EGL_SWAP_BEHAVIOR_PRESERVED_BIT=_C('EGL_SWAP_BEHAVIOR_PRESERVED_BIT',0x0400)
EGL_OPENGL_ES_BIT=_C('EGL_OPENGL_ES_BIT',0x0001)
EGL_OPENVG_BIT=_C('EGL_OPENVG_BIT',0x0002)
EGL_OPENGL_ES2_BIT=_C('EGL_OPENGL_ES2_BIT',0x0004)
EGL_OPENGL_BIT=_C('EGL_OPENGL_BIT',0x0008)
EGL_VENDOR=_C('EGL_VENDOR',0x3053)
EGL_VERSION=_C('EGL_VERSION',0x3054)
EGL_EXTENSIONS=_C('EGL_EXTENSIONS',0x3055)
EGL_CLIENT_APIS=_C('EGL_CLIENT_APIS',0x308D)
EGL_HEIGHT=_C('EGL_HEIGHT',0x3056)
EGL_WIDTH=_C('EGL_WIDTH',0x3057)
EGL_LARGEST_PBUFFER=_C('EGL_LARGEST_PBUFFER',0x3058)
EGL_TEXTURE_FORMAT=_C('EGL_TEXTURE_FORMAT',0x3080)
EGL_TEXTURE_TARGET=_C('EGL_TEXTURE_TARGET',0x3081)
EGL_MIPMAP_TEXTURE=_C('EGL_MIPMAP_TEXTURE',0x3082)
EGL_MIPMAP_LEVEL=_C('EGL_MIPMAP_LEVEL',0x3083)
EGL_RENDER_BUFFER=_C('EGL_RENDER_BUFFER',0x3086)
EGL_VG_COLORSPACE=_C('EGL_VG_COLORSPACE',0x3087)
EGL_VG_ALPHA_FORMAT=_C('EGL_VG_ALPHA_FORMAT',0x3088)
EGL_HORIZONTAL_RESOLUTION=_C('EGL_HORIZONTAL_RESOLUTION',0x3090)
EGL_VERTICAL_RESOLUTION=_C('EGL_VERTICAL_RESOLUTION',0x3091)
EGL_PIXEL_ASPECT_RATIO=_C('EGL_PIXEL_ASPECT_RATIO',0x3092)
EGL_SWAP_BEHAVIOR=_C('EGL_SWAP_BEHAVIOR',0x3093)
EGL_MULTISAMPLE_RESOLVE=_C('EGL_MULTISAMPLE_RESOLVE',0x3099)
EGL_BACK_BUFFER=_C('EGL_BACK_BUFFER',0x3084)
EGL_SINGLE_BUFFER=_C('EGL_SINGLE_BUFFER',0x3085)
EGL_VG_COLORSPACE_sRGB=_C('EGL_VG_COLORSPACE_sRGB',0x3089)
EGL_VG_COLORSPACE_LINEAR=_C('EGL_VG_COLORSPACE_LINEAR',0x308A)
EGL_VG_ALPHA_FORMAT_NONPRE=_C('EGL_VG_ALPHA_FORMAT_NONPRE',0x308B)
EGL_VG_ALPHA_FORMAT_PRE=_C('EGL_VG_ALPHA_FORMAT_PRE',0x308C)
EGL_DISPLAY_SCALING=_C('EGL_DISPLAY_SCALING',10000)
EGL_BUFFER_PRESERVED=_C('EGL_BUFFER_PRESERVED',0x3094)
EGL_BUFFER_DESTROYED=_C('EGL_BUFFER_DESTROYED',0x3095)
EGL_OPENVG_IMAGE=_C('EGL_OPENVG_IMAGE',0x3096)
EGL_CONTEXT_CLIENT_TYPE=_C('EGL_CONTEXT_CLIENT_TYPE',0x3097)
EGL_CONTEXT_CLIENT_VERSION=_C('EGL_CONTEXT_CLIENT_VERSION',0x3098)
EGL_MULTISAMPLE_RESOLVE_DEFAULT=_C('EGL_MULTISAMPLE_RESOLVE_DEFAULT',0x309A)
EGL_MULTISAMPLE_RESOLVE_BOX=_C('EGL_MULTISAMPLE_RESOLVE_BOX',0x309B)
EGL_OPENGL_ES_API=_C('EGL_OPENGL_ES_API',0x30A0)
EGL_OPENVG_API=_C('EGL_OPENVG_API',0x30A1)
EGL_OPENGL_API=_C('EGL_OPENGL_API',0x30A2)
EGL_DRAW=_C('EGL_DRAW',0x3059)
EGL_READ=_C('EGL_READ',0x305A)
EGL_CORE_NATIVE_ENGINE=_C('EGL_CORE_NATIVE_ENGINE',0x305B)
EGL_EGLEXT_VERSION=_C('EGL_EGLEXT_VERSION',15)
EGL_KHR_config_attribs=_C('EGL_KHR_config_attribs',1)
EGL_CONFORMANT_KHR=_C('EGL_CONFORMANT_KHR',0x3042)
EGL_VG_COLORSPACE_LINEAR_BIT_KHR=_C('EGL_VG_COLORSPACE_LINEAR_BIT_KHR',0x0020)
EGL_VG_ALPHA_FORMAT_PRE_BIT_KHR=_C('EGL_VG_ALPHA_FORMAT_PRE_BIT_KHR',0x0040)
EGL_KHR_lock_surface=_C('EGL_KHR_lock_surface',1)
EGL_READ_SURFACE_BIT_KHR=_C('EGL_READ_SURFACE_BIT_KHR',0x0001)
EGL_WRITE_SURFACE_BIT_KHR=_C('EGL_WRITE_SURFACE_BIT_KHR',0x0002)
EGL_LOCK_SURFACE_BIT_KHR=_C('EGL_LOCK_SURFACE_BIT_KHR',0x0080)
EGL_OPTIMAL_FORMAT_BIT_KHR=_C('EGL_OPTIMAL_FORMAT_BIT_KHR',0x0100)
EGL_MATCH_FORMAT_KHR=_C('EGL_MATCH_FORMAT_KHR',0x3043)
EGL_FORMAT_RGB_565_EXACT_KHR=_C('EGL_FORMAT_RGB_565_EXACT_KHR',0x30C0)
EGL_FORMAT_RGB_565_KHR=_C('EGL_FORMAT_RGB_565_KHR',0x30C1)
EGL_FORMAT_RGBA_8888_EXACT_KHR=_C('EGL_FORMAT_RGBA_8888_EXACT_KHR',0x30C2)
EGL_FORMAT_RGBA_8888_KHR=_C('EGL_FORMAT_RGBA_8888_KHR',0x30C3)
EGL_MAP_PRESERVE_PIXELS_KHR=_C('EGL_MAP_PRESERVE_PIXELS_KHR',0x30C4)
EGL_LOCK_USAGE_HINT_KHR=_C('EGL_LOCK_USAGE_HINT_KHR',0x30C5)
EGL_BITMAP_POINTER_KHR=_C('EGL_BITMAP_POINTER_KHR',0x30C6)
EGL_BITMAP_PITCH_KHR=_C('EGL_BITMAP_PITCH_KHR',0x30C7)
EGL_BITMAP_ORIGIN_KHR=_C('EGL_BITMAP_ORIGIN_KHR',0x30C8)
EGL_BITMAP_PIXEL_RED_OFFSET_KHR=_C('EGL_BITMAP_PIXEL_RED_OFFSET_KHR',0x30C9)
EGL_BITMAP_PIXEL_GREEN_OFFSET_KHR=_C('EGL_BITMAP_PIXEL_GREEN_OFFSET_KHR',0x30CA)
EGL_BITMAP_PIXEL_BLUE_OFFSET_KHR=_C('EGL_BITMAP_PIXEL_BLUE_OFFSET_KHR',0x30CB)
EGL_BITMAP_PIXEL_ALPHA_OFFSET_KHR=_C('EGL_BITMAP_PIXEL_ALPHA_OFFSET_KHR',0x30CC)
EGL_BITMAP_PIXEL_LUMINANCE_OFFSET_KHR=_C('EGL_BITMAP_PIXEL_LUMINANCE_OFFSET_KHR',0x30CD)
EGL_LOWER_LEFT_KHR=_C('EGL_LOWER_LEFT_KHR',0x30CE)
EGL_UPPER_LEFT_KHR=_C('EGL_UPPER_LEFT_KHR',0x30CF)
EGL_KHR_image=_C('EGL_KHR_image',1)
EGL_NATIVE_PIXMAP_KHR=_C('EGL_NATIVE_PIXMAP_KHR',0x30B0)
EGL_KHR_vg_parent_image=_C('EGL_KHR_vg_parent_image',1)
EGL_VG_PARENT_IMAGE_KHR=_C('EGL_VG_PARENT_IMAGE_KHR',0x30BA)
EGL_KHR_gl_texture_2D_image=_C('EGL_KHR_gl_texture_2D_image',1)
EGL_GL_TEXTURE_2D_KHR=_C('EGL_GL_TEXTURE_2D_KHR',0x30B1)
EGL_GL_TEXTURE_LEVEL_KHR=_C('EGL_GL_TEXTURE_LEVEL_KHR',0x30BC)
EGL_KHR_gl_texture_cubemap_image=_C('EGL_KHR_gl_texture_cubemap_image',1)
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_X_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_X_KHR',0x30B3)
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_X_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_X_KHR',0x30B4)
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Y_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Y_KHR',0x30B5)
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Y_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Y_KHR',0x30B6)
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Z_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Z_KHR',0x30B7)
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Z_KHR=_C('EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Z_KHR',0x30B8)
EGL_KHR_gl_texture_3D_image=_C('EGL_KHR_gl_texture_3D_image',1)
EGL_GL_TEXTURE_3D_KHR=_C('EGL_GL_TEXTURE_3D_KHR',0x30B2)
EGL_GL_TEXTURE_ZOFFSET_KHR=_C('EGL_GL_TEXTURE_ZOFFSET_KHR',0x30BD)
EGL_KHR_gl_renderbuffer_image=_C('EGL_KHR_gl_renderbuffer_image',1)
EGL_GL_RENDERBUFFER_KHR=_C('EGL_GL_RENDERBUFFER_KHR',0x30B9)
EGL_KHR_reusable_sync=_C('EGL_KHR_reusable_sync',1)
EGL_SYNC_STATUS_KHR=_C('EGL_SYNC_STATUS_KHR',0x30F1)
EGL_SIGNALED_KHR=_C('EGL_SIGNALED_KHR',0x30F2)
EGL_UNSIGNALED_KHR=_C('EGL_UNSIGNALED_KHR',0x30F3)
EGL_TIMEOUT_EXPIRED_KHR=_C('EGL_TIMEOUT_EXPIRED_KHR',0x30F5)
EGL_CONDITION_SATISFIED_KHR=_C('EGL_CONDITION_SATISFIED_KHR',0x30F6)
EGL_SYNC_TYPE_KHR=_C('EGL_SYNC_TYPE_KHR',0x30F7)
EGL_SYNC_REUSABLE_KHR=_C('EGL_SYNC_REUSABLE_KHR',0x30FA)
EGL_SYNC_FLUSH_COMMANDS_BIT_KHR=_C('EGL_SYNC_FLUSH_COMMANDS_BIT_KHR',0x0001)
EGL_FOREVER_KHR=_C('EGL_FOREVER_KHR',0xFFFFFFFFFFFFFFFF)
EGL_KHR_image_base=_C('EGL_KHR_image_base',1)
EGL_IMAGE_PRESERVED_KHR=_C('EGL_IMAGE_PRESERVED_KHR',0x30D2)
EGL_KHR_image_pixmap=_C('EGL_KHR_image_pixmap',1)
EGL_IMG_context_priority=_C('EGL_IMG_context_priority',1)
EGL_CONTEXT_PRIORITY_LEVEL_IMG=_C('EGL_CONTEXT_PRIORITY_LEVEL_IMG',0x3100)
EGL_CONTEXT_PRIORITY_HIGH_IMG=_C('EGL_CONTEXT_PRIORITY_HIGH_IMG',0x3101)
EGL_CONTEXT_PRIORITY_MEDIUM_IMG=_C('EGL_CONTEXT_PRIORITY_MEDIUM_IMG',0x3102)
EGL_CONTEXT_PRIORITY_LOW_IMG=_C('EGL_CONTEXT_PRIORITY_LOW_IMG',0x3103)
EGL_KHR_lock_surface2=_C('EGL_KHR_lock_surface2',1)
EGL_BITMAP_PIXEL_SIZE_KHR=_C('EGL_BITMAP_PIXEL_SIZE_KHR',0x3110)
EGL_NV_coverage_sample=_C('EGL_NV_coverage_sample',1)
EGL_COVERAGE_BUFFERS_NV=_C('EGL_COVERAGE_BUFFERS_NV',0x30E0)
EGL_COVERAGE_SAMPLES_NV=_C('EGL_COVERAGE_SAMPLES_NV',0x30E1)
EGL_NV_depth_nonlinear=_C('EGL_NV_depth_nonlinear',1)
EGL_DEPTH_ENCODING_NV=_C('EGL_DEPTH_ENCODING_NV',0x30E2)
EGL_DEPTH_ENCODING_NONE_NV=_C('EGL_DEPTH_ENCODING_NONE_NV',0)
EGL_DEPTH_ENCODING_NONLINEAR_NV=_C('EGL_DEPTH_ENCODING_NONLINEAR_NV',0x30E3)
EGL_NV_sync=_C('EGL_NV_sync',1)
EGL_SYNC_PRIOR_COMMANDS_COMPLETE_NV=_C('EGL_SYNC_PRIOR_COMMANDS_COMPLETE_NV',0x30E6)
EGL_SYNC_STATUS_NV=_C('EGL_SYNC_STATUS_NV',0x30E7)
EGL_SIGNALED_NV=_C('EGL_SIGNALED_NV',0x30E8)
EGL_UNSIGNALED_NV=_C('EGL_UNSIGNALED_NV',0x30E9)
EGL_SYNC_FLUSH_COMMANDS_BIT_NV=_C('EGL_SYNC_FLUSH_COMMANDS_BIT_NV',0x0001)
EGL_FOREVER_NV=_C('EGL_FOREVER_NV',0xFFFFFFFFFFFFFFFF)
EGL_ALREADY_SIGNALED_NV=_C('EGL_ALREADY_SIGNALED_NV',0x30EA)
EGL_TIMEOUT_EXPIRED_NV=_C('EGL_TIMEOUT_EXPIRED_NV',0x30EB)
EGL_CONDITION_SATISFIED_NV=_C('EGL_CONDITION_SATISFIED_NV',0x30EC)
EGL_SYNC_TYPE_NV=_C('EGL_SYNC_TYPE_NV',0x30ED)
EGL_SYNC_CONDITION_NV=_C('EGL_SYNC_CONDITION_NV',0x30EE)
EGL_SYNC_FENCE_NV=_C('EGL_SYNC_FENCE_NV',0x30EF)
EGL_KHR_fence_sync=_C('EGL_KHR_fence_sync',1)
EGL_SYNC_PRIOR_COMMANDS_COMPLETE_KHR=_C('EGL_SYNC_PRIOR_COMMANDS_COMPLETE_KHR',0x30F0)
EGL_SYNC_CONDITION_KHR=_C('EGL_SYNC_CONDITION_KHR',0x30F8)
EGL_SYNC_FENCE_KHR=_C('EGL_SYNC_FENCE_KHR',0x30F9)
EGL_HI_clientpixmap=_C('EGL_HI_clientpixmap',1)
EGL_CLIENT_PIXMAP_POINTER_HI=_C('EGL_CLIENT_PIXMAP_POINTER_HI',0x8F74)
EGL_HI_colorformats=_C('EGL_HI_colorformats',1)
EGL_COLOR_FORMAT_HI=_C('EGL_COLOR_FORMAT_HI',0x8F70)
EGL_COLOR_RGB_HI=_C('EGL_COLOR_RGB_HI',0x8F71)
EGL_COLOR_RGBA_HI=_C('EGL_COLOR_RGBA_HI',0x8F72)
EGL_COLOR_ARGB_HI=_C('EGL_COLOR_ARGB_HI',0x8F73)
EGL_MESA_drm_image=_C('EGL_MESA_drm_image',1)
EGL_DRM_BUFFER_FORMAT_MESA=_C('EGL_DRM_BUFFER_FORMAT_MESA',0x31D0)
EGL_DRM_BUFFER_USE_MESA=_C('EGL_DRM_BUFFER_USE_MESA',0x31D1)
EGL_DRM_BUFFER_FORMAT_ARGB32_MESA=_C('EGL_DRM_BUFFER_FORMAT_ARGB32_MESA',0x31D2)
EGL_DRM_BUFFER_MESA=_C('EGL_DRM_BUFFER_MESA',0x31D3)
EGL_DRM_BUFFER_STRIDE_MESA=_C('EGL_DRM_BUFFER_STRIDE_MESA',0x31D4)
EGL_DRM_BUFFER_USE_SCANOUT_MESA=_C('EGL_DRM_BUFFER_USE_SCANOUT_MESA',0x00000001)
EGL_DRM_BUFFER_USE_SHARE_MESA=_C('EGL_DRM_BUFFER_USE_SHARE_MESA',0x00000002)
EGL_NV_post_sub_buffer=_C('EGL_NV_post_sub_buffer',1)
EGL_POST_SUB_BUFFER_SUPPORTED_NV=_C('EGL_POST_SUB_BUFFER_SUPPORTED_NV',0x30BE)
EGL_ANGLE_query_surface_pointer=_C('EGL_ANGLE_query_surface_pointer',1)
EGL_ANGLE_surface_d3d_texture_2d_share_handle=_C('EGL_ANGLE_surface_d3d_texture_2d_share_handle',1)
EGL_D3D_TEXTURE_2D_SHARE_HANDLE_ANGLE=_C('EGL_D3D_TEXTURE_2D_SHARE_HANDLE_ANGLE',0x3200)
EGL_NV_coverage_sample_resolve=_C('EGL_NV_coverage_sample_resolve',1)
EGL_COVERAGE_SAMPLE_RESOLVE_NV=_C('EGL_COVERAGE_SAMPLE_RESOLVE_NV',0x3131)
EGL_COVERAGE_SAMPLE_RESOLVE_DEFAULT_NV=_C('EGL_COVERAGE_SAMPLE_RESOLVE_DEFAULT_NV',0x3132)
EGL_COVERAGE_SAMPLE_RESOLVE_NONE_NV=_C('EGL_COVERAGE_SAMPLE_RESOLVE_NONE_NV',0x3133)
EGL_NV_system_time=_C('EGL_NV_system_time',1)
EGL_KHR_stream=_C('EGL_KHR_stream',1)
EGL_CONSUMER_LATENCY_USEC_KHR=_C('EGL_CONSUMER_LATENCY_USEC_KHR',0x3210)
EGL_PRODUCER_FRAME_KHR=_C('EGL_PRODUCER_FRAME_KHR',0x3212)
EGL_CONSUMER_FRAME_KHR=_C('EGL_CONSUMER_FRAME_KHR',0x3213)
EGL_STREAM_STATE_KHR=_C('EGL_STREAM_STATE_KHR',0x3214)
EGL_STREAM_STATE_CREATED_KHR=_C('EGL_STREAM_STATE_CREATED_KHR',0x3215)
EGL_STREAM_STATE_CONNECTING_KHR=_C('EGL_STREAM_STATE_CONNECTING_KHR',0x3216)
EGL_STREAM_STATE_EMPTY_KHR=_C('EGL_STREAM_STATE_EMPTY_KHR',0x3217)
EGL_STREAM_STATE_NEW_FRAME_AVAILABLE_KHR=_C('EGL_STREAM_STATE_NEW_FRAME_AVAILABLE_KHR',0x3218)
EGL_STREAM_STATE_OLD_FRAME_AVAILABLE_KHR=_C('EGL_STREAM_STATE_OLD_FRAME_AVAILABLE_KHR',0x3219)
EGL_STREAM_STATE_DISCONNECTED_KHR=_C('EGL_STREAM_STATE_DISCONNECTED_KHR',0x321A)
EGL_BAD_STREAM_KHR=_C('EGL_BAD_STREAM_KHR',0x321B)
EGL_BAD_STATE_KHR=_C('EGL_BAD_STATE_KHR',0x321C)
EGL_KHR_stream_consumer_gltexture=_C('EGL_KHR_stream_consumer_gltexture',1)
EGL_CONSUMER_ACQUIRE_TIMEOUT_USEC_KHR=_C('EGL_CONSUMER_ACQUIRE_TIMEOUT_USEC_KHR',0x321E)
EGL_KHR_stream_producer_eglsurface=_C('EGL_KHR_stream_producer_eglsurface',1)
EGL_STREAM_BIT_KHR=_C('EGL_STREAM_BIT_KHR',0x0800)
EGL_KHR_stream_producer_aldatalocator=_C('EGL_KHR_stream_producer_aldatalocator',1)
EGL_KHR_stream_fifo=_C('EGL_KHR_stream_fifo',1)
EGL_STREAM_FIFO_LENGTH_KHR=_C('EGL_STREAM_FIFO_LENGTH_KHR',0x31FC)
EGL_STREAM_TIME_NOW_KHR=_C('EGL_STREAM_TIME_NOW_KHR',0x31FD)
EGL_STREAM_TIME_CONSUMER_KHR=_C('EGL_STREAM_TIME_CONSUMER_KHR',0x31FE)
EGL_STREAM_TIME_PRODUCER_KHR=_C('EGL_STREAM_TIME_PRODUCER_KHR',0x31FF)
EGL_EXT_create_context_robustness=_C('EGL_EXT_create_context_robustness',1)
EGL_CONTEXT_OPENGL_ROBUST_ACCESS_EXT=_C('EGL_CONTEXT_OPENGL_ROBUST_ACCESS_EXT',0x30BF)
EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY_EXT=_C('EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY_EXT',0x3138)
EGL_NO_RESET_NOTIFICATION_EXT=_C('EGL_NO_RESET_NOTIFICATION_EXT',0x31BE)
EGL_LOSE_CONTEXT_ON_RESET_EXT=_C('EGL_LOSE_CONTEXT_ON_RESET_EXT',0x31BF)
EGL_ANGLE_d3d_share_handle_client_buffer=_C('EGL_ANGLE_d3d_share_handle_client_buffer',1)
EGL_KHR_create_context=_C('EGL_KHR_create_context',1)
EGL_CONTEXT_MINOR_VERSION_KHR=_C('EGL_CONTEXT_MINOR_VERSION_KHR',0x30FB)
EGL_CONTEXT_FLAGS_KHR=_C('EGL_CONTEXT_FLAGS_KHR',0x30FC)
EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR=_C('EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR',0x30FD)
EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY_KHR=_C('EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY_KHR',0x31BD)
EGL_NO_RESET_NOTIFICATION_KHR=_C('EGL_NO_RESET_NOTIFICATION_KHR',0x31BE)
EGL_LOSE_CONTEXT_ON_RESET_KHR=_C('EGL_LOSE_CONTEXT_ON_RESET_KHR',0x31BF)
EGL_CONTEXT_OPENGL_DEBUG_BIT_KHR=_C('EGL_CONTEXT_OPENGL_DEBUG_BIT_KHR',0x00000001)
EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE_BIT_KHR=_C('EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE_BIT_KHR',0x00000002)
EGL_CONTEXT_OPENGL_ROBUST_ACCESS_BIT_KHR=_C('EGL_CONTEXT_OPENGL_ROBUST_ACCESS_BIT_KHR',0x00000004)
EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR=_C('EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR',0x00000001)
EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT_KHR=_C('EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT_KHR',0x00000002)
EGL_OPENGL_ES3_BIT_KHR=_C('EGL_OPENGL_ES3_BIT_KHR',0x00000040)
EGL_KHR_surfaceless_context=_C('EGL_KHR_surfaceless_context',1)
EGL_KHR_stream_cross_process_fd=_C('EGL_KHR_stream_cross_process_fd',1)
EGL_EXT_multiview_window=_C('EGL_EXT_multiview_window',1)
EGL_MULTIVIEW_VIEW_COUNT_EXT=_C('EGL_MULTIVIEW_VIEW_COUNT_EXT',0x3134)
EGL_KHR_wait_sync=_C('EGL_KHR_wait_sync',1)
EGL_NV_post_convert_rounding=_C('EGL_NV_post_convert_rounding',1)
EGL_NV_native_query=_C('EGL_NV_native_query',1)
EGL_NV_3dvision_surface=_C('EGL_NV_3dvision_surface',1)
EGL_AUTO_STEREO_NV=_C('EGL_AUTO_STEREO_NV',0x3136)
EGL_ANDROID_framebuffer_target=_C('EGL_ANDROID_framebuffer_target',1)
EGL_FRAMEBUFFER_TARGET_ANDROID=_C('EGL_FRAMEBUFFER_TARGET_ANDROID',0x3147)
EGL_ANDROID_blob_cache=_C('EGL_ANDROID_blob_cache',1)
EGL_ANDROID_image_native_buffer=_C('EGL_ANDROID_image_native_buffer',1)
EGL_NATIVE_BUFFER_ANDROID=_C('EGL_NATIVE_BUFFER_ANDROID',0x3140)
EGL_ANDROID_native_fence_sync=_C('EGL_ANDROID_native_fence_sync',1)
EGL_SYNC_NATIVE_FENCE_ANDROID=_C('EGL_SYNC_NATIVE_FENCE_ANDROID',0x3144)
EGL_SYNC_NATIVE_FENCE_FD_ANDROID=_C('EGL_SYNC_NATIVE_FENCE_FD_ANDROID',0x3145)
EGL_SYNC_NATIVE_FENCE_SIGNALED_ANDROID=_C('EGL_SYNC_NATIVE_FENCE_SIGNALED_ANDROID',0x3146)
EGL_NO_NATIVE_FENCE_FD_ANDROID=_C('EGL_NO_NATIVE_FENCE_FD_ANDROID',1)
EGL_ANDROID_recordable=_C('EGL_ANDROID_recordable',1)
EGL_RECORDABLE_ANDROID=_C('EGL_RECORDABLE_ANDROID',0x3142)
EGL_EXT_buffer_age=_C('EGL_EXT_buffer_age',1)
EGL_BUFFER_AGE_EXT=_C('EGL_BUFFER_AGE_EXT',0x313D)
EGL_EXT_image_dma_buf_import=_C('EGL_EXT_image_dma_buf_import',1)
EGL_LINUX_DMA_BUF_EXT=_C('EGL_LINUX_DMA_BUF_EXT',0x3270)
EGL_LINUX_DRM_FOURCC_EXT=_C('EGL_LINUX_DRM_FOURCC_EXT',0x3271)
EGL_DMA_BUF_PLANE0_FD_EXT=_C('EGL_DMA_BUF_PLANE0_FD_EXT',0x3272)
EGL_DMA_BUF_PLANE0_OFFSET_EXT=_C('EGL_DMA_BUF_PLANE0_OFFSET_EXT',0x3273)
EGL_DMA_BUF_PLANE0_PITCH_EXT=_C('EGL_DMA_BUF_PLANE0_PITCH_EXT',0x3274)
EGL_DMA_BUF_PLANE1_FD_EXT=_C('EGL_DMA_BUF_PLANE1_FD_EXT',0x3275)
EGL_DMA_BUF_PLANE1_OFFSET_EXT=_C('EGL_DMA_BUF_PLANE1_OFFSET_EXT',0x3276)
EGL_DMA_BUF_PLANE1_PITCH_EXT=_C('EGL_DMA_BUF_PLANE1_PITCH_EXT',0x3277)
EGL_DMA_BUF_PLANE2_FD_EXT=_C('EGL_DMA_BUF_PLANE2_FD_EXT',0x3278)
EGL_DMA_BUF_PLANE2_OFFSET_EXT=_C('EGL_DMA_BUF_PLANE2_OFFSET_EXT',0x3279)
EGL_DMA_BUF_PLANE2_PITCH_EXT=_C('EGL_DMA_BUF_PLANE2_PITCH_EXT',0x327A)
EGL_YUV_COLOR_SPACE_HINT_EXT=_C('EGL_YUV_COLOR_SPACE_HINT_EXT',0x327B)
EGL_SAMPLE_RANGE_HINT_EXT=_C('EGL_SAMPLE_RANGE_HINT_EXT',0x327C)
EGL_YUV_CHROMA_HORIZONTAL_SITING_HINT_EXT=_C('EGL_YUV_CHROMA_HORIZONTAL_SITING_HINT_EXT',0x327D)
EGL_YUV_CHROMA_VERTICAL_SITING_HINT_EXT=_C('EGL_YUV_CHROMA_VERTICAL_SITING_HINT_EXT',0x327E)
EGL_ITU_REC601_EXT=_C('EGL_ITU_REC601_EXT',0x327F)
EGL_ITU_REC709_EXT=_C('EGL_ITU_REC709_EXT',0x3280)
EGL_ITU_REC2020_EXT=_C('EGL_ITU_REC2020_EXT',0x3281)
EGL_YUV_FULL_RANGE_EXT=_C('EGL_YUV_FULL_RANGE_EXT',0x3282)
EGL_YUV_NARROW_RANGE_EXT=_C('EGL_YUV_NARROW_RANGE_EXT',0x3283)
EGL_YUV_CHROMA_SITING_0_EXT=_C('EGL_YUV_CHROMA_SITING_0_EXT',0x3284)
EGL_YUV_CHROMA_SITING_0_5_EXT=_C('EGL_YUV_CHROMA_SITING_0_5_EXT',0x3285)
EGL_MESA_screen_surface=_C('EGL_MESA_screen_surface',1)
EGL_BAD_SCREEN_MESA=_C('EGL_BAD_SCREEN_MESA',0x4000)
EGL_BAD_MODE_MESA=_C('EGL_BAD_MODE_MESA',0x4001)
EGL_SCREEN_COUNT_MESA=_C('EGL_SCREEN_COUNT_MESA',0x4002)
EGL_SCREEN_POSITION_MESA=_C('EGL_SCREEN_POSITION_MESA',0x4003)
EGL_SCREEN_POSITION_GRANULARITY_MESA=_C('EGL_SCREEN_POSITION_GRANULARITY_MESA',0x4004)
EGL_MODE_ID_MESA=_C('EGL_MODE_ID_MESA',0x4005)
EGL_REFRESH_RATE_MESA=_C('EGL_REFRESH_RATE_MESA',0x4006)
EGL_OPTIMAL_MESA=_C('EGL_OPTIMAL_MESA',0x4007)
EGL_INTERLACED_MESA=_C('EGL_INTERLACED_MESA',0x4008)
EGL_SCREEN_BIT_MESA=_C('EGL_SCREEN_BIT_MESA',0x08)
EGL_MESA_copy_context=_C('EGL_MESA_copy_context',1)
EGL_MESA_drm_display=_C('EGL_MESA_drm_display',1)
EGL_DRM_BUFFER_USE_CURSOR_MESA=_C('EGL_DRM_BUFFER_USE_CURSOR_MESA',0x0004)
EGL_WL_bind_wayland_display=_C('EGL_WL_bind_wayland_display',1)
EGL_WAYLAND_BUFFER_WL=_C('EGL_WAYLAND_BUFFER_WL',0x31D5)
EGL_NOK_swap_region=_C('EGL_NOK_swap_region',1)
EGL_NOK_texture_from_pixmap=_C('EGL_NOK_texture_from_pixmap',1)
EGL_Y_INVERTED_NOK=_C('EGL_Y_INVERTED_NOK',0x307F)
EGL_ANDROID_image_native_buffer=_C('EGL_ANDROID_image_native_buffer',1)
EGL_NATIVE_BUFFER_ANDROID=_C('EGL_NATIVE_BUFFER_ANDROID',0x3140)
@_f
@_p.types(_cs.EGLint,)
def eglGetError():pass
@_f
@_p.types(_cs.EGLDisplay,_cs.EGLNativeDisplayType)
def eglGetDisplay(display_id):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,arrays.GLintArray,arrays.GLintArray)
def eglInitialize(dpy,major,minor):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay)
def eglTerminate(dpy):pass
@_f
@_p.types(arrays.GLbyteArray,_cs.EGLDisplay,_cs.EGLint)
def eglQueryString(dpy,name):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,arrays.GLvoidpArray,_cs.EGLint,arrays.GLintArray)
def eglGetConfigs(dpy,configs,config_size,num_config):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,arrays.GLintArray,arrays.GLvoidpArray,_cs.EGLint,arrays.GLintArray)
def eglChooseConfig(dpy,attrib_list,configs,config_size,num_config):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLConfig,_cs.EGLint,arrays.GLintArray)
def eglGetConfigAttrib(dpy,config,attribute,value):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,_cs.EGLNativeWindowType,arrays.GLintArray)
def eglCreateWindowSurface(dpy,config,win,attrib_list):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,arrays.GLintArray)
def eglCreatePbufferSurface(dpy,config,attrib_list):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,_cs.EGLNativePixmapType,arrays.GLintArray)
def eglCreatePixmapSurface(dpy,config,pixmap,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface)
def eglDestroySurface(dpy,surface):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint,arrays.GLintArray)
def eglQuerySurface(dpy,surface,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLenum)
def eglBindAPI(api):pass
@_f
@_p.types(_cs.EGLenum,)
def eglQueryAPI():pass
@_f
@_p.types(_cs.EGLBoolean,)
def eglWaitClient():pass
@_f
@_p.types(_cs.EGLBoolean,)
def eglReleaseThread():pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLenum,_cs.EGLClientBuffer,_cs.EGLConfig,arrays.GLintArray)
def eglCreatePbufferFromClientBuffer(dpy,buftype,buffer,config,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint,_cs.EGLint)
def eglSurfaceAttrib(dpy,surface,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint)
def eglBindTexImage(dpy,surface,buffer):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint)
def eglReleaseTexImage(dpy,surface,buffer):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLint)
def eglSwapInterval(dpy,interval):pass
@_f
@_p.types(_cs.EGLContext,_cs.EGLDisplay,_cs.EGLConfig,_cs.EGLContext,arrays.GLintArray)
def eglCreateContext(dpy,config,share_context,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLContext)
def eglDestroyContext(dpy,ctx):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLSurface,_cs.EGLContext)
def eglMakeCurrent(dpy,draw,read,ctx):pass
@_f
@_p.types(_cs.EGLContext,)
def eglGetCurrentContext():pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLint)
def eglGetCurrentSurface(readdraw):pass
@_f
@_p.types(_cs.EGLDisplay,)
def eglGetCurrentDisplay():pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLContext,_cs.EGLint,arrays.GLintArray)
def eglQueryContext(dpy,ctx,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,)
def eglWaitGL():pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLint)
def eglWaitNative(engine):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface)
def eglSwapBuffers(dpy,surface):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLNativePixmapType)
def eglCopyBuffers(dpy,surface,target):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,arrays.GLintArray)
def eglLockSurfaceKHR(display,surface,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface)
def eglUnlockSurfaceKHR(display,surface):pass
@_f
@_p.types(_cs.EGLImageKHR,_cs.EGLDisplay,_cs.EGLContext,_cs.EGLenum,_cs.EGLClientBuffer,arrays.GLintArray)
def eglCreateImageKHR(dpy,ctx,target,buffer,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLImageKHR)
def eglDestroyImageKHR(dpy,image):pass
@_f
@_p.types(_cs.EGLSyncKHR,_cs.EGLDisplay,_cs.EGLenum,arrays.GLintArray)
def eglCreateSyncKHR(dpy,type,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSyncKHR)
def eglDestroySyncKHR(dpy,sync):pass
@_f
@_p.types(_cs.EGLint,_cs.EGLDisplay,_cs.EGLSyncKHR,_cs.EGLint,_cs.EGLTimeKHR)
def eglClientWaitSyncKHR(dpy,sync,flags,timeout):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSyncKHR,_cs.EGLenum)
def eglSignalSyncKHR(dpy,sync,mode):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSyncKHR,_cs.EGLint,arrays.GLintArray)
def eglGetSyncAttribKHR(dpy,sync,attribute,value):pass
@_f
@_p.types(_cs.EGLSyncNV,_cs.EGLDisplay,_cs.EGLenum,arrays.GLintArray)
def eglCreateFenceSyncNV(dpy,condition,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLSyncNV)
def eglDestroySyncNV(sync):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLSyncNV)
def eglFenceNV(sync):pass
@_f
@_p.types(_cs.EGLint,_cs.EGLSyncNV,_cs.EGLint,_cs.EGLTimeNV)
def eglClientWaitSyncNV(sync,flags,timeout):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLSyncNV,_cs.EGLenum)
def eglSignalSyncNV(sync,mode):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLSyncNV,_cs.EGLint,arrays.GLintArray)
def eglGetSyncAttribNV(sync,attribute,value):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,ctypes.POINTER(_cs.EGLClientPixmapHI))
def eglCreatePixmapSurfaceHI(dpy,config,pixmap):pass
@_f
@_p.types(_cs.EGLImageKHR,_cs.EGLDisplay,arrays.GLintArray)
def eglCreateDRMImageMESA(dpy,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLImageKHR,arrays.GLintArray,arrays.GLintArray,arrays.GLintArray)
def eglExportDRMImageMESA(dpy,image,name,handle,stride):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint,_cs.EGLint,_cs.EGLint,_cs.EGLint)
def eglPostSubBufferNV(dpy,surface,x,y,width,height):pass
@_f
@_p.types(_cs.EGLuint64NV,)
def eglGetSystemTimeFrequencyNV():pass
@_f
@_p.types(_cs.EGLuint64NV,)
def eglGetSystemTimeNV():pass
@_f
@_p.types(_cs.EGLStreamKHR,_cs.EGLDisplay,arrays.GLintArray)
def eglCreateStreamKHR(dpy,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR)
def eglDestroyStreamKHR(dpy,stream):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR,_cs.EGLenum,_cs.EGLint)
def eglStreamAttribKHR(dpy,stream,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR,_cs.EGLenum,arrays.GLintArray)
def eglQueryStreamKHR(dpy,stream,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR,_cs.EGLenum,arrays.GLuint64Array)
def eglQueryStreamu64KHR(dpy,stream,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR)
def eglStreamConsumerGLTextureExternalKHR(dpy,stream):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR)
def eglStreamConsumerAcquireKHR(dpy,stream):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR)
def eglStreamConsumerReleaseKHR(dpy,stream):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,_cs.EGLStreamKHR,arrays.GLintArray)
def eglCreateStreamProducerSurfaceKHR(dpy,config,stream,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLStreamKHR,_cs.EGLenum,arrays.GLuint64Array)
def eglQueryStreamTimeKHR(dpy,stream,attribute,value):pass
@_f
@_p.types(_cs.EGLNativeFileDescriptorKHR,_cs.EGLDisplay,_cs.EGLStreamKHR)
def eglGetStreamFileDescriptorKHR(dpy,stream):pass
@_f
@_p.types(_cs.EGLStreamKHR,_cs.EGLDisplay,_cs.EGLNativeFileDescriptorKHR)
def eglCreateStreamFromFileDescriptorKHR(dpy,file_descriptor):pass
@_f
@_p.types(_cs.EGLint,_cs.EGLDisplay,_cs.EGLSyncKHR,_cs.EGLint)
def eglWaitSyncKHR(dpy,sync,flags):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,arrays.GLvoidpArray)
def eglQueryNativeDisplayNV(dpy,display_id):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,arrays.GLvoidpArray)
def eglQueryNativeWindowNV(dpy,surf,window):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,arrays.GLvoidpArray)
def eglQueryNativePixmapNV(dpy,surf,pixmap):pass
@_f
@_p.types(None,_cs.EGLDisplay,_cs.EGLSetBlobFuncANDROID,_cs.EGLGetBlobFuncANDROID)
def eglSetBlobCacheFuncsANDROID(dpy,set,get):pass
@_f
@_p.types(_cs.EGLint,_cs.EGLDisplay,_cs.EGLSyncKHR)
def eglDupNativeFenceFDANDROID(dpy,sync):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,arrays.GLintArray,ctypes.POINTER(_cs.EGLModeMESA),_cs.EGLint,arrays.GLintArray)
def eglChooseModeMESA(dpy,screen,attrib_list,modes,modes_size,num_modes):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,ctypes.POINTER(_cs.EGLModeMESA),_cs.EGLint,arrays.GLintArray)
def eglGetModesMESA(dpy,screen,modes,modes_size,num_modes):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLModeMESA,_cs.EGLint,arrays.GLintArray)
def eglGetModeAttribMESA(dpy,mode,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,ctypes.POINTER(_cs.EGLScreenMESA),_cs.EGLint,arrays.GLintArray)
def eglGetScreensMESA(dpy,screens,max_screens,num_screens):pass
@_f
@_p.types(_cs.EGLSurface,_cs.EGLDisplay,_cs.EGLConfig,arrays.GLintArray)
def eglCreateScreenSurfaceMESA(dpy,config,attrib_list):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLint,_cs.EGLSurface,_cs.EGLModeMESA)
def eglShowScreenSurfaceMESA(dpy,screen,surface,mode):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,_cs.EGLint,_cs.EGLint)
def eglScreenPositionMESA(dpy,screen,x,y):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,_cs.EGLint,arrays.GLintArray)
def eglQueryScreenMESA(dpy,screen,attribute,value):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,ctypes.POINTER(_cs.EGLSurface))
def eglQueryScreenSurfaceMESA(dpy,screen,surface):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLScreenMESA,ctypes.POINTER(_cs.EGLModeMESA))
def eglQueryScreenModeMESA(dpy,screen,mode):pass
@_f
@_p.types(arrays.GLbyteArray,_cs.EGLDisplay,_cs.EGLModeMESA)
def eglQueryModeStringMESA(dpy,mode):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLContext,_cs.EGLContext,_cs.EGLint)
def eglCopyContextMESA(dpy,source,dest,mask):pass
@_f
@_p.types(_cs.EGLDisplay,_cs.c_int)
def eglGetDRMDisplayMESA(fd):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,ctypes.POINTER(_cs.wl_display))
def eglBindWaylandDisplayWL(dpy,display):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,ctypes.POINTER(_cs.wl_display))
def eglUnbindWaylandDisplayWL(dpy,display):pass
@_f
@_p.types(_cs.EGLBoolean,_cs.EGLDisplay,_cs.EGLSurface,_cs.EGLint,arrays.GLintArray)
def eglSwapBuffersRegionNOK(dpy,surface,numRects,rects):pass

del ctypes 
del arrays 
