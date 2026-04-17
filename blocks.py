

atlas_w = 4
atlas_h = 8
def tex_coord(tex_id):
    return (tex_id%atlas_w, atlas_h-1 - tex_id//atlas_w)

FFRONT,FBACK,FRIGHT,FLEFT,FUP,FDOWN = range(6)

idx = 0
class Block:
    def __init__(self, tex_ids=None, solid=True):
        global idx; self.id = idx; idx += 1
        self.tex_ids = tex_ids
        self.tex_coords = [tex_coord(tex_id) for tex_id in tex_ids] if tex_ids else None
        self.solid = solid
        
    def __repr__(self):
        return f"<Block[{self.id}]>"

AIR = Block()
GRASS = Block([2]*4+[0,1])
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
WATER = Block([17]*6, solid=False)
