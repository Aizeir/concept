from threading import Thread
from ursina import *
from hud import HUD
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

        # Player
        self.player = Player(self, position=(0,MAX_GEN_HEIGHT+1,0))
        self.world.player = self.player
        self.player_last_chunk = None
        self.cursor = Entity(parent=camera.ui, model='quad', texture="assets/cursor", scale=.05)

        # HUD
        self.hud = HUD(self)

    def update(self, finalquad):
        # Update chunks
        chunk = Vec2(self.player.chunk)
        if chunk != self.player_last_chunk:
            self.player_last_chunk = chunk
            self.world.update_chunks()

        # Update uniforms
        if self.player.selection:
            self.world.all_chunks.set_shader_input("selection", (*self.player.selection[0], self.player.transitions["break"][0]))
            self.world.all_waters.set_shader_input("selection", (*self.player.selection[0], self.player.transitions["break"][0]))
        else:
            self.world.all_chunks.set_shader_input("selection", (0,0,0,-1))
            self.world.all_waters.set_shader_input("selection", (0,0,0,-1))
        finalquad.setShaderInput("underwater",self.player.underwater)

        tod = (1 + sin(time.time() * 6.28 / 300)) / 2
        self.world.all_chunks.set_shader_input("tod", tod)
        self.world.all_waters.set_shader_input("tod", tod)
        self.world.all_animals.set_shader_input("tod", tod)

        # HUD
        self.hud.update()



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
    game.player.input(key)

app.run()