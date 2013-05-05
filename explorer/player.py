import game_interface
import random
import time


BOUNDS = 25
seen = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        seen[(x,y)] = '?'

seen[(0, 0)] = 'O'

target = (-BOUNDS, -BOUNDS)

def next_target((X, Y)):
    if Y == BOUNDS:
        return (X + 1, -BOUNDS)
    return (X, Y + 1)

def next_move((x, y), (tx, ty)):
    if x != tx:
        return game_interface.LEFT if tx < x else game_interface.RIGHT
    if y != ty:
        return game_interface.DOWN if ty < y else game_interface.UP

def pl_chr(plant_info):
    if plant_info == game_interface.STATUS_UNKNOWN_PLANT:
        return '?'
    if plant_info == game_interface.STATUS_NUTRITIOUS_PLANT:
        return 'N'
    if plant_info == game_interface.STATUS_POISONOUS_PLANT:
        return 'P'
    return ' '

prev_life = 10000

def get_move(view):
    global seen, target
    # Update based on life total
    curr_life = view.GetLife()
    #if prev_life - 10 == curr_life:


    # Eat any plant we find.
    hasPlant = view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT

    # Choose a random direction.
    # if hasPlant:
    #     for i in xrange(5):
    #         print view.GetImage()
    #         print view.GetLife()

    # time.sleep(0.1)

    (X, Y) = (view.GetXPos(), view.GetYPos())

    if abs(X) <= BOUNDS and abs(Y) <= BOUNDS and (X,Y) != (0,0):
        seen[(X,Y)] = pl_chr(view.GetPlantInfo())

    if target == (X, Y):
        target = next_target(target)

    #print target
    # walk towards the target.
    return (next_move((X, Y), target), hasPlant)


def colorize(s):
    if s == 'N':
        return '\033[32m' + s + '\033[m'
    if s == 'O':
        return '\033[1;36m%s\033[m' % s
    return s

def print_board():
    nut, pois = 0, 0
    area = 1.0 * (2*BOUNDS + 1) ** 2

    for x in range(-BOUNDS, BOUNDS+1):
        for y in range(-BOUNDS, BOUNDS+1):
            nut += 

    for y in range(-BOUNDS, BOUNDS+1):
            print '' +''.join([colorize(seen[(x,y)]) for x in range(-BOUNDS, BOUNDS+1)])