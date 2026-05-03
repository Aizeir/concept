from ursina import *

with open("shaders/world.vert", "r") as file: vert = file.read()
with open("shaders/def.vert", "r") as file: avert = file.read()
with open("shaders/world.frag", "r") as file: frag = file.read()
with open("shaders/water.frag", "r") as file: wfrag = file.read()
with open("shaders/cam.frag", "r") as file: cfrag = file.read()
with open("shaders/def.frag", "r") as file: afrag = file.read()

shader = Shader(
    language=Shader.GLSL,
    vertex=vert,
    fragment=frag,
)
water_shader = Shader(
    language=Shader.GLSL,
    vertex=vert,
    fragment=wfrag,
)
cam_shader = Shader(
    language=Shader.GLSL,
    fragment=cfrag,
)
animal_shader = Shader(
    language=Shader.GLSL,
    vertex=avert,
    fragment=afrag,
)


light_direction = Vec3(0.21, 0.71, 0.07)