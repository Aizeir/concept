from ursina import *

with open("shaders/world.vert", "r") as file: vert = file.read()
with open("shaders/world.frag", "r") as file: frag = file.read()
with open("shaders/water.frag", "r") as file: wfrag = file.read()
with open("shaders/cam.frag", "r") as file: cfrag = file.read()

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

light_direction = Vec3(0.21, 0.71, 0.07)