from concurrent.futures import ThreadPoolExecutor
from random import choice, randint
from threading import Thread
import queue
import threading
from perlin_noise import PerlinNoise
from ursina import *
from animal import Animal
from blocks import *
from drop import Drop
from settings import *
from shader import *


class World:
    def __init__(self, game):
        self.game = game
        self.player = None # defini plus tard

        self.noise = PerlinNoise(0.01)

        self.chunk_meshes = {}
        self.chunk_contents = {}
        self.all_chunks = Entity(shader=shader)
        self.all_waters = Entity(shader=water_shader)
        self.all_animals = Entity(shader=animal_shader)
        self.chunks = {(dcx,dcz): Entity(
            parent=self.all_chunks,
            model=Mesh(),
            texture="assets/atlas",
            texture_scale=(1/atlas_w,1/atlas_h),
            shader=shader,
        ) for dcx,dcz in RENDER_COORDS}

        self.waters = {(dcx,dcz): Entity(
            parent=self.all_waters,
            model=Mesh(),
            texture="assets/atlas",
            texture_scale=(1/atlas_w,1/atlas_h),
            shader=water_shader,
            double_sided=True,
        ) for dcx,dcz in RENDER_COORDS}

        self.all_chunks.set_shader_input("light_direction", light_direction)
        self.all_waters.set_shader_input("light_direction", light_direction)
        self.all_animals.set_shader_input("light_direction", light_direction)
        self.drops = []

    def spawn(self, pos, animal):
        Animal(self, pos, animal)

    def compute_ground(self, cx, cz, x, z):
        pos = (cx*CHUNK_W+x, cz*CHUNK_W+z)

        value = 0.0
        freq = 1.0
        amplitude = 1.5
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

    def chunk_procedural(self, cx,cz):
        content = {}

        for x in range(CHUNK_W):
            for z in range(CHUNK_W):
                ground = self.compute_ground(cx,cz,x,z)
                dirt = ground - 3
                for y in range(CHUNK_H):
                    if y == 0:
                        content[x,y,z] = BEDROCK

                    elif y < dirt:
                        p = (x*73856093 ^ y*19349663 ^ z*83492791) % 100
                        if   p <= 2:
                            content[x,y,z] = GOLD_ORE
                        elif p <= 6:
                            content[x,y,z] = COPPER_ORE
                        elif p <= 12:
                            content[x,y,z] = IRON_ORE
                        else:
                            content[x,y,z] = STONE
                        
                    elif dirt <= y <= ground:
                        if y <= SEA_LEVEL+1:
                            content[x,y,z] = SAND
                        else:
                            content[x,y,z] = (DIRT,GRASS_BLOCK)[y==ground]
                    
                    elif ground < y <= SEA_LEVEL:
                        content[x,y,z] = WATER
                
                    elif y == ground+1:
                        if randint(1,20) == 1:
                            content[x,y,z] = choice((PUPPY, DANDELION, DEADBUSH, GRASS, MUSHROOM))
                        else:
                            content[x,y,z] = AIR
                        
                        if randint(1,600) == 1:
                            wx,wz = cx*CHUNK_W+x,cz*CHUNK_W+z
                            self.spawn((wx,y+1,wz), choice(("cow","sheep","fox")))
                    
                    else:
                        content[x,y,z] = AIR
                        
        return content

    def _create_mesh_data(self, chunk_pos, chunk_type=CT_TERRAIN):
        content = self.chunk_contents[chunk_pos]
        vertices = []
        triangles = []
        uvs = []
        normals = []
        colors = []
        cx,cz = chunk_pos

        for x,y,z in CHUNK_COORDS:
            block = content[x,y,z]
            if block.type not in CHUNK_TYPES[chunk_type]: continue

            if block.mesh == MESH_CUBE:
                for i in range(6):
                    # Quelques conditions
                    dx,dy,dz = face_normals[i]
                    wnx,wny,wnz = cx*CHUNK_W+x+dx,y+dy,cz*CHUNK_W+z+dz

                    if chunk_type == CT_TERRAIN and block.type == BT_SOLID:
                        if self.get_block(wnx,wny,wnz).type == BT_SOLID: continue

                    elif chunk_type == CT_WATER and block.type == BT_WATER:
                        if self.get_block(wnx,wny,wnz).type == BT_WATER: continue
                        if self.get_block(wnx,wny,wnz).type == BT_SOLID: continue
                    
                    # ---
                    idx = len(vertices)
                    vertices.extend([(x+vx, y+vy, z+vz) for vx,vy,vz in cube_vertices[i*4:(i+1)*4]])
                    triangles.extend([idx, idx+2, idx+1, idx, idx+3, idx+2])
                    uvs.extend(atlas_face_uv(block.tex_coords[i]))
                    normals.extend([face_normals[i]]*4)
                    colors.extend([cx*CHUNK_W+x,y,cz*CHUNK_W+z,block.id]*4)
            
            elif block.mesh == MESH_X:
                for i in range(4):
                    idx = len(vertices)
                    vertices.extend([(x+vx, y+vy, z+vz) for vx,vy,vz in x_vertices[i*4:(i+1)*4]])
                    triangles.extend([idx, idx+2, idx+1, idx, idx+3, idx+2])
                    uvs.extend(atlas_face_uv(block.tex_coords[i]))
                    normals.extend([x_face_normals[i]]*4)
                    colors.extend([cx*CHUNK_W+x,y,cz*CHUNK_W+z,block.id]*4)

        return {"vertices": vertices, "triangles": triangles, "uvs": uvs, "normals": normals, "colors": colors}

    def create_mesh(self, chunk_pos):
        if chunk_pos not in self.chunk_meshes:
            self.chunk_meshes[chunk_pos] = (Mesh(), Mesh())

        mesh, water_mesh = self.chunk_meshes[chunk_pos]
        mesh_data, water_data = self._create_mesh_data(chunk_pos, CT_TERRAIN), self._create_mesh_data(chunk_pos, CT_WATER)

        mesh.clear()
        for k,v in mesh_data.items(): setattr(mesh, k, v)
        mesh.generate()

        water_mesh.clear()
        for k,v in water_data.items(): setattr(water_mesh, k, v)
        water_mesh.generate()
    

    def load_chunk(self, dcx,dcz):
        """ Affecte la bonne position et le bon mesh à l'entité-chunk """
        chunk_pos = (
            self.player.chunk[0] + dcx-RENDER_DISTANCE,
            self.player.chunk[1] + dcz-RENDER_DISTANCE
        )
        c,w = self.chunks[dcx,dcz], self.waters[dcx,dcz]
        if chunk_pos not in self.chunk_meshes: return
        c.model, w.model = self.chunk_meshes[chunk_pos]
        c.position = w.position = (
            chunk_pos[0]*CHUNK_W, 0, chunk_pos[1]*CHUNK_W
        )


    def get_block(self, wx, wy, wz):
        """ Retourne le type de block (AIR si le bloc n'existe pas) """
        cx, cz = chunk_of_block(wx,wz)
        lx, lz = local_of_block(wx,wz)
        if not self.block_exists(wx,wy,wz): return AIR
        return self.chunk_contents[cx,cz][lx,wy,lz]

    def block_exists(self, wx,wy,wz):
        return chunk_of_block(wx,wz) in self.chunk_contents and y_inbounds(wy)
        
    def set_block(self, wx,wy,wz, block):
        # Pas possible de poser en <0 et >= CHUNK_H
        if not y_inbounds(wy): return False
        # Changer le block
        cx, cz = chunk_of_block(wx,wz)
        lx, lz = local_of_block(wx,wz)
        self.chunk_contents[cx,cz][lx,wy,lz] = block

        # Recréér le mesh / recharger le chunk
        application.pause()
        pcx,pcz = self.player.chunk
        dcx,dcz = cx-pcx+RENDER_DISTANCE,cz-pcz+RENDER_DISTANCE
        self.create_mesh((cx,cz))
        self.load_chunk(dcx,dcz)
        
        # Recréér / recharger les chunks d'à coté
        for i in range(4):
            dx,dz = face_normals_xz[i]
            if not chunk_inbounds(lx+dx,lz+dz):
                ncx,ncz = chunk_of_block(wx+dx, wz+dz)
                ndcx,ndcz = ncx-pcx+RENDER_DISTANCE,ncz-pcz+RENDER_DISTANCE
                self.create_mesh((ncx,ncz))
                self.load_chunk(ndcx,ndcz)

        # Ecoulement eau
        if block == WATER:
            for n in face_normals:
                if n == face_normals[FTOP]: continue
                nx,ny,nz = wx+n[0],wy+n[1],wz+n[2]
                if self.block_exists(nx,ny,nz) and self.get_block(nx,ny,nz) == AIR:
                    self.set_block(nx,ny,nz, WATER)
                    
        application.resume()
        return True
    
    def break_block(self, x,y,z):
        block = self.get_block(x,y,z)
        if block.type in CHUNK_TYPES[CT_TERRAIN]:
            self.player.try_add_item(block)
             #self.drops.append(Drop(self, (x,y,z), block))
        self.set_block(x,y,z, AIR)

        if self.get_block(x,y+1,z).type == BT_PLANT:
            self.break_block(x,y+1,z)

        # Ecoulement eau
        for n in face_normals:
            if n == face_normals[FBOTTOM]: continue
            if self.get_block(x+n[0],y+n[1],z+n[2]) == WATER:
                self.set_block(x,y,z, WATER)
                break

    def update_chunks(self):
        # Générer les nouveaux chunks
        pcx,pcz = self.player.chunk
        new_chunks = []
        for dcx, dcz in RENDER_COORDS:
            chunk_pos = (
                pcx + dcx-RENDER_DISTANCE,
                pcz + dcz-RENDER_DISTANCE
            )
            if chunk_pos not in self.chunk_contents:
                c = self.chunk_procedural(*chunk_pos)
                self.chunk_contents[chunk_pos] = c
                new_chunks.append(chunk_pos)
            
        # Recréér les meshs des nouveaux chunks
        recreate = []
        for cx,cz in new_chunks:
            for dcx,dcz in ((0,0),*face_normals_xz):
                if (cx+dcx, cz+dcz) in self.chunk_contents:
                    recreate.append((cx+dcx, cz+dcz))
        for chunk_pos in list(set(recreate)):
            self.create_mesh(chunk_pos)

        # D'abord clear les vbo ou jsp quoi
        for dcx, dcz in RENDER_COORDS:
            self.chunks[dcx,dcz].model = Mesh()
            self.waters[dcx,dcz].model = Mesh()
        
        # Changer les chunks
        for dcx, dcz in RENDER_COORDS:
            self.load_chunk(dcx,dcz)

            