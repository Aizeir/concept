


atlas_w = 4
atlas_h = 8
def tex_coord(tex_id):
    return (tex_id%atlas_w, atlas_h-1 - tex_id//atlas_w)


class Block:
    def __init__(self, idx, tex_ids=None):
        self.idx = idx
        self.tex_ids = tex_ids
        self.tex_coords = [tex_coord(tex_id) for tex_id in tex_ids] if tex_ids else None

    def __repr__(self):
        return f"<Block[{self.idx}]>"

AIR = Block(0)
GRASS = Block(1, [0]*6)
