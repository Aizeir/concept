from ursina import *

atlas_w = 4
atlas_h = 8
def tex_coord(tex_id):
    return (tex_id%atlas_w, atlas_h-1 - tex_id//atlas_w)

FFRONT,FBACK,FRIGHT,FLEFT,FTOP,FBOTTOM = range(6)
BT_SOLID, BT_WATER, BT_AIR, BT_PLANT = range(4)
MESH_CUBE, MESH_X = "cube","x"

CT_TERRAIN, CT_WATER = range(2)
CHUNK_TYPES = {CT_TERRAIN: (BT_SOLID,BT_PLANT), CT_WATER:(BT_WATER,)}

idx = 0
class Block:
    def __init__(self, tex_ids=None, type=BT_SOLID, mesh=MESH_CUBE):
        global idx; self.id = idx; idx += 1
        self.tex_ids = tex_ids
        self.tex_coords = [tex_coord(tex_id) for tex_id in tex_ids] if tex_ids else None
        self.type = type
        self.mesh = mesh
        
    def __repr__(self):
        return f"<Block[{self.id} | {self.type}]>"

AIR = Block(type=BT_AIR)
GRASS_BLOCK = Block([2]*4+[0,1])
DIRT = Block([1]*6)
SAND = Block([8]*6)
BEDROCK = Block([14]*6)
STONE = Block([3]*6)
IRON_ORE = Block([4]*4+[7]*2)
COPPER_ORE = Block([5]*4+[7]*2)
GOLD_ORE = Block([6]*4+[7]*2)
STUMP = Block([10]*4+[11,16])
LOG = Block([9]*4+[11]*2)
TREETOP = Block([15]*4+[16,11])
PLANKS = Block([13]*6)
LEAVES = Block([12]*6)
FRUIT_LEAVES = Block([19]*6)
WATER = Block([17]*6, type=BT_WATER)
GRASS = Block([18]*4, type=BT_PLANT, mesh=MESH_X)
PUPPY = Block([20]*4, type=BT_PLANT, mesh=MESH_X)
DEADBUSH = Block([21]*4, type=BT_PLANT, mesh=MESH_X)
MUSHROOM = Block([22]*4, type=BT_PLANT, mesh=MESH_X)
DANDELION = Block([23]*4, type=BT_PLANT, mesh=MESH_X)


# --- Constants
face_normals = [(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]
face_normals_xz = [(0,1),(0,-1),(1,0),(-1,0)]
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


x_face_normals = [(-1,0,-1),(1,0,1),(1,0,-1),(-1,0,1)]
x_vertices = [
    Vec3(0,0,1), Vec3(1,0,0), Vec3(1,1,0), Vec3(0,1,1),
    Vec3(1,0,0), Vec3(0,0,1), Vec3(0,1,1), Vec3(1,1,0),
    Vec3(0,0,0), Vec3(1,0,1), Vec3(1,1,1), Vec3(0,1,0),
    Vec3(1,0,1), Vec3(0,0,0), Vec3(0,1,0), Vec3(1,1,1),
]


def atlas_face_uv(tex_coord):
    tx,ty = tex_coord
    return [
        (tx/atlas_w, ty/atlas_h),
        ((tx+1)/atlas_w, ty/atlas_h),
        ((tx+1)/atlas_w, (ty+1)/atlas_h),
        (tx/atlas_w, (ty+1)/atlas_h),
    ]

# ---