import game_interface
import random
import time


########################################
# Initial Variables
########################################

BOUNDS = 20
TICKS = range(-BOUNDS, BOUNDS + 1)
GRID = [(x, y) for x in TICKS for y in reversed(TICKS)]

## Visited array

seen = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        seen[(x,y)] = '?'

seen[(0, 0)] = 'O'

## Density

# assume uniform density at the start
PLANT_PRIOR_DENSITY = 330.0 / 1680

BIN_RADIUS = 2
BIN_AREA = float((BIN_RADIUS + 1) ** 2)

density = {}
for pos in GRID:
    density[pos] = PLANT_PRIOR_DENSITY

target = (-BOUNDS, -BOUNDS)

## Density update matrix
update_matrix = {}
update_matrix[('.','N')] = PLANT_PRIOR_DENSITY / BIN_AREA * 2
update_matrix[('.','U')] = PLANT_PRIOR_DENSITY / BIN_AREA
update_matrix[('.','P')] = -PLANT_PRIOR_DENSITY / BIN_AREA * 2

## Life totals
prev_life = None
prev_pos = (0, 0)

## Plant consumption stats
eaten_nut, eaten_pois = 0, 0

## Printing constants
NO_PLANT_CHAR = '.'

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
    return random.randint(0, 3)

def neighbors((x, y), r):
    return [(nx, ny) for (nx, ny) in GRID if abs(x - nx) + abs(y - ny) <= r]


def update_density(pos, plant):
    global density
    print pos, plant
    if pos not in GRID:
        return

    if plant == NO_PLANT_CHAR:
        for n_pos in neighbors(pos, BIN_RADIUS):
            density[n_pos] -= PLANT_PRIOR_DENSITY / BIN_AREA
        density[pos] = -9999
    elif plant == 'U':
        for n_pos in neighbors(pos, BIN_RADIUS):
            density[n_pos] += 4 * PLANT_PRIOR_DENSITY / BIN_AREA

def densest_pos():
    max_density = 0
    best_pos = []
    for pos in GRID:
        if density[pos] > max_density:
            best_pos = [pos]
            max_density = density[pos]
        elif density[pos] == max_density:
            best_pos.append(pos)

    return random.choice(best_pos)

def next_target((X, Y)):
    if Y == BOUNDS:
        return (X + 1, -BOUNDS)
    return (X, Y + 1)

def get_move(view):
    global seen, density, prev_life, prev_pos
    global eaten_nut, eaten_pois
    global target

    # get starting life only at the start of the game
    if prev_life == None:
        prev_life = view.GetLife()

    ate_plant = False
    # use life totals to figure out if a plant was eaten
    if view.GetLife() >= prev_life + 15:
        eaten_nut += 1
        print "Nutricious", prev_life, view.GetLife()
        seen[prev_pos] = 'N'
        ate_plant = True
    if view.GetLife() <= prev_life - 8:
        eaten_pois += 1
        print "Poisonous", prev_life, view.GetLife()
        seen[prev_pos] = 'P'
        ate_plant = True

    # update the density
    update_density(prev_pos, seen[prev_pos])

    # target the densest spot
    target = densest_pos()

    # Eat any plant we find.
    has_plant = view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT

    # print view.GetPlantInfo()

    (X, Y) = (view.GetXPos(), view.GetYPos())

    # cache the previous position and life
    prev_pos = (X, Y)
    prev_life = view.GetLife()

    # update where we have been
    if abs(X) <= BOUNDS and abs(Y) <= BOUNDS and (X,Y) != (0,0):
        # seen[(X,Y)] = pl_chr(view.GetPlantInfo())
        if view.GetPlantInfo() == game_interface.STATUS_NO_PLANT:
            seen[(X,Y)] = '.'
        if view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT:
            seen[(X,Y)] = 'U'

    # time.sleep(0.1)
    # return a random move (CHANGE)
    return (next_move((X, Y), target), random.choice([True, False]) if has_plant else False)




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
    if s == 'U':
        # return ' '
        return '\033[1;33m%s\033[m' % s
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

    seen[densest_pos()] = 'D'

    for y in reversed(range(-BOUNDS, BOUNDS+1)):
            print '' +''.join([colorize(seen[(x,y)]) for x in range(-BOUNDS, BOUNDS+1)])

    print eaten_nut, eaten_pois, area
    