from world import *
from ursina import *

def dda(get_block, start_pos, direction, chunk):
    # Initialisation des variables de direction et de position
    player_block = Vec3(floor(start_pos.x),floor(start_pos.y),floor(start_pos.z))
    block = Vec3(player_block)
    offset = start_pos - block

    # Détermination de la direction de déplacement dans chaque axe (X, Y, Z)
    step = Vec3(
        (-1,1)[direction.x>0],
        (-1,1)[direction.y>0],
        (-1,1)[direction.z>0],
    )
    # Calcul des distances unitaires de déplacement dans chaque axe
    distUnitX = float("inf") if direction.x == 0 else abs(1 / direction.x)
    distUnitY = float("inf") if direction.y == 0 else abs(1 / direction.y)
    distUnitZ = float("inf") if direction.z == 0 else abs(1 / direction.z)
                 
    # Initialisation des distances initiales pour chaque axe
    distToX = (offset.x,1-offset.x)[step.x==1] * distUnitX
    distToY = (offset.y,1-offset.y)[step.y==1] * distUnitY
    distToZ = (offset.z,1-offset.z)[step.z==1] * distUnitZ

    # Tant que la distance totale n'a pas dépassé la distance maximale
    while (min(distToX,distToY,distToZ) <= BREAK_DIST):
        # On avance dans l'axe ayant la distance la plus courte
        if (distToX <= distToY and distToX <= distToZ):
            block.x += step.x
            distToX += distUnitX
            face = (FLEFT,FRIGHT)[step.x < 0] # on entre dans le bloc par la face opposée à step
            
        elif (distToY <= distToZ):
            block.y += step.y
            distToY += distUnitY
            face = (FDOWN,FUP)[step.y < 0] 

        else:
            block.z += step.z
            distToZ += distUnitZ
            face = (FBACK,FFRONT)[step.z < 0] 
            
        # Bloc solide
        blocktype = get_block(*block)
        solid = blocktype != AIR
        if (solid and block != player_block):
            return block, face

    # Retourne une valeur par défaut si aucun bloc solide n'est touché
    return None, None