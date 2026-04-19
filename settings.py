from itertools import product
from math import floor

RENDER_DISTANCE = 5
RENDER_COORDS = list(product(range(2*RENDER_DISTANCE+1), range(2*RENDER_DISTANCE+1)))

CHUNK_W = 8
CHUNK_H = 40
CHUNK_COORDS = list(product(range(CHUNK_W), range(CHUNK_H), range(CHUNK_W)))

y_inbounds = lambda y: 0 <= y < CHUNK_H
chunk_inbounds = lambda x,z: 0<=x<CHUNK_W and 0<=z<CHUNK_W
chunk_of_block = lambda wx,wz: (int(wx//CHUNK_W),int(wz//CHUNK_W))
chunk_of_blockv = lambda wv: chunk_of_block(wv[0],wv[2])
local_of_block = lambda wx,wz: (int(wx %CHUNK_W),int(wz %CHUNK_W))
local_of_blockv = lambda wv: (int(wv[0]%CHUNK_W),int(wv[1]),int(wv[2]%CHUNK_W))

MIN_GEN_HEIGHT = 8
SEA_LEVEL = 20
MAX_GEN_HEIGHT = 40
BREAK_DIST = 10

pos_to_block = lambda x,y,z: (int(x//1),int(y//1),int(z//1))
pos_to_blockv = lambda v: pos_to_block(*v)