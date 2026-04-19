from threading import Thread
from ursina import *
from player import Player
from world import *
from settings import *
from panda3d.core import Shader, Texture
from direct.filter.FilterManager import FilterManager

app = Ursina()

class Game:
    def __init__(self):
        # Lighting
        self.sky = Sky(color=color.rgb(100/255, 160/255, 255/255), texture="sky_sunset.jpg")
        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(1, -2, 1))
        self.ambient_light = AmbientLight()
        self.ambient_light.color = color.rgba(150, 150, 150, 255)

        # World
        self.world = World(self)
        self.all_colliders = []

        # Player
        self.player = Player(self, position=(0,MAX_GEN_HEIGHT+1,0))
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
                    if self.world.get_block(wx, wy, wz).type == BT_SOLID:
                        self.all_colliders.append(Entity(
                            parent=self.player.block_colliders,
                            position=Vec3(wx+.5, wy+.5, wz+.5),
                            collider='box',
                            visible=False,
                            # color = color.black,
                            # model="cube"
                        ))

    def update(self, finalquad):
        # Update chunks
        chunk = Vec2(self.player.chunk)
        if chunk != self.player_last_chunk:
            self.player_last_chunk = chunk
            self.world.update_chunks()

        # Update colliders
        self.update_colliders()

        # Update uniforms
        if self.player.selection:
            self.world.all_chunks.set_shader_input("selection", (*self.player.selection[0], 1))
            self.world.all_waters.set_shader_input("selection", (*self.player.selection[0], 1))
        else:
            self.world.all_chunks.set_shader_input("selection", (0,0,0,0))
            self.world.all_waters.set_shader_input("selection", (0,0,0,0))
        finalquad.setShaderInput("underwater",self.player.underwater)

game = Game()

# post process
manager = FilterManager(app.win, app.cam)
tex = Texture()
finalquad = manager.renderSceneInto(colortex=tex)
finalquad.setShader(Shader.load(
    Shader.SL_GLSL,
    vertex="shaders/cam.vert",
    fragment="shaders/cam.frag"
))
finalquad.setShaderInput("tex", tex)

# update
def update():
    game.update(finalquad)
def input(key):
    if key=="tab": game.player.fly = not game.player.fly

app.run()