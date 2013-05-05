#
# nnet.py - Neural network implementation.
#

import math
import random
from itertools import *

NLABELS = 2
SAMPLES = 20
LIMIT = 75000

TRAIN_FILE = "../data/plants0.dat"
VALID_FILE = "../data/plants1.dat"
TEST_FILE  = "../data/plants2.dat"

def sigmoid(x):
    denom = 1 + math.exp(-x)
    if denom != 0.0:
        return 1.0 / denom
    return 0.0 if x < 0 else 1.0

class Weight:
    def __init__(self, value):
        self.value = value

class Example:
    def __init__(self, label):
        self.input = []
        self.target = [1.0 if label == i else 0.0 for i in xrange(NLABELS)]

class Synapse:
    def __init__(self, neuron, weight):
        self.neuron = neuron
        self.weight = weight

class Neuron:
    def __init__(self):
        self.preds = []
        self.succs = []
        self.bias = Weight(0.5)
        self.activation = 0.0

    def addPred(self, neuron, weight=0.0):
        w = Weight(weight)
        self.preds.append(Synapse(neuron, w))
        neuron.succs.append(Synapse(self, w))

    def addSucc(self, neuron, weight=0.0):
        w = Weight(weight)
        self.succs.append(Synapse(neuron, w))
        neuron.preds.append(Synapse(self, w))

    def setValueForInput(self, x):
        self.activation = x

    def computeActivation(self):
        self.activation = self.bias.value
        for syn in self.preds:
            self.activation += syn.weight.value * syn.neuron.activation
        self.activation = sigmoid(self.activation)

class NeuralNetwork:
    def __init__(self, spec, wmin, wmax):
        self.layers = [[] for _ in spec]
        self.inputs = self.layers[0]
        self.outputs = self.layers[-1]
        self.weights = []

        for i, n in enumerate(spec):
            for j in xrange(n):
                neuron = Neuron()
                self.layers[i].append(neuron)

                if i > 0:
                    for other in self.layers[i-1]:
                        neuron.addPred(other, random.uniform(wmin, wmax))
                        self.weights.append(neuron.preds[-1].weight)

                self.weights.append(neuron.bias)

    def feedForward(self, inputv):
        assert len(self.inputs) == len(inputv)

        for neuron, val in zip(self.inputs, inputv):
            neuron.setValueForInput(val)

        for layer in self.layers[1:]:
            for neuron in layer:
                neuron.computeActivation()

    def restore(self, weights):
        assert len(self.weights) == len(weights)

        for w, v in zip(self.weights, weights):
            w.value = v

    def actuate(self, inputv):
        self.feedForward(inputv)

        acts = [(n.activation, i) for (i, n) in enumerate(self.outputs)]
        return max(acts)[-1]

    def verify(self, example):
        return 1 if example.target[self.actuate(example.input)] else 0

    def performance(self, examples):
        return sum(self.verify(ex) for ex in examples) / float(len(examples))


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

def file_get_examples(fname, limit):
    examples = []

    with open(fname, 'r') as f:
        for line in f:
            if line[0] == '#':
                if len(examples) >= limit and limit != -1:
                    break
                examples.append(Example(int(line[1:])))
            else:
                examples[-1].input.extend([float(w) for w in line.split()])

    return examples

def sample_average(examples, sample_size, take):
    means = []

    for sample in grouper(examples, sample_size):
        mu = sample[0]

        for ex in sample[1:take]:
            for i in xrange(len(mu.input)):
                mu.input[i] += ex.input[i]

        mu.input = [v / take for v in mu.input]
        means.append(mu)

    return means


if __name__ == '__main__':
    network = NeuralNetwork([36, 10, 10, 2], -0.01, 0.01)

    with open('weights.out', 'r') as f:
        weights = [float(w) for w in f.read().split()]

    network.restore(weights)

    train_set = file_get_examples(TRAIN_FILE, LIMIT)
    valid_set = file_get_examples(VALID_FILE, LIMIT / 10)
    test_set  = file_get_examples(TEST_FILE,  LIMIT / 10)

    train_set = sample_average(train_set, SAMPLES, 6)
    valid_set = sample_average(valid_set, SAMPLES, 6)
    test_set  = sample_average(test_set,  SAMPLES, 4)

    print (
        "Performance\n"
        "  training:   %lf\n"
        "  validation: %lf\n"
        "  test:       %lf\n" % (
        network.performance(train_set),
        network.performance(valid_set),
        network.performance(test_set))
    );
