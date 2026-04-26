from settings import *
from ursina import *


hotbar = load_texture("assets/inventory.png")
hotbar_size = hotbar.size_getter()
hotbar_scale = .5


def rel_pos(parent_size, pos, size, z=0):
    pos, size, parent_size = Vec2(pos),Vec2(size),Vec2(parent_size)
    return Vec3((pos+size/2) / parent_size - Vec2(.5), -z)

def rel_size(parent_size, size):
    size, parent_size = Vec2(size),Vec2(parent_size)
    return size / parent_size

class HUD:
    def __init__(self,game):
        self.game = game
        self.player = game.player


        self.hotbar = Entity(
            parent=camera.ui,
            model="quad",
            texture=hotbar,
            scale=(hotbar_scale, (hotbar_size[1]/hotbar_size[0])*hotbar_scale),
            position=(0,-.4)
        )
        
        slots = load_texture("assets/atlas.png")
        self.slots = [
            Entity(
                parent=self.hotbar,
                model="quad",
                texture=slots,
                texture_scale=Vec2(1)/atlas_size,
                texture_offset=(0,0),
                scale=rel_size(hotbar_size, (8,8)),
                position=rel_pos(hotbar_size, (2+i*9, 2), (8,8), 1),
            )
            for i in range(INV_SIZE)
        ]

        self.inv_cache = None

        self.selector = Entity(
            parent=self.hotbar,
            model="quad",
            color=color.rgba(0,0,0,.5),
            scale=rel_size(hotbar_size, (10,10)),
        )

    def update(self):
        if self.player.inventory != self.inv_cache:
            self.inv_cache = self.player.inventory.copy()

            for i in range(INV_SIZE):
                block, amt = self.inv_cache[i]
                self.slots[i].texture_offset = Vec2(block.tex_coords[FFRONT])/atlas_size

        self.selector.position_setter(rel_pos(hotbar_size, (1+self.player.slot*9, 1), (10,10), .5))
