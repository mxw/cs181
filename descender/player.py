import game_interface
import random
import time


########################################
# Initial Variables
########################################

BOUNDS = 25

## Visited array

seen = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        seen[(x,y)] = '?'

seen[(0, 0)] = 'O'

## Density




########################################
# Move Logic
########################################

# choose the next move given current position and target.
# assumes no noise
def next_move((x, y), (tx, ty)):
    if x != tx:
        return game_interface.LEFT if tx < x else game_interface.RIGHT
    if y != ty:
        return game_interface.DOWN if ty < y else game_interface.UP




def get_move(view):
	return (random.randint(0, 3), False)

########################################
# Debugging/Printing Functions
########################################


def pl_chr(plant_info):
    if plant_info == game_interface.STATUS_UNKNOWN_PLANT:
        return '?'
    if plant_info == game_interface.STATUS_NUTRITIOUS_PLANT:
        return 'N'
    if plant_info == game_interface.STATUS_POISONOUS_PLANT:
        return 'P'
    return ' '

def colorize(s):
    if s == 'N':
        # return ' '
        return '\033[32m' + s + '\033[m'
    if s == 'O':
        return '\033[1;36m%s\033[m' % s
    if s == 'P':
        # return ' '
        return s
    return s

def print_board():
    nut, pois = 0, 0
    area = 1.0 * (2*BOUNDS + 1) ** 2

    for x in range(-BOUNDS, BOUNDS+1):
        for y in range(-BOUNDS, BOUNDS+1):
            nut += 1 if seen[(x,y)] == 'N' else 0
            pois += 1 if seen[(x,y)] == 'P' else 0

    for y in range(-BOUNDS, BOUNDS+1):
            print '' +''.join([colorize(seen[(x,y)]) for x in range(-BOUNDS, BOUNDS+1)])

    print nut, pois, area