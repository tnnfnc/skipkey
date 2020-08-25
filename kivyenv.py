# -*- coding: utf-8 -*-
"""
KIVY environment variables:
    define variables before importing kivy module!
"""
import os
import kivy
kivy.require('1.11.0')

def setenv(var, value):
    os.environ[var.upper()] = value


'''If set, the SDL2 libraries and headers from this path are used when compiling kivy instead of the ones installed system-wide. To use the same libraries while running a kivy app, this path must be added at the start of the PATH environment variable.'''
# KIVY_SDL2_PATH

# AND NOW....
# =============================================================================
# import kivy
# =============================================================================


# # Kivy uses OpenGL and therefore requires a backend that provides it. The
# # backend used is controlled through the USE_OPENGL_MOCK and USE_SDL2
# # compile-time variables and through the KIVY_GL_BACKEND runtime
# # environmental variable.

# os.environ['KIVY_GL_BACKEND']
# # KIVY_GL_BACKEND
# # Implementation to use for creating the Window
# # Values: sdl2, pygame, x11, egl_rpi

# os.environ['KIVY_WINDOW']
# #
# #
# # Implementation to use for rendering text
# # Values: sdl2, pil, pygame, sdlttf

# os.environ['KIVY_TEXT']  # KIVY_TEXT
# #
# #
# # Implementation to use for rendering video
# # Values: gstplayer, ffpyplayer, ffmpeg, null
# os.environ['KIVY_VIDEO']  # KIVY_VIDEO
# #
# #
# # Implementation to use for playing audio
# # Values: sdl2, gstplayer, ffpyplayer, pygame, avplayer
# os.environ['KIVY_AUDIO']  # KIVY_AUDIO
# #
# #
# # Implementation to use for reading image
# # Values: sdl2, pil, pygame, imageio, tex, dds, gif
# os.environ['KIVY_IMAGE']  # KIVY_IMAGE
#
#
# Implementation to use for reading camera
# Values: avfoundation, android, opencv
#value = 'sdl2'
# os.environ['KIVY_CAMERA'] = value #KIVY_CAMERA
#
#
# Implementation to use for spelling
# Values: enchant, osxappkit
#value = 'sdl2'
# os.environ['KIVY_SPELLING'] = value #KIVY_SPELLING
#
#
# Implementation to use for clipboard management
# Values: sdl2, pygame, dummy, android

 # KIVY_CLIPBOARD
#

env_defaults = [
    os.environ.get('KIVY_CLIPBOARD', ''),
    os.environ.get('KIVY_GL_BACKEND', ''),
    os.environ.get('KIVY_WINDOW', ''),
    os.environ.get('KIVY_TEXT', ''),
    os.environ.get('KIVY_VIDEO', ''),
    os.environ.get('KIVY_AUDIO', ''),
    os.environ.get('KIVY_IMAGE', ''),
    os.environ.get('KIVY_CAMERA', ''),
    os.environ.get('KIVY_SPELLING', ''),
    os.environ.get('KIVY_CLIPBOARD', '')]

print(env_defaults)
