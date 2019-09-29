# -*- coding: utf-8 -*-
"""
KIVY environment variables:
    define variables before importing kivy module!
"""
import os

def setenv(var, value):
    os.environ[var.upper()] = value

'''If set, the SDL2 libraries and headers from this path are used when compiling kivy instead of the ones installed system-wide. To use the same libraries while running a kivy app, this path must be added at the start of the PATH environment variable.'''
#KIVY_SDL2_PATH

# AND NOW....
# =============================================================================
# import kivy
# =============================================================================



# Kivy uses OpenGL and therefore requires a backend that provides it. The
#backend used is controlled through the USE_OPENGL_MOCK and USE_SDL2
#compile-time variables and through the KIVY_GL_BACKEND runtime
#environmental variable.
value = 'glew'#'sdl2' 'angle_sdl2' 'glew'
os.environ['KIVY_GL_BACKEND'] = value
#KIVY_GL_BACKEND
#Implementation to use for creating the Window
#Values: sdl2, pygame, x11, egl_rpi
value = 'sdl2'
os.environ['KIVY_WINDOW'] = value
#
#
#Implementation to use for rendering text
#Values: sdl2, pil, pygame, sdlttf
value = 'sdl2'
os.environ['KIVY_TEXT'] = value #KIVY_TEXT
#
#
#Implementation to use for rendering video
#Values: gstplayer, ffpyplayer, ffmpeg, null
value = 'null'
os.environ['KIVY_VIDEO'] = value #KIVY_VIDEO
#
#
#Implementation to use for playing audio
#Values: sdl2, gstplayer, ffpyplayer, pygame, avplayer
value = 'sdl2'
os.environ['KIVY_AUDIO'] = value #KIVY_AUDIO
#
#
#Implementation to use for reading image
#Values: sdl2, pil, pygame, imageio, tex, dds, gif
value = 'sdl2'
os.environ['KIVY_IMAGE'] = value #KIVY_IMAGE
#
#
#Implementation to use for reading camera
#Values: avfoundation, android, opencv
#value = 'sdl2'
#os.environ['KIVY_CAMERA'] = value #KIVY_CAMERA
#
#
#Implementation to use for spelling
#Values: enchant, osxappkit
#value = 'sdl2'
#os.environ['KIVY_SPELLING'] = value #KIVY_SPELLING
#
#
#Implementation to use for clipboard management
#Values: sdl2, pygame, dummy, android
value = 'sdl2'
os.environ['KIVY_CLIPBOARD'] = value #KIVY_CLIPBOARD
#
print('loaded environment')
env_defaults = [#os.environ['KIVY_GL_BACKEND'],
os.environ['KIVY_WINDOW'],
os.environ['KIVY_TEXT'],
os.environ['KIVY_VIDEO'],
os.environ['KIVY_AUDIO'],
os.environ['KIVY_IMAGE'],
#os.environ['KIVY_CAMERA'],
#os.environ['KIVY_SPELLING'],
os.environ['KIVY_CLIPBOARD']]

print(env_defaults)