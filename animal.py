from random import randint

from blocks import AIR
from physics import Physics
from settings import *
from direct.actor.Actor import Actor
from ursina.shaders import basic_lighting_shader
from shader import animal_shader
import math
from pygame.math import Vector2 as vec2

def norm(v):
    return (v.x**2+v.y**2+v.z**2)**.5
def normalize(v):
    if norm(v) > 0: return v / norm(v)
    else: return v

class Animal(Physics):
    def __init__(self, world, position, animal):
        self.world = world
        self.type = animal

        super().__init__(world.game,
            parent=world.all_animals,
            position=position,
            size=Vec3(.5,1,.5),
            shader=animal_shader,
            collider="box"
        )

        path = f"assets/models/{animal}.glb"
        self.actor = Actor(path, {
            "move": path,
            "eat": path,
        })
        self.actor.reparentTo(self)
        self.actor.setBlend(frameBlend=True)
        
        self.t = 0
        self.current_anim = "move"
        self.actor.loop("move")
        self.leg0 = self.actor.controlJoint(None, "modelRoot", "leg0")
        self.leg1 = self.actor.controlJoint(None, "modelRoot", "leg1")
        self.leg2 = self.actor.controlJoint(None, "modelRoot", "leg2")
        self.leg3 = self.actor.controlJoint(None, "modelRoot", "leg3")
        self.speed = 2
        self.moving = False
        self.change_direction()

    def change_direction(self):
        if not self.moving:
            self.direction = vec2(1,0).rotate(randint(0,359))
            self.move_timer = (time.time(), randint(5,15))
            self.moving = True
        else:
            self.move_timer = (time.time(), randint(5,15))
            self.moving = False

    def animate(self, anim):
        match anim:
            case "move":
                self.t += time.dt * 6
                angle = math.sin(self.t) * 30
                self.leg0.setP(angle)
                self.leg1.setP(-angle)
                self.leg2.setP(-angle)
                self.leg3.setP(angle)
            case "idle":
                self.leg0.setP(0)
                self.leg1.setP(0)
                self.leg2.setP(0)
                self.leg3.setP(0)

    def update(self):
        # Timers
        if time.time() - self.move_timer[0] > self.move_timer[1]:
            self.change_direction()
        if self.moving:
            v = self.direction
            a = math.atan2(v.y,v.x)*180/math.pi
            self.world_rotation_y_setter(90-a)

            self.velocity.xz_setter(v * self.speed)
            self.animate("move")
        else:
            self.velocity.xz_setter((0,0))
            self.animate("idle")

        # Gravity
        if self.underwater:
            self.velocity.y = max(self.velocity.y - self.water_gravity, -self.water_gravity_max)
        else:
            self.velocity.y -= self.gravity

        dv = self.velocity * min(0.1, time.dt)

        # Collisions
        bx,bz = self.collisions(Vec3(dv.x, 0, 0)), self.collisions(Vec3(0, 0, dv.z))
        if bx:
            self.velocity.x = 0
        else:
            self.position += Vec3(dv.x, 0, 0)

        if bz:
            self.velocity.z = 0
        else:
            self.position += Vec3(0, 0, dv.z)

        self.grounded = False
        if self.collisions(Vec3(0, dv.y, 0)):
            self.velocity.y = 0
        else:
            self.position += Vec3(0,dv.y,0)

        do_jump = len(bx+bz)>0
        cow_y = self.block[1]
        for x,y,z in bx+bz:
            if y == cow_y and self.world.get_block(x,y+1,z) != AIR:
                do_jump = False

        if do_jump and self.grounded:
            self.jump() 