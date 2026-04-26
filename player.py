from ursina import *
from dda import dda
from physics import Physics
from world import *
from ursina.shaders import basic_lighting_shader

text = Text()

class Player(Physics):
    def __init__(self, game, **kwargs):
        super().__init__(game, size=Vec3(.5,1.8,.5), **kwargs)

        self.cam_off = Vec3(0, 1.5, 0)
        self.camera_pivot = Entity(parent=self, position=self.cam_off)
        camera.parent = self.camera_pivot
        camera.position = Vec3.zero
        camera.rotation = Vec3.zero
        camera.fov = 90

        mouse.locked = True
        self.mouse_sensitivity = Vec2(100)

        self.jump_force = 20
        self.water_jump_force = 14
        self.jumping = False
        self.sprint = False
        self.fly = False

        self.inventory = [(PLANKS,10) for _ in range(10)]
        self.slot = 0

        self.transitions = { # value / start / reverse / duration
            "sprint": [0, 0, True, .2],
            "break":  [0, 0, True, .25],
            "place":  [0, 0, True, .25],
        } 
        
        self.on_destroy = self.on_disable

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
        self.world.spawn(self.position, "cow")

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
        # hide selection block
        else:
            self.selection = None
            self.breaking_cube.visible_setter(False)
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
        self.breaking_cube.alpha_setter(0)
        
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
        if mouse.right and not self.placing_block and not self.breaking_block and self.selection:
            if self.place_block():
                self.activate_trans("place", False)
        elif not mouse.right and self.placing_block:
            self.end_trans("place",0)
        
        # - Placement
        if mouse.middle and not self.placing_block and not self.breaking_block and self.selection:
            self.inventory[self.slot] = (self.world.get_block(*self.selection[0]), self.inventory[self.slot][1])
        
        ## Movement
        # Direction
        direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()

        # Fly
        if self.fly:
            self.velocity = direction * self.speed + (self.up * (held_keys["space"]-held_keys["shift"]) + direction) * self.speed
            self.position += self.velocity * min(0.1, time.dt)
            return
        else:
            self.velocity.xz = direction.xz * self.speed
        
        # Underwater
        if self.underwater:
            if held_keys["space"]:
                self.velocity.y += self.water_gravity * 2
            if held_keys["shift"]:
                self.velocity.y -= self.water_gravity

        # Collisions
        super().update()

    def break_block(self):
        self.world.break_block(*self.selection[0])

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
            return self.world.set_block(x,y,z, self.inventory[self.slot][0])
        else:
            return False

    def jump(self):
        if not self.grounded: return
        self.velocity.y = self.gravity * (self.jump_force,self.water_jump_force)[self.underwater]

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


    def input(self, key):
        global _scroll
        match key:
            case "tab":
                self.fly = not self.fly
            case "scroll up":
                _scroll = not _scroll
                self.slot = max(0, self.slot-_scroll)
            case "scroll down":
                _scroll = not _scroll
                self.slot = min(INV_SIZE-1, self.slot+_scroll)
_scroll = True