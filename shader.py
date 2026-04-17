from ursina import *

with open("shader.vert", "r") as file:
    vert = file.read()
with open("shader.frag", "r") as file:
    frag = file.read()

shader = Shader(
    language=Shader.GLSL,
    vertex=vert,
    fragment=frag,
)


light_direction = Vec3(0.21, 0.71, 0.07)