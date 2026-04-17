from random import randint

from perlin_noise import PerlinNoise
from ursina import *
from blocks import *
from settings import *
from shader import *

# --- Constants
face_normals = [(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]

cube_vertices = [
    # FRONT (Z=1)
    Vec3(0,0,1), Vec3(1,0,1), Vec3(1,1,1), Vec3(0,1,1),
    # BACK (Z=0)
    Vec3(1,0,0), Vec3(0,0,0), Vec3(0,1,0), Vec3(1,1,0),
    # RIGHT (X=1)
    Vec3(1,0,1), Vec3(1,0,0), Vec3(1,1,0), Vec3(1,1,1),
    # LEFT (X=0)
    Vec3(0,0,0), Vec3(0,0,1), Vec3(0,1,1), Vec3(0,1,0),
    # TOP (Y=1)
    Vec3(0,1,1), Vec3(1,1,1), Vec3(1,1,0), Vec3(0,1,0),
    # BOTTOM (Y=0)
    Vec3(0,0,0), Vec3(1,0,0), Vec3(1,0,1), Vec3(0,0,1),
]

cube_triangles = []
cube_normals = []
for i in range(6):
    j = i*4
    cube_triangles.extend([j, j+2, j+1,  j, j+3, j+2])
    cube_normals.extend([face_normals[i]]*4)

def atlas_face_uv(tex_coord):
    tx,ty = tex_coord
    return [
        (tx/atlas_w, ty/atlas_h),
        ((tx+1)/atlas_w, ty/atlas_h),
        ((tx+1)/atlas_w, (ty+1)/atlas_h),
        (tx/atlas_w, (ty+1)/atlas_h),
    ]


def chunk_mesh(mesh, content, chunk_pos):
    vertices = []
    triangles = []
    uvs = []
    normals = []
    colors = []
    cx,cy,cz = chunk_pos

    for x in range(CHUNK_W):
        for z in range(CHUNK_W):
            for y in range(CHUNK_H):
                block = content[x,y,z]
                if block == AIR:  continue

                for i in range(6):
                    dx,dy,dz = face_normals[i]
                    nx,ny,nz = x+dx, y+dy, z+dz
                    if chunk_inbounds(nx,ny,nz) and content[nx,ny,nz] != AIR: continue

                    idx = len(vertices)
                    vertices.extend([(x+vx, y+vy, z+vz) for vx,vy,vz in cube_vertices[i*4:(i+1)*4]])
                    triangles.extend([idx, idx+2, idx+1, idx, idx+3, idx+2])
                    uvs.extend(atlas_face_uv(block.tex_coords[i]))
                    normals.extend([face_normals[i]]*4)
                    colors.extend([cx*CHUNK_W+x,cy*CHUNK_H+y,cz*CHUNK_W+z,block.id]*4)


    mesh.vertices = vertices
    mesh.triangles = triangles
    mesh.uvs = uvs
    mesh.normals = normals
    mesh.colors = colors
    return mesh

# ---

class World:
    def __init__(self, game):
        self.game = game
        self.player = None # defini plus tard

        self.noise = PerlinNoise(0.01)

        self.chunk_meshes = {}
        self.chunk_contents = {}
        self.all_chunks = Entity(shader=shader)
        self.chunks = {(dcx,dcy,dcz): Entity(
            parent=self.all_chunks,
            model=Mesh(),
            texture="assets/atlas",
            texture_scale=(1/atlas_w,1/atlas_h),
            shader=shader,
        )\
        for dcz in range(2*RENDER_DISTANCE_XZ+1)
        for dcy in range(2*RENDER_DISTANCE_Y+1)
        for dcx in range(2*RENDER_DISTANCE_XZ+1)}

        self.all_chunks.set_shader_input("light_direction", light_direction)

        self.chunk_queue = []

    def compute_ground(self, cx, cz, x, z):
        pos = (cx*CHUNK_W+x, cz*CHUNK_W+z)

        value = 0.0
        freq = 1.0
        amplitude = 2.0
        max_value = 0.0

        for i in range(4):
            value += self.noise((pos[0] * freq, pos[1] * freq)) * amplitude
            max_value += amplitude
            amplitude *= 0.6
            freq *= 2.0

        value = (value + 1) / 2
        value = pow(value, 1) * 0.8
        
        ground = MIN_GEN_HEIGHT + int(value * (MAX_GEN_HEIGHT - MIN_GEN_HEIGHT))
        return ground

    def chunk_procedural(self, cx,cy,cz):
        content = {}

        for x in range(CHUNK_W):
            for z in range(CHUNK_W):
                ground = self.compute_ground(cx,cz,x,z)
                dirt = ground - 3
                for y in range(CHUNK_H):
                    wy = cy*CHUNK_H+y
                    if wy <= 0:
                        content[x,y,z] = BEDROCK

                    elif wy < dirt:
                        p = (x*73856093 ^ y*19349663 ^ z*83492791) % 100
                        if   p <= 2:
                            content[x,y,z] = GOLD_ORE
                        elif p <= 6:
                            content[x,y,z] = COPPER_ORE
                        elif p <= 12:
                            content[x,y,z] = IRON_ORE
                        else:
                            content[x,y,z] = STONE
                        
                    elif dirt <= wy <= ground:
                        if wy <= SEA_LEVEL+1:
                            content[x,y,z] = SAND
                        else:
                            content[x,y,z] = (DIRT,GRASS)[wy==ground]
                    else:
                        content[x,y,z] = (AIR,WATER)[wy <= SEA_LEVEL]
                        
        return content
    
    def reload_chunk(self, dcx,dcy,dcz, clear=False, mesh=False):
        application.pause()
        # pcx,pcy,pcz = self.player.chunk
        # dcx,dcy,dcz = cx-pcx+RENDER_DISTANCE_XZ,cy-pcy+RENDER_DISTANCE_Y,cz-pcz+RENDER_DISTANCE_XZ
        c = self.chunks[dcx,dcy,dcz]
        chunk_pos = (
            self.player.chunk[0] + dcx-RENDER_DISTANCE_XZ,
            self.player.chunk[1] + dcy-RENDER_DISTANCE_Y,
            self.player.chunk[2] + dcz-RENDER_DISTANCE_XZ
        )

        # Clear le VBO (nul ursina)
        if clear: c.model = Mesh(); return
        
        #t = time.time()
        # Si nouveau chunk
        if chunk_pos not in self.chunk_meshes:
            self.chunk_contents[chunk_pos] = self.chunk_procedural(*chunk_pos)
            #tp = time.time()
            mesh = Mesh(vertices=[], triangles=[], uvs=[], normals=[])
            chunk_mesh(mesh, self.chunk_contents[chunk_pos], chunk_pos)
            #tb = time.time()
            mesh.generate()
            self.chunk_meshes[chunk_pos] = mesh
            #tc = time.time()
            #print("recreation", tp-t, tb-tp, tc-tb)

        # Si besoin de recréér
        elif mesh:
            mesh = Mesh(vertices=[], triangles=[], uvs=[], normals=[])
            chunk_mesh(mesh, self.chunk_contents[chunk_pos], chunk_pos)
            mesh.generate()
            self.chunk_meshes[chunk_pos] = mesh
        #t2 = time.time()
        c.model = self.chunk_meshes[chunk_pos]
        c.position = Vec3(
            chunk_pos[0]*CHUNK_W,
            chunk_pos[1]*CHUNK_H,
            chunk_pos[2]*CHUNK_W
        )
        #t3 = time.time()
        application.resume()
        #print("chunk reloaded", t3-t, ":", t2-t, "+", t3-t2)

    def get_block(self, wx, wy, wz):
        cx, cy, cz = wx//CHUNK_W, wy//CHUNK_H, wz//CHUNK_W
        lx, ly, lz = wx%CHUNK_W, wy%CHUNK_H, wz%CHUNK_W
        if (cx,cy,cz) not in self.chunk_contents: return AIR
        return self.chunk_contents[cx,cy,cz][lx,ly,lz]

    def set_block(self, wx,wy,wz, block):
        cx, cy, cz = wx//CHUNK_W, wy//CHUNK_H, wz//CHUNK_W
        lx, ly, lz = wx%CHUNK_W, wy%CHUNK_H, wz%CHUNK_W
        self.chunk_contents[cx,cy,cz][lx,ly,lz] = block
        
        pcx,pcy,pcz = self.player.chunk
        dcx,dcy,dcz = cx-pcx+RENDER_DISTANCE_XZ,cy-pcy+RENDER_DISTANCE_Y,cz-pcz+RENDER_DISTANCE_XZ
        self.reload_chunk(dcx,dcy,dcz, False, True)
