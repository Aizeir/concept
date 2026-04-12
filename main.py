from threading import Thread
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from player import Player
from world import *
from ursina.shaders.basic_lighting_shader import basic_lighting_shader

RENDER_DISTANCE_XZ = 3
RENDER_DISTANCE_Y = 0


app = Ursina()
sky = Sky(color=color.rgb(100/255, 160/255, 255/255), texture=None)

# Les lumières fonctionnent quand même avec basic_lighting_shader
sun = DirectionalLight()
sun.look_at(Vec3(1, -2, 1))
ambient = AmbientLight()
ambient.color = color.rgba(150, 150, 150, 255)

# player
player = Player(position=(0,20,0))
cursor = Entity(parent=camera.ui, model='quad', texture="assets/cursor", scale=.05)


# chunks
plr_chunk = None
chunks = {(dcx,dcy,dcz): Entity(
    model=Mesh(),
    texture="assets/atlas",
    texture_scale=(1/atlas_w,1/atlas_h),
    shader=basic_lighting_shader
)\
for dcz in range(2*RENDER_DISTANCE_XZ+1)
for dcy in range(2*RENDER_DISTANCE_Y+1)
for dcx in range(2*RENDER_DISTANCE_XZ+1)}


def reload_chunk(dcx,dcy,dcz, clear=False, mesh=False):
    c = chunks[dcx,dcy,dcz]
    chunk_pos = (
        plr_chunk.x + dcx-RENDER_DISTANCE_XZ,
        plr_chunk.y + dcy-RENDER_DISTANCE_Y,
        plr_chunk.z + dcz-RENDER_DISTANCE_XZ
    )

    # Clear le VBO (nul ursina)
    if clear:
        c.model = Mesh()
        return
    
    # Si nouveau chunk
    if chunk_pos not in chunk_meshes:
        application.pause() # la génération = couteuse ?
        chunk_contents[chunk_pos] = chunk_procedural(*chunk_pos)
        mesh = Mesh(vertices=[], triangles=[], uvs=[], normals=[])
        chunk_mesh(mesh, chunk_contents[chunk_pos])
        mesh.generate()
        chunk_meshes[chunk_pos] = mesh
        application.resume()

    # Si besoin de recréér
    if mesh:
        application.pause() # la génération = couteuse ?
        mesh = Mesh(vertices=[], triangles=[], uvs=[], normals=[])
        chunk_mesh(mesh, chunk_contents[chunk_pos])
        mesh.generate()
        chunk_meshes[chunk_pos] = mesh
        application.resume()

    c.model = chunk_meshes[chunk_pos]
    c.position = Vec3(
        chunk_pos[0]*CHUNK_W,
        chunk_pos[1]*CHUNK_H,
        chunk_pos[2]*CHUNK_W
    )

def set_block(wx,wy,wz, block):
    pcx,pcy,pcz = player.chunk
    cx, cy, cz = wx//CHUNK_W, wy//CHUNK_H, wz//CHUNK_W
    lx, ly, lz = wx%CHUNK_W, wy%CHUNK_H, wz%CHUNK_W
    chunk_contents[cx,cy,cz][lx,ly,lz] = block
    
    reload_chunk(cx-pcx+RENDER_DISTANCE_XZ,cy-pcy+RENDER_DISTANCE_Y,cz-pcz+RENDER_DISTANCE_XZ, True)
    reload_chunk(cx-pcx+RENDER_DISTANCE_XZ,cy-pcy+RENDER_DISTANCE_Y,cz-pcz+RENDER_DISTANCE_XZ, False, True)

player.set_block = set_block

all_colliders = []
def update_colliders(): 
    for e in all_colliders: destroy(e)
    all_colliders.clear()

    px, py, pz = floor(player.x), floor(player.y), floor(player.z)

    # Collisions
    for dx in range(-2,3):
        for dy in range(-3,3):
            for dz in range(-2,3):
                wx, wy, wz = px+dx, py+dy, pz+dz
                if get_block(wx, wy, wz) != AIR:
                    all_colliders.append(Entity(
                        parent=player.block_colliders,
                        position=Vec3(wx+.5, wy+.5, wz+.5),
                        collider='box',
                        visible=False,
                        # color = color.black,
                        # model="cube"
                    ))
update_colliders()

def update():
    global plr_chunk
    chunk = Vec3(player.chunk)

    # Update chunks
    if chunk != plr_chunk:
        plr_chunk = chunk

        # d'abord clear les vbo ou jsp quoi
        for dcx in range(2*RENDER_DISTANCE_XZ+1):
            for dcy in range(2*RENDER_DISTANCE_Y+1):
                for dcz in range(2*RENDER_DISTANCE_XZ+1):
                    reload_chunk(dcx,dcy,dcz, True)

        # changer les mesh
        for dcx in range(2*RENDER_DISTANCE_XZ+1):
            for dcy in range(2*RENDER_DISTANCE_Y+1):
                for dcz in range(2*RENDER_DISTANCE_XZ+1):
                    reload_chunk(dcx,dcy,dcz)

    # Update colliders
    update_colliders()

app.run()