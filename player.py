from ursina import *
from dda import dda
from world import *
from ursina.shaders import basic_lighting_shader

class Player(Entity):
    def __init__(self, height=2, **kwargs):
        super().__init__(**kwargs)
        self.speed = 5
        self.height = height

        self.camera_pivot = Entity(parent=self, y=self.height)
        camera.parent = self.camera_pivot
        camera.position = Vec3.zero
        camera.rotation = Vec3.zero
        camera.fov = 90

        mouse.locked = True
        self.mouse_sensitivity = Vec2(100)

        self.gravity = 1
        self.grounded = False
        self.jump_height = 2
        self.jump_up_duration = .5
        self.fall_after = .35 # will interrupt jump up
        self.jumping = False
        self.air_time = 0
        self.sprint = False

        self.transitions = { # value / start / reverse / duration
            "sprint": [0, 0, True, .2],
            "break":  [0, 0, True, 1],
            "place":  [0, 0, True, .3],
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
        # for j in range(6): # n° face
        #     uvs = []
        #     for j2 in range(6): uvs.extend(atlas_face_uv(tex_coord(6*4+(0,3)[j==j2])))
        #     self.hover_anim.append(
        #         Mesh(
        #             vertices=[x-Vec3(.5) for x in cube_vertices],
        #             triangles=cube_triangles,
        #             normals=cube_normals,
        #             uvs=uvs,
        #         )
        #     )

        # make sure we don't fall through the ground if we start inside it
        if self.gravity:
            ray = raycast(self.world_position+(0,self.height,0), self.down, traverse_target=self.block_colliders, ignore=self.ignore_list)
            if ray.hit:
                self.y = ray.world_point.y

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
        return self.position+Vec3(0,self.height,0)
    
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
        self.camera_pivot.rotation_x= clamp(self.camera_pivot.rotation_x, -90, 90)

        self.direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
            ).normalized()
        
        # Sprint
        sprint = held_keys["f"]
        if self.sprint != sprint:
            self.activate_trans("sprint", not sprint)
        self.sprint = sprint
        self.speed = 5 + 5*self.transitions["sprint"][0]**2
        camera.fov = 90 + 15*self.transitions["sprint"][0]**2

        # Jump
        if held_keys["space"] and self.grounded:
            self.jump()

        # - Select block
        block_pos, face = dda(self.head, camera.forward)
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
            self.place_block()
            self.activate_trans("place", False)
        elif not mouse.right and self.placing_block:
            self.end_trans("place",0)
            
        # Collisions
        self.collisions()

    def break_block(self):
        self.set_block(*self.selection[0], AIR)

    def place_block(self):
        self.set_block(*(self.selection[0]+face_normals[self.selection[1]]), GRASS)

    def collisions(self):
        # Collision X/Z
        feet_ray = raycast(self.position+Vec3(0,0.5,0), self.direction, traverse_target=self.block_colliders, ignore=self.ignore_list, distance=.5, debug=False)
        head_ray = raycast(self.position+Vec3(0,self.height-.1,0), self.direction, traverse_target=self.block_colliders, ignore=self.ignore_list, distance=.5, debug=False)
        if not feet_ray.hit and not head_ray.hit:
            move_amount = self.direction * time.dt * self.speed

            if raycast(self.position+Vec3(-.0,1,0), Vec3(1,0,0), distance=.5, traverse_target=self.block_colliders, ignore=self.ignore_list).hit:
                move_amount[0] = min(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(-1,0,0), distance=.5, traverse_target=self.block_colliders, ignore=self.ignore_list).hit:
                move_amount[0] = max(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,1), distance=.5, traverse_target=self.block_colliders, ignore=self.ignore_list).hit:
                move_amount[2] = min(move_amount[2], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,-1), distance=.5, traverse_target=self.block_colliders, ignore=self.ignore_list).hit:
                move_amount[2] = max(move_amount[2], 0)
            self.position += move_amount

            # self.position += self.direction * self.speed * time.dt


        # Collision Y
        if self.gravity:
            # gravity
            ray = raycast(self.world_position+(0,self.height,0), self.down, traverse_target=self.block_colliders, ignore=self.ignore_list)

            if ray.distance <= self.height+.1:
                if not self.grounded:
                    self.land()
                self.grounded = True
                # make sure it's not a wall and that the point is not too far up
                if ray.world_normal.y > .7 and ray.world_point.y - self.world_y < .5: # walk up slope
                    self.y = ray.world_point[1]
                return
            else:
                self.grounded = False

            # if not on ground and not on way up in jump, fall
            self.y -= min(self.air_time, ray.distance-.05) * time.dt * 100
            self.air_time += time.dt * .25 * self.gravity


       

    def input(self, key):
        if key == 'space':
            self.jump()

    def jump(self):
        if not self.grounded: return

        self.grounded = False
        self.animate_y(self.y+self.jump_height, self.jump_up_duration, resolution=int(1//time.dt), curve=curve.out_expo)
        invoke(self.start_fall, delay=self.fall_after)

    def start_fall(self):
        self.y_animator.pause()
        self.jumping = False

    def land(self):
        self.air_time = 0
        self.grounded = True

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

