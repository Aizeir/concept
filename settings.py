from itertools import product
from math import floor

RENDER_DISTANCE_XZ = 5
RENDER_DISTANCE_Y = 1
RENDER_COORDS_MAP = list(product(range(2*RENDER_DISTANCE_XZ+1), range(2*RENDER_DISTANCE_Y+1), range(2*RENDER_DISTANCE_XZ+1)))

CHUNK_W = 8
CHUNK_H = 40
CHUNK_COORDS_MAP = list(product(range(CHUNK_W), range(CHUNK_H), range(CHUNK_W)))

chunk_inbounds = lambda x,y,z: 0<=x<CHUNK_W and 0<=y<CHUNK_H and 0<=z<CHUNK_W
chunk_of_block = lambda wx,wy,wz: (int(wx//CHUNK_W),int(wy//CHUNK_H),int(wz//CHUNK_W))
local_of_block = lambda wx,wy,wz: (int(wx %CHUNK_W),int(wy %CHUNK_H),int(wz %CHUNK_W))
chunk_of_blockv = lambda wv: chunk_of_block(*wv)
local_of_blockv = lambda wv: local_of_block(*wv)

MIN_GEN_HEIGHT = 8
SEA_LEVEL = 16
MAX_GEN_HEIGHT = 40
BREAK_DIST = 10

pos_to_block = lambda x,y,z: (int(x//1),int(y//1),int(z//1))
pos_to_blockv = lambda v: pos_to_block(*v)