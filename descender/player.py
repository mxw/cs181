import game_interface
import random
import time


########################################
# Initial Variables
########################################

BOUNDS = 25
TICKS = range(-BOUNDS, BOUNDS + 1)
GRID = [(x, y) for x in TICKS for y in TICKS]

## Visited array

seen = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        seen[(x,y)] = '?'

seen[(0, 0)] = 'O'

## Density

# assume uniform density at the start
PLANT_PRIOR_DENSITY = 330.0 / 1680

BIN_RADIUS = 3
BIN_AREA = float((BIN_RADIUS + 1) ** 2)

density = {}
for pos in GRID:
    density[pos] = PLANT_PRIOR_DENSITY


## Life totals
prev_life = 100
prev_pos = (0, 0)

## Plant consumption stats
eaten_nut, eaten_pois = 0, 0

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


def update_density():
    global density



def get_move(view):
    global seen, density, prev_life
    global eaten_nut, eaten_pois

    # use life totals to figure out if a plant was eaten
    if view.GetLife() >= prev_life + 15:
        eaten_nut += 1
        print "Nutricious", prev_life, view.GetLife()
    if view.GetLife() <= prev_life - 8:
        eaten_pois += 1
        print "Poisonous", prev_life, view.GetLife()

    # Eat any plant we find.
    has_plant = view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT

    # print view.GetPlantInfo()

    (X, Y) = (view.GetXPos(), view.GetYPos())

    # cache the previous position and life
    prev_pos = (X, Y)
    prev_life = view.GetLife()

    # update where we have been
    if abs(X) <= BOUNDS and abs(Y) <= BOUNDS and (X,Y) != (0,0):
        seen[(X,Y)] = pl_chr(view.GetPlantInfo())
        # if view.GetPlantInfo() == game_interface.STATUS_NO_PLANT:
        #     seen[(X,Y)] = '.'

    # return a random move (CHANGE)
    return (random.randint(0, 3), has_plant)




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
        return '\033[1;31m%s\033[m' % s
    if s == '.':
        return '\033[1;35m%s\033[m' % s
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

    print eaten_nut, eaten_pois, area