import game_interface
import random
import time
import nnet
import os


########################################
# Neural Network / Classification code
########################################



WEIGHTS_FILE = 'weights.out'
absolute_path = os.path.dirname(os.path.abspath(__file__)) + '/' + WEIGHTS_FILE

network = nnet.NeuralNetwork.Import(absolute_path)

IMAGES_TO_ASK_FOR = 4

def average_images(l):
    print l
    return [sum(image[i] for image in l) / float(len(l)) for i in range(len(l[0]))]

########################################
# Initial Variables
########################################

BOUNDS = 15
TICKS = range(-BOUNDS, BOUNDS + 1)
GRID = [(x, y) for x in TICKS for y in reversed(TICKS)]

## Visited array

seen = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        seen[(x,y)] = '?'

# seen[(0, 0)] = 'O'

## Belief array
belief = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        belief[(x,y)] = 'U'

vis = {}
for x in range(-BOUNDS, BOUNDS+1):
    for y in range(-BOUNDS, BOUNDS+1):
        vis[(x,y)] = False

vis[(0, 0)] = False

## Density

def dist((x,y), (nx,ny)):
    return abs(x - nx) + abs(y - ny)

# assume uniform density at the start
PLANT_PRIOR_DENSITY = 330.0 / 1680

BIN_RADIUS = 3
BIN_AREA = float((BIN_RADIUS + 1) ** 2)

density = {}
for pos in GRID:
    density[pos] = PLANT_PRIOR_DENSITY

other = {}
for pos in GRID:
    other[pos] = False

target = (-BOUNDS, -BOUNDS)

## Density update matrix
update_matrix = {}
update_matrix[('.','N')] = PLANT_PRIOR_DENSITY / BIN_AREA * 2
update_matrix[('.','U')] = PLANT_PRIOR_DENSITY / BIN_AREA
update_matrix[('.','P')] = -PLANT_PRIOR_DENSITY / BIN_AREA * 2

## Life totals
starting_life = 100
prev_life = None
prev_pos = None

## Plant consumption stats
eaten_nut, eaten_pois = 0, 0

## Printing constants
NO_PLANT_CHAR = '.'

MOVE_THRESHOLD = PLANT_PRIOR_DENSITY + 0.01

########################################
# Move Logic / Density code
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


# update the "nutritious" density
def update_density(pos, plant, ate_plant=True):
    global density
    print pos, plant
    if pos not in GRID:
        return

    if vis[pos]:
        return
    if plant != 'U':
        vis[pos] = True
    if plant == NO_PLANT_CHAR:
        for n_pos in neighbors(pos, BIN_RADIUS):
            density[n_pos] -= 4 * PLANT_PRIOR_DENSITY / BIN_AREA * (BIN_RADIUS - dist(pos, n_pos) + 1) / (BIN_RADIUS + 1)
        density[pos] = -9999
    elif plant == 'U':
        for n_pos in neighbors(pos, BIN_RADIUS):
            density[n_pos] += 5 * PLANT_PRIOR_DENSITY / BIN_AREA * (BIN_RADIUS - dist(pos, n_pos) + 1) / (BIN_RADIUS + 1)
        assert not ate_plant
    elif plant == 'P':
        density[pos] = -9999
        for n_pos in neighbors(pos, BIN_RADIUS):
            density[n_pos] -= 1 * PLANT_PRIOR_DENSITY / BIN_AREA * (BIN_RADIUS - dist(pos, n_pos) + 1) / (BIN_RADIUS + 1)
    elif plant == 'N':
        density[pos] = -9999 
        for n_pos in neighbors(pos, BIN_RADIUS):
            if other[pos]:
                # other player already ate this nutritious plant - he probably ate others in the area as well
                nut_weight = - 2
            else:
                nut_weight = 12
            density[n_pos] += nut_weight * PLANT_PRIOR_DENSITY / BIN_AREA * (BIN_RADIUS - dist(pos, n_pos) + 1) / (BIN_RADIUS + 1)
        density[pos] = -9999

SEARCH_RADIUS = 2

def densest_pos(cur_pos=None):
    max_density = 0
    best_pos = []
    for pos in neighbors(cur_pos, SEARCH_RADIUS):
        if density[pos] > max_density:
            best_pos = [pos]
            max_density = density[pos]
        elif density[pos] == max_density:
            best_pos.append(pos)

    

    if cur_pos != None:
        # best_pos = filter(lambda bp: density[bp] > MOVE_THRESHOLD, neighbors(cur_pos, 5))
        if len(best_pos) == 0:
            best_pos = neighbors(cur_pos, SEARCH_RADIUS)
        # print best_pos, cur_pos
        move = random.choice(sorted(best_pos, key=lambda bp: dist(cur_pos, bp))[0:4])
        # print sorted(map(lambda bp: dist(cur_pos, bp), best_pos))
        return move 
    return best_pos[0]
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
        # print "Nutritious", prev_life, view.GetLife()
        seen[prev_pos] = 'N'
        ate_plant = True
    if view.GetLife() <= prev_life - 8:
        eaten_pois += 1
        # print "Poisonous", prev_life, view.GetLife()
        seen[prev_pos] = 'P'
        ate_plant = True

    # update the density
    print 'Prev_pos:', prev_pos
    if prev_pos in GRID:
        update_density(prev_pos, seen[prev_pos], ate_plant)

    (X, Y) = (view.GetXPos(), view.GetYPos())

    # target the densest spot
    target = densest_pos((view.GetXPos(), view.GetYPos()))

    # Eat any plant we find.
    has_plant = view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT

    # print view.GetPlantInfo()

   

    # cache the previous position and life
    prev_pos = (X, Y)
    prev_life = view.GetLife()

    # update where we have been
    if abs(X) <= BOUNDS and abs(Y) <= BOUNDS:
        # print 'plant info', view.GetPlantInfo()
        # seen[(X,Y)] = pl_chr(view.GetPlantInfo())
        if view.GetPlantInfo() == game_interface.STATUS_NO_PLANT:
            seen[(X,Y)] = '.'
        if view.GetPlantInfo() == game_interface.STATUS_UNKNOWN_PLANT:
            seen[(X,Y)] = 'U'


        seen[(X,Y)] = pl_chr(view.GetPlantInfo())
        if seen[(X,Y)] in ['N', 'P'] and not vis[(X,Y)]:
            # other player already found this plant:
            other[(X,Y)] = True
            pass

    time.sleep(0.1)

    print_board((X,Y))


    # Figure out whether to eat the plant or not...
    if (X,Y) in GRID and has_plant and belief[(X,Y)] != 'P':
        images = []
        for i in range(IMAGES_TO_ASK_FOR):
            images.append(view.GetImage())


        belief[(X,Y)] = 'N' if network.actuate(average_images(images)) else 'P'

        # # if we are in a region with high enough density, eat anyway...
        # if (X,Y) in GRID and belief[(X,Y)] == 'P' and density[(X,Y)] > PLANT_PRIOR_DENSITY + 0.05:
        #     hungry = has_plant
        #     belief[(X, Y)] = 'N'
        if belief[(X,Y)] == 'P':
            # don't go back to an image we think is poisonous
            density[(X,Y)] = -9999

    hungry = has_plant and (X,Y) in GRID and belief[(X, Y)] != 'P'

    # get hungry randomly
    if has_plant and (X,Y) in GRID and belief[(X, Y)] != 'P':
        if view.GetLife() < 50:
            if random.random() < (50 - view.GetLife()) / 100.0:
                hungry = True

    

    return (next_move((X, Y), target), hungry)




########################################
# Debugging/Printing Functions
########################################


def pl_chr(plant_info):
    if plant_info == game_interface.STATUS_UNKNOWN_PLANT:
        return 'U'
    if plant_info == game_interface.STATUS_NUTRITIOUS_PLANT:
        return 'N'
    if plant_info == game_interface.STATUS_POISONOUS_PLANT:
        return 'P'
    return '.'

def colorize(s, pos=None):
    if s == 'N':
        # return ' '
        if pos != None and other[pos]:
            return '\033[38;5;202m' + s + '\033[m'
        else:
            return '\033[32m' + s + '\033[m'
    if s == 'O':
        return '\033[1;36m%s\033[m' % s
    if s == 'P':
        if pos != None and other[pos]:
            return '\033[38;5;245m' + s + '\033[m'
        else:
            return '\033[1;31m%s\033[m' % s
    if s == 'U':
        # return ' '
        return '\033[1;33m%s\033[m' % s
    if s == '.':
        return '\033[1;35m%s\033[m' % s
    if s == 'M':
        return '\033[1;34m%s\033[m' % s
    if s == 'D':
        return '\033[1;32m%s\033[m' % s
    if pos == None:
        return s
    c = 240 if density[pos] < 0 else 250
    if density[pos] > PLANT_PRIOR_DENSITY:
        c = 200
    return '\033[38;5;%dm%s\033[m' % (c,s)

def print_board(pos=None):
    print chr(27) + "[2J"
    nut, pois = 0, 0
    area = 1.0 * (2*BOUNDS + 1) ** 2

    for x in range(-BOUNDS, BOUNDS+1):
        for y in range(-BOUNDS, BOUNDS+1):
            nut += 1 if seen[(x,y)] == 'N' else 0
            pois += 1 if seen[(x,y)] == 'P' else 0

    dense_pos = densest_pos(pos)
    tmpdns, seen[dense_pos] =  seen[dense_pos], 'D'

    if pos != None and pos in GRID:
        tmp = seen[pos]
        seen[pos] = 'M'

    for y in reversed(range(-BOUNDS, BOUNDS+1)):
            print '' +''.join([colorize(seen[(x,y)], (x,y)) for x in range(-BOUNDS, BOUNDS+1)]), 
            print ' '.join(['%0.2f' % (density[(x,y)] if density[(x,y)] > -2 else -5) for x in range(-BOUNDS, BOUNDS+1)])

    if pos != None and pos in GRID:
        seen[pos] = tmp

    seen[dense_pos] = tmpdns

    print eaten_nut, eaten_pois, area
    