import sys
import time
from itertools import *
import game_interface

BOUNDS = 25
NIMGS = 10

plants = []
life, prev_life = 100, 100
target = (-BOUNDS, -BOUNDS)

f = open('plants.dat', 'a')

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

def next_target((x, y)):
    if y == BOUNDS:
        if x == BOUNDS:
            return None
        else:
            return (x + 1, -BOUNDS)
    else:
        return (x, y + 1)

def next_move((x, y), (tx, ty)):
    if x != tx:
        return game_interface.LEFT if tx < x else game_interface.RIGHT
    if y != ty:
        return game_interface.DOWN if ty < y else game_interface.UP

def get_move(view):
    global plants, life, prev_life, target

    # Pull data.
    has_plant = view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT
    pos = (view.GetXPos(), view.GetYPos())
    prev_life, life = life, view.GetLife()

    should_eat = pos == target and has_plant

    # Write out the data for all plant images we obtained.
    if plants:
        nutritious = life > prev_life

        for plant in plants:
            image = '\n'.join([' '.join(row) for row in plant])
            f.write('#%d\n' % nutritious)
            f.write('%s\n' % image)

        plants = []

    # If we've swept the board, abort.
    if target is None:
        sys.exit()

    # If we hit our target, snap photos if possible.
    if pos == target:
        if has_plant:
            for _ in xrange(NIMGS):
                image = [str(px) for px in view.GetImage()]
                plants.append(grouper(image, 6))
        target = next_target(target)

    # Decide where to move next.
    if target is None:
        move = game_interface.UP
    else:
        move = next_move(pos, target)

    return (move, should_eat)
