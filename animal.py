from physics import Physics
from settings import *
from direct.actor.Actor import Actor
from ursina.shaders import basic_lighting_shader

class Animal(Physics):
    def __init__(self, world, position, animal):
        self.world = world
        self.type = animal

        super().__init__(world.game,
            parent=world.animals,
            position=position,
            size=Vec3(.5,1,.5),
            shader=basic_lighting_shader
        )

        self.actor = Actor(f'assets/models/{animal}.gltf')
        self.actor.reparent_to(self)
        self.actor.loop('move')