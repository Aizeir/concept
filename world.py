from perlin_noise import PerlinNoise
from ursina import *
from blocks import *



FFRONT,FBACK,FRIGHT,FLEFT,FUP,FDOWN = range(6)
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


CHUNK_W = 8
CHUNK_H = 32
chunk_inbounds = lambda x,y,z: 0<=x<CHUNK_W and 0<=z<CHUNK_W and 0<=y<CHUNK_H

FLOOR = 8
MAX_GEN_HEIGHT = 24
BREAK_DIST = 10

noise = PerlinNoise(0.01)


def chunk_mesh(mesh, content):
    for x in range(CHUNK_W):
        for z in range(CHUNK_W):
            for y in range(CHUNK_H):
                block = content[x,y,z]
                pos = Vec3(x,y,z)
                if block == AIR: continue
                # Faces
                for i in range(6): 
                    dx,dy,dz = face_normals[i]
                    face_hidden = chunk_inbounds(x+dx,y+dy,z+dz) and content[x+dx,y+dy,z+dz] != AIR
                    if face_hidden: continue

                    l = len(mesh.vertices)
                    mesh.vertices.extend([pos+v for v in cube_vertices[i*4:(i+1)*4]])
                    mesh.triangles.extend([l, l+2, l+1,  l, l+3, l+2])
                    mesh.uvs.extend(atlas_face_uv(block.tex_coords[i]))
                    mesh.normals.extend([face_normals[i]]*4)
    return mesh
        
def chunk_procedural(cx,cy,cz):
    content = {}

    for x in range(CHUNK_W):
        for z in range(CHUNK_W):
            value = noise((cx*CHUNK_W+x,cz*CHUNK_W+z))
            ground = FLOOR + int((MAX_GEN_HEIGHT-FLOOR+1)*value)

            for y in range(CHUNK_H):
                if cy*CHUNK_H+y <= ground:
                    content[x,y,z] = GRASS
                else:
                    content[x,y,z] = AIR
    
    return content



chunk_meshes = {}
chunk_contents = {}


def get_block(wx, wy, wz):
    cx, cy, cz = wx//CHUNK_W, wy//CHUNK_H, wz//CHUNK_W
    lx, ly, lz = wx%CHUNK_W, wy%CHUNK_H, wz%CHUNK_W
    if (cx,cy,cz) not in chunk_contents:
        return AIR
    return chunk_contents[cx,cy,cz][lx,ly,lz]

