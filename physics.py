from ursina import *
from settings import *


class Physics(Entity):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.world = game.world

        self.speed = 5
        self.size = kwargs["size"]
        self.velocity = Vec3()

        self.gravity = 1
        self.water_gravity = .4
        self.water_gravity_max = self.water_gravity * 10
        self.grounded = False

        self.jump_force = 14
        self.water_jump_force = 14
        self.jumping = False

        self.traverse_target = scene     # by default, it will collide with everything. change this to change the raycasts' traverse targets.
        self.ignore_list = [self, ]
    
    @property
    def chunk(self):
        return chunk_of_blockv(self.position)
    
    @property
    def block(self):
        return pos_to_blockv(self.position)
    
    @property
    def underwater(self):
        block = pos_to_blockv(self.position+Vec3(0,self.size.y,0))
        return self.world.get_block(*block).type == BT_WATER     

    def jump(self):
        if not self.grounded: return
        self.velocity.y = self.gravity * (self.jump_force,self.water_jump_force)[self.underwater]

    def update(self):
        """ A exécuter après la détermination de velocity !!! """
        # Gravity
        if self.underwater:
            self.velocity.y = max(self.velocity.y - self.water_gravity, -self.water_gravity_max)
        else:
            self.velocity.y -= self.gravity

        # Raycasts
        dv = self.velocity * min(0.1, time.dt)
        r = self.size[0]
        feet_ray = raycast(self.position+Vec3(0,.5,0), dv, traverse_target=self.traverse_target, ignore=self.ignore_list, distance=r, debug=False)
        head_ray = raycast(self.position+Vec3(0,self.size[1]-.1,0), dv, traverse_target=self.traverse_target, ignore=self.ignore_list, distance=r, debug=False)            
        y_ray = raycast(self.position+Vec3(0,self.size[1],0), Vec3(0,-1,0), traverse_target=self.traverse_target, ignore=self.ignore_list, distance=self.size[1], debug=False)            
        xz_ray_hit = feet_ray.hit or head_ray.hit

        # Collisions
        if self.collisions(Vec3(dv.x, 0, 0)) or xz_ray_hit:
            self.velocity.x = 0
        else:
            self.position += Vec3(dv.x, 0, 0)

        if self.collisions(Vec3(0, 0, dv.z)) or xz_ray_hit:
            self.velocity.z = 0
        else:
            self.position += Vec3(0, 0, dv.z)

        self.grounded = False
        if self.collisions(Vec3(0, dv.y, 0)) or y_ray.hit:
            self.velocity.y = 0
        else:
            self.position += Vec3(0,dv.y,0)

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
        blocks_list = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    block = self.world.get_block(x, y, z)
                    if block.type == BT_SOLID:
                        if dv.y < 0:
                            pos.y = y + 1
                            self.grounded = True
                        if dv.y > 0:
                            pos.y = y - self.size.y
                        blocks_list.append((x,y,z))
        return blocks_list
        