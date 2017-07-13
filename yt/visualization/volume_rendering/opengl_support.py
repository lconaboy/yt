# encoding: utf-8
"""
Shader and ShaderProgram wrapper classes for vertex and fragment shaders used 
in Interactive Data Visualization
"""

# ----------------------------------------------------------------------------
# Copyright (c) 2016, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

# This is a part of the experimental Interactive Data Visualization 

import OpenGL.GL as GL
from contextlib import contextmanager
import traitlets
import numpy as np

# Set up a mapping from numbers to names

const_types = (GL.constant.IntConstant,
               GL.constant.LongConstant,
               GL.constant.FloatConstant)

num_to_const = {}
for i in dir(GL):
    if i.startswith("GL_"):
        v = getattr(GL, i)
        if not isinstance(v, const_types): continue
        num_to_const[v.real] = v

_coersion_funcs = {
        'FLOAT': float,
        'DOUBLE': float,
        'INT': int,
        'UNSIGNED': int,
        'BOOL': bool
}

_shapes = {
        'MAT2'   : (2, 2),
        'MAT3'   : (3, 3),
        'MAT4'   : (4, 4),
        'MAT2x3' : (2, 3),
        'MAT2x4' : (2, 4),
        'MAT3x2' : (3, 2),
        'MAT3x4' : (3, 4),
        'MAT4x2' : (4, 2),
        'MAT4x3' : (4, 3),
        'VEC2'   : (2,),
        'VEC3'   : (3,),
        'VEC4'   : (4,),
}

# PyOpenGL has the reverse mapping for this
gl_to_np = {
        'FLOAT'    : 'f',
        'DOUBLE'   : 'd',
        'INT'      : 'i',
        'UNSIGNED' : 'I',
        'BOOL'     : 'b',
}

def coerce_uniform_type(val, gl_type):
    # gl_type here must be in const_types
    if not isinstance(gl_type, const_types):
        gl_type = num_to_const[gl_type]
    # Now we can get down to business!
    spec = gl_type.name.split("_")[1:] # Strip out the GL_
    # We know what to do with:
    #   FLOAT DOUBLE INT UNSIGNED BOOL
    # We can ignore:
    #    SAMPLER IMAGE 
    if "SAMPLER" in spec or "IMAGE" in spec:
        # Do nothing to these, and let PyOpenGL handle it
        return val
    if len(spec) == 1 or spec == ['UNSIGNED', 'INT']:
        return _coersion_funcs[spec[0]](val)
    # We need to figure out if it's a matrix, a vector, etc.
    shape = _shapes[spec[-1]]
    dtype = gl_to_np[spec[0]]
    val = np.asanyarray(val, dtype = dtype)
    val.shape = shape
    return val

class TextureBoundary(traitlets.TraitType):
    default_value = GL.GL_CLAMP_TO_EDGE
    info_text = "A boundary type of mirror, clamp, or repeat"

    def validate(self, obj, value):
        if isinstance(value, str):
            try:
                return {'clamp': GL.GL_CLAMP_TO_EDGE,
                        'mirror': GL.GL_MIRRORED_REPEAT,
                        'repeat': GL.GL_REPEAT}[value.lower()]
            except KeyError:
                self.error(obj, value)
        elif value in (GL.GL_CLAMP_TO_EDGE,
                       GL.GL_MIRRORED_REPEAT,
                       GL.GL_REPEAT):
            return value
        self.error(obj, value)

class Texture(traitlets.HasTraits):
    texture_name = traitlets.CInt(-1)
    data = traitlets.Instance(np.ndarray)

    @traitlets.default('texture_name')
    def _default_texture_name(self):
        return GL.glGenTextures(1)

    @contextmanager
    def bind(self):
        GL.glBindTexture(self.dim_enum, self.texture_name)
        yield
        GL.glBindTexture(self.dim_enum, 0)

class Texture1D(Texture):
    boundary_x = TextureBoundary()
    dims = 1
    dim_enum = GL.GL_TEXTURE_1D

    @traitlets.observe("data")
    def _set_data(self, change):
        with self.bind():
            dx, = change['new'].shape
            GL.glTexStorage1D(GL.GL_TEXTURE_1D, 1, GL.GL_R32F,
                    *change['new'].shape)
            GL.glTexSubImage1D(GL.GL_TEXTURE_1D, 0, 0, dx,
                        GL.GL_RED, GL.GL_FLOAT, 
                        change['new'])
            GL.glTexParameterf(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S,
                    self.boundary_x)
            GL.glGenerateMipmap(GL.GL_TEXTURE_1D)


class Texture2D(Texture):
    boundary_x = TextureBoundary()
    boundary_y = TextureBoundary()
    dims = 2
    dim_enum = GL.GL_TEXTURE_2D

    @traitlets.observe("data")
    def _set_data(self, change):
        with self.bind():
            dx, dy = change['new'].shape
            GL.glTexStorage2D(GL.GL_TEXTURE_2D, 1, GL.GL_R32F,
                    *change['new'].shape)
            GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, dx, dy, 
                        GL.GL_RED, GL.GL_FLOAT,
                        change['new'].T)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                    self.boundary_x)
            GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                    self.boundary_y)
            GL.glGenerateMipmap(GL.GL_TEXTURE_2D)

class Texture3D(Texture):
    boundary_x = TextureBoundary()
    boundary_y = TextureBoundary()
    boundary_z = TextureBoundary()
    dims = 3
    dim_enum = GL.GL_TEXTURE_3D

    @traitlets.observe("data")
    def _set_data(self, change):
        with self.bind():
            dx, dy, dz = change['new'].shape
            GL.glTexStorage3D(GL.GL_TEXTURE_3D, 1, GL.GL_R32F,
                    *change['new'].shape)
            GL.glTexSubImage3D(GL.GL_TEXTURE_3D, 0, 0, 0, 0, dx, dy, dz,
                        GL.GL_RED, GL.GL_FLOAT, 
                        change['new'].T)
            GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S,
                    self.boundary_x)
            GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T,
                    self.boundary_y)
            GL.glTexParameterf(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R,
                    self.boundary_z)
            GL.glGenerateMipmap(GL.GL_TEXTURE_3D)
