from random import choice, randint
from threading import Thread
import queue
import threading
from perlin_noise import PerlinNoise
from ursina import *
from blocks import *
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
        ) for dcx,dcz in RENDER_COORDS}


        self.all_chunks.set_shader_input("light_direction", light_direction)
        self.all_waters.set_shader_input("light_direction", light_direction)

        self.chunk_queue = queue.Queue()
        self.new_chunks = queue.Queue()
        self.chunk_worker = threading.Thread(target=self.update_chunk_queue, daemon=True)
        self.chunk_worker.start()

        self.chunk_waitlist = set()
        self.chunk_queue_lock = threading.Lock()

    def compute_ground(self, cx, cz, x, z):
        pos = (cx*CHUNK_W+x, cz*CHUNK_W+z)

        value = 0.0
        freq = 1.0
        amplitude = 3.0
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
                    
                    else:
                        content[x,y,z] = AIR
                        
        return content
    
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

    def chunk_create_mesh(self, mesh, chunk_pos, chunk_type=CT_TERRAIN):
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

        mesh.vertices = vertices
        mesh.triangles = triangles
        mesh.uvs = uvs
        mesh.normals = normals
        mesh.colors = colors
        mesh.generate()
        return mesh

    def create_mesh(self, chunk_pos):
        if chunk_pos not in self.chunk_meshes:
            self.chunk_meshes[chunk_pos] = (Mesh(),Mesh())
        
        mesh, water_mesh = self.chunk_meshes[chunk_pos] 
        mesh.clear(); water_mesh.clear()
        self.chunk_create_mesh(mesh, chunk_pos)
        self.chunk_create_mesh(water_mesh, chunk_pos, chunk_type=CT_WATER)
        self.chunk_meshes[chunk_pos] = (mesh, water_mesh)

    def get_block(self, wx, wy, wz):
        cx, cz = chunk_of_block(wx,wz)
        lx, lz = local_of_block(wx,wz)
        if (cx,cz) not in self.chunk_contents or not y_inbounds(wy): return AIR
        return self.chunk_contents[cx,cz][lx,wy,lz]

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
                    
        application.resume()
        return True
    
    def update_chunk_queue(self):
        while True:
            # Récupérer un chunk de la queue
            try: chunk_pos = self.chunk_queue.get(timeout=0.1)
            except queue.Empty: continue

            # Génerer le chunk
            c = self.chunk_procedural(*chunk_pos)
            self.chunk_contents[chunk_pos] = c

            # Enlever le chunk de la liste d'attente
            self.new_chunks.put(chunk_pos)
            with self.chunk_queue_lock: self.chunk_waitlist.discard(chunk_pos)

            # signaler que l'item est traité
            self.chunk_queue.task_done()

    def update_chunks(self):
        # Générer les nouveaux chunks
        pcx,pcz = self.player.chunk
        for dcx, dcz in RENDER_COORDS:
            chunk_pos = (
                pcx + dcx-RENDER_DISTANCE,
                pcz + dcz-RENDER_DISTANCE
            )
            if chunk_pos not in self.chunk_contents:
                with self.chunk_queue_lock:
                    if chunk_pos not in self.chunk_waitlist:
                        self.chunk_waitlist.add(chunk_pos)
                        self.chunk_queue.put(chunk_pos)

        # Recréér les meshs des nouveaux chunks
        recreate = []
        while not self.new_chunks.empty():
            cx,cz = self.new_chunks.get_nowait()
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