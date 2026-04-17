from ursina import *
from dda import dda
from world import *
from ursina.shaders import basic_lighting_shader

text = Text()

class Player(Entity):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.world = game.world

        self.speed = 5
        self.size = Vec3(.5,1.8,.5)
        self.cam_off = Vec3(0, 1.5, 0)
        self.velocity = Vec3()

        self.camera_pivot = Entity(parent=self, position=self.cam_off)
        camera.parent = self.camera_pivot
        camera.position = Vec3.zero
        camera.rotation = Vec3.zero
        camera.fov = 90

        mouse.locked = True
        self.mouse_sensitivity = Vec2(100)

        self.gravity = 1
        self.grounded = False
        self.jump_force = 20
        self.jumping = False
        self.sprint = False

        self.transitions = { # value / start / reverse / duration
            "sprint": [0, 0, True, .2],
            "break":  [0, 0, True, 0.05],
            "place":  [0, 0, True, .25],
        } 
        
        self.traverse_target = scene     # by default, it will collide with everything. change this to change the raycasts' traverse targets.
        self.ignore_list = [self, ]
        self.on_destroy = self.on_disable

        self.block_colliders = Entity()
        self.break_colliders = Entity()

        self.selection = None

        self.breaking_cube = Entity(
            model=Mesh(),
            visible=False,
            scale=1.001,
            texture="assets/atlas",
            texture_scale=(1/atlas_w,1/atlas_h),
            shader=basic_lighting_shader
        )
        self.selecting_cube = Entity(
            model="cube",
            visible=False,
            scale=1.0001,
            color=color.black,
            alpha=0.2,
            shader=basic_lighting_shader
        )

        selection_anims = [
            Mesh(
                vertices=[x-Vec3(.5) for x in cube_vertices],
                triangles=cube_triangles,
                normals=cube_normals,
                uvs=atlas_face_uv(tex_coord(6*4+i))*6,
            )
            for i in range(4)
        ]
        self.breaking_anim = selection_anims[0:3]
        
        self.hover_anim = selection_anims[3]
        self.hover_alpha = .2

    def on_window_ready(self):
        camera.rotation = Vec3.zero

    def activate_trans(self, name, reverse=False):
        self.transitions[name][1] = time.time()
        self.transitions[name][2] = reverse

    def end_trans(self, name, value):
        self.transitions[name][1] -= self.transitions[name][3]
        self.transitions[name][2] = not value
        self.transitions[name][0] = value

    @property
    def head(self):
        return self.position + self.cam_off
    
    @property
    def chunk(self):
        pos = self.position
        return int(pos.x//CHUNK_W), int(pos.y//CHUNK_H), int(pos.z//CHUNK_W)

    @property
    def breaking_block(self):
        return not self.transitions["break"][2]
    @property
    def placing_block(self):
        return not self.transitions["place"][2]

    def update(self):
        # Transitions (value / start / reverse / duration)
        for t in self.transitions.values():
            val = min(1, (time.time()-t[1]) / t[3])
            t[0] = (val, 1-val)[t[2]]
        #

        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

        # Sprint
        sprint = held_keys["f"]
        if self.sprint != sprint:
            self.activate_trans("sprint", not sprint)
        self.sprint = sprint
        self.speed = 5 + 5*self.transitions["sprint"][0]**2
        camera.fov = 90 + 8*self.transitions["sprint"][0]**2

        # Jump
        if held_keys["space"] and self.grounded:
            self.jump()

        # - Select block
        block_pos, face = dda(self.world.get_block, self.head, camera.forward, self.chunk)
        block_swap = self.selection and self.selection[0] != block_pos

        # show selection block
        if block_pos is not None:
            self.selection = (block_pos,face)
            self.breaking_cube.visible_setter(True)
            self.breaking_cube.position_setter(block_pos+Vec3(.5))
            self.selecting_cube.visible_setter(True)
            self.selecting_cube.position_setter(block_pos+Vec3(.5))
        # hide selection block
        else:
            self.selection = None
            self.breaking_cube.visible_setter(False)
            self.selecting_cube.visible_setter(False)
            self.end_trans("break", 0)
            self.end_trans("place", 0)
        

        # - Block selection animation
        if self.placing_block and self.transitions["place"][0] == 1:
            self.end_trans("place", 0)

        if self.breaking_block:
            if self.transitions["break"][0] == 1:
                self.break_block()
                self.end_trans("break",0)
            else:
                value = self.transitions["break"][0]
                self.breaking_cube.model_setter(self.breaking_anim[int(3*value)])
                self.breaking_cube.alpha_setter(1)
        
        elif self.selection:
            self.breaking_cube.model_setter(self.hover_anim)
            self.breaking_cube.alpha_setter(self.hover_alpha)
        
        # - Breaking block
        # release block
        if not mouse.left and self.breaking_block:
            self.end_trans("break", 0)
        # break block
        elif mouse.left and not self.breaking_block and not self.placing_block:
            self.activate_trans("break", False)
        # reset if block change
        if self.breaking_block and block_swap:
            self.end_trans("break",0)

        # - Placement
        if mouse.right and not self.placing_block and not self.breaking_block:
            if self.place_block():
                self.activate_trans("place", False)
        elif not mouse.right and self.placing_block:
            self.end_trans("place",0)
            
        # Collisions
        direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()
        
        self.velocity.xz = direction.xz * self.speed
        self.velocity.y -= self.gravity

        dv = self.velocity * min(0.1, time.dt)
        if self.collisions(Vec3(dv.x, 0, 0)):
            self.velocity.x = 0
        else:
            self.position += Vec3(dv.x, 0, 0)

        if self.collisions(Vec3(0, 0, dv.z)):
            self.velocity.z = 0
        else:
            self.position += Vec3(0, 0, dv.z)

        self.grounded = False
        if self.collisions(Vec3(0, dv.y, 0)):
            self.velocity.y = 0
        else:
            self.position += Vec3(0,dv.y,0)
            

    def break_block(self):
        self.world.set_block(*self.selection[0], AIR)

    def place_block(self):
        pos = self.position
        min_x = math.floor(pos.x - self.size.x/2)
        max_x = math.floor(pos.x + self.size.x/2)
        min_y = math.floor(pos.y)
        max_y = math.floor(pos.y + self.size.y)
        min_z = math.floor(pos.z - self.size.z/2)
        max_z = math.floor(pos.z + self.size.z/2)

        x,y,z = self.selection[0]+face_normals[self.selection[1]]
        if not (min_x <= x <= max_x and min_y <= y <= max_y and min_z <= z <= max_z):
            self.world.set_block(x,y,z, GRASS)
            return True
        else:
            return False

    def collisions(self, dv):
        # Hitbox rectangle
        pos = self.position
        min_x = math.floor(pos.x + dv.x - self.size.x/2)
        max_x = math.floor(pos.x + dv.x + self.size.x/2)
        min_y = math.floor(pos.y + dv.y)
        max_y = math.floor(pos.y + dv.y + self.size.y)
        min_z = math.floor(pos.z + dv.z - self.size.z/2)
        max_z = math.floor(pos.z + dv.z + self.size.z/2)

        # Collisions
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    block = self.world.get_block(x, y, z)
                    if block != AIR:
                        if dv.y < 0:
                            pos.y = y + 1
                            self.grounded = True
                        if dv.y > 0:
                            pos.y = y - self.size.y
                        return True
        return False

    def jump(self):
        if not self.grounded: return
        self.velocity.y = self.gravity * self.jump_force

    def on_enable(self):
        mouse.locked = True
        # restore parent and position/rotation from before disablem in case you moved the camera in the meantime.
        if hasattr(self, 'camera_pivot') and hasattr(self, '_original_camera_transform'):
            camera.parent = self.camera_pivot
            camera.transform = self._original_camera_transform

    def on_disable(self):
        mouse.locked = False
        self._original_camera_transform = camera.transform  # store original position and rotation
        camera.world_parent = scene

