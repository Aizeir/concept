from threading import Thread
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from player import Player
from world import *
from ursina.shaders.basic_lighting_shader import basic_lighting_shader
from settings import *


app = Ursina()

class Game:
    def __init__(self):
        # Lighting
        self.sky = Sky(color=color.rgb(100/255, 160/255, 255/255), texture=None)
        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(1, -2, 1))
        self.ambient_light = AmbientLight()
        self.ambient_light.color = color.rgba(150, 150, 150, 255)
        # World
        self.world = World(self)
        self.all_colliders = []

        # Player
        self.player = Player(self, position=(0,20,0))
        self.world.player = self.player
        self.player_last_chunk = None
        self.cursor = Entity(parent=camera.ui, model='quad', texture="assets/cursor", scale=.05)

        self.update_colliders()


    def update_colliders(self): 
        for e in self.all_colliders: destroy(e)
        self.all_colliders.clear()

        px, py, pz = floor(self.player.x), floor(self.player.y), floor(self.player.z)

        # Collisions
        for dx in range(-2,3):
            for dy in range(-3,3):
                for dz in range(-2,3):
                    wx, wy, wz = px+dx, py+dy, pz+dz
                    if self.world.get_block(wx, wy, wz) != AIR:
                        self.all_colliders.append(Entity(
                            parent=self.player.block_colliders,
                            position=Vec3(wx+.5, wy+.5, wz+.5),
                            collider='box',
                            visible=False,
                            # color = color.black,
                            # model="cube"
                        ))

    def update(self):
        # Update chunks
        chunk = Vec3(self.player.chunk)
        if chunk != self.player_last_chunk:
            self.player_last_chunk = chunk

            # d'abord clear les vbo ou jsp quoi
            for dcx in range(2*RENDER_DISTANCE_XZ+1):
                for dcy in range(2*RENDER_DISTANCE_Y+1):
                    for dcz in range(2*RENDER_DISTANCE_XZ+1):
                        self.world.reload_chunk(dcx,dcy,dcz, True)
                        
            for dcx in range(2*RENDER_DISTANCE_XZ+1):
                for dcy in range(2*RENDER_DISTANCE_Y+1):
                    for dcz in range(2*RENDER_DISTANCE_XZ+1):
                        self.world.reload_chunk(dcx,dcy,dcz, False)

        # Update colliders
        self.update_colliders()

game = Game()
def update(): game.update()
app.run()