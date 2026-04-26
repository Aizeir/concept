from settings import *
from blocks import *
from ursina.shaders import basic_lighting_shader

drop_size = Vec3(1/3)
class Drop(Entity):
    def __init__(self, world, position, block):
        self.world = world
        super().__init__(
            position=Vec3(position)+Vec3(.5,.5,.5),
            scale=drop_size,
            texture="assets/atlas",
            texture_scale=(1/atlas_w,1/atlas_h),
            shader=basic_lighting_shader,
        )

        # Mesh
        uvs = []
        triangles = []
        normals = []

        if block.type == BT_SOLID:
            vertices = [x-Vec3(.5) for x in cube_vertices]
            fn = face_normals
            for i in range(6): uvs.extend(atlas_face_uv(block.tex_coords[i]))
        elif block.type == BT_PLANT:
            vertices = [x-Vec3(.5) for x in x_vertices]
            fn = x_face_normals
            for i in range(4): uvs.extend(atlas_face_uv(block.tex_coords[i]))

        for i in range(FACE_AMT[block.type]):
            j = i*4
            triangles.extend([j, j+2, j+1,  j, j+3, j+2])
            normals.extend([fn[i]]*4)

        self.model = Mesh(
            vertices=vertices,
            triangles=triangles,
            uvs=uvs,
            normals=normals,
        )

        self.size = Vec3(.5)

    def update(self):
        self.rotate(Vec3(0,time.dt*360,0))
        
        plr_size = self.world.player.size
        size = self.size
        
