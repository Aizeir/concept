
RENDER_DISTANCE_XZ = 5
RENDER_DISTANCE_Y = 1
render_inbounds = lambda cx,cy,cz: 0<=cx<RENDER_DISTANCE_XZ*2 and 0<=cz<RENDER_DISTANCE_XZ*2 and 0<=cy<RENDER_DISTANCE_Y*2

CHUNK_W = 8
CHUNK_H = 16
chunk_inbounds = lambda x,y,z: 0<=x<CHUNK_W and 0<=z<CHUNK_W and 0<=y<CHUNK_H

FLOOR = 8
MAX_GEN_HEIGHT = 40
BREAK_DIST = 10
