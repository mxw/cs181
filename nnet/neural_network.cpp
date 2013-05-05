/**
 * neural_network.cpp - Neural network implementation that takes less than
 * three hours to run.
 */

#include <cstdio>
#include <cassert>
#include <set>
#include <vector>

#include "neural_network.h"
#include "util.h"

using namespace std;


///////////////////////////////////////////////////////////////////////////////
//
//  Example methods
//

/**
 * example_mean - Take the average of a collection of examples, asserting that
 * they have the same label.
 */
static
Example
example_mean(vector<Example> examples)
{
  unsigned i;
  vector<Example>::iterator it;

  Example ex(examples[0].input, examples[0].target);

  for (it = examples.begin(), ++it; it != examples.end(); ++it) {
    for (i = 0; i < it->input.size(); ++i) {
      ex.input[i] += it->input[i];
    }
  }

  for (i = 0; i < ex.input.size(); ++i) {
    ex.input[i] += examples.size();
  }

  return ex;
}

/**
 * sample_average - Treat the examples list as a list of samples; for each
 * sample_size elements, average take of them.
 */
vector<Example>
sample_average(vector<Example> examples, int sample_size, int take)
{
  int i;
  vector<Example>::iterator it;
  vector<Example> means;

  it = examples.begin();

  while (it != examples.end()) {
    vector<Example> sample;

    for (i = 0; i < take; ++i, ++it) {
      sample.push_back(*it);
    }
    for (i = take; i < sample_size; ++i, ++it);

    means.push_back(example_mean(sample));
  }

  return means;
}


///////////////////////////////////////////////////////////////////////////////
//
//  Neuron methods
//

/**
 * ~Neuron - Free all of our input weights.  We leave it to our successor nodes
 * to free our output weights.
 */
Neuron::~Neuron()
{
  vector<Synapse>::iterator it;

  for (it = preds_.begin(); it != preds_.end(); ++it) {
    free(it->weight_);
  }
}

/**
 * addPred - Add an input with a default weight of 0.0.
 */
void
Neuron::addPred(Neuron *neuron)
{
  addPred(neuron, 0.0);
}

/**
 * addPred - Add `neuron' as an input and add ourselves as an output for
 * `neuron', via synapses that share a weight.
 */
void
Neuron::addPred(Neuron *neuron, double weight)
{
  double *wp;

  wp = (double *)malloc(sizeof(*wp));
  assert(wp);
  *wp = weight;

  preds_.push_back(Synapse(neuron, wp));
  neuron->succs_.push_back(Synapse(this, wp));
}

/**
 * addSucc - Add an output with a default weight of 0.0.
 */
void
Neuron::addSucc(Neuron *neuron)
{
  addSucc(neuron, 0.0);
}

/**
 * addSucc - Add `neuron' as an output and add ourselves as an input for
 * `neuron', via synapses that share a weight.
 */
void
Neuron::addSucc(Neuron *neuron, double weight)
{
  double *wp;

  wp = (double *)malloc(sizeof(*wp));
  assert(wp);
  *wp = weight;

  succs_.push_back(Synapse(neuron, wp));
  neuron->preds_.push_back(Synapse(this, wp));
}

/**
 * setValueForInput - Set the activation output manually.  We enforce that this
 * is only done for input nodes, i.e., nodes with no predecessors.
 */
void
Neuron::setValueForInput(double x)
{
  assert(preds_.size() == 0);
  activation_ = x;
}

/**
 * computeActivation - Apply the activation function to the weighted sum of the
 * inputs---i.e., compute g(w'x)---and set the activation field.
 */
void
Neuron::computeActivation()
{
  vector<Synapse>::iterator it;

  activation_ = bias_;
  for (it = preds_.begin(); it != preds_.end(); ++it) {
    activation_ += *(it->weight_) * it->neuron_->activation_;
  }
  activation_ = sigmoid(activation_);
}

/**
 * computeDescentForOutput - Compute the descent factor for an output neuron.
 * We enforce that this is only done for nodes with no successors.
 */
void
Neuron::computeDescentForOutput(double y)
{
  descent_ = (y - activation_) * activation_ * (1 - activation_);
}

/**
 * computeDescent - Compute the descent factor (i.e, 'delta') for hidden nodes
 * for use in the back propagation algorithm.
 */
void
Neuron::computeDescent()
{
  vector<Synapse>::iterator it;

  descent_ = 0.0;
  for (it = succs_.begin(); it != succs_.end(); ++it) {
    descent_ += *(it->weight_) * it->neuron_->descent_;
  }
  descent_ *= activation_ * (1 - activation_);
}

/**
 * backPropagate - Propagate weights backwards based on our computed descent
 * factor and a learning rate.
 */
void
Neuron::backPropagate(double rate)
{
  vector<Synapse>::iterator it;

  double rd = rate * descent_;

  for (it = preds_.begin(); it != preds_.end(); ++it) {
    *(it->weight_) += rd * it->neuron_->activation_;
  }
  bias_ += rd;
}


///////////////////////////////////////////////////////////////////////////////
//
//  NeuralNetwork construction and training methods
//

/**
 * NeuralNetwork - Construct a neural network from a vector specifying the
 * number of nodes per layer.
 */
NeuralNetwork::NeuralNetwork(vector<unsigned> const& spec,
    double wmin, double wmax)
  : layers_(spec.size(), vector<Neuron *>()),
    inputs_(layers_.front()), outputs_(layers_.back())
{
  unsigned i, j;
  vector<Neuron *>::iterator it;
  Neuron *neuron;

  for (i = 0; i < spec.size(); ++i) {
    for (j = 0; j < spec[i]; ++j) {
      neuron = new Neuron();
      addNode(neuron, i);

      if (i > 0) {
        // Add all of the previous layer's neurons as predecessors.
        for (it = layers_[i-1].begin(); it != layers_[i-1].end(); ++it) {
          neuron->addPred(*it, frand(wmin, wmax));
          weights_.push_back(neuron->getPreds().back().weight_);
        }
      }

      weights_.push_back(neuron->getBiasPtr());
    }
  }

  assertComplete();
}

/**
 * addNode - Add a node to the `layer'th layer of the neural network.  This
 * does no other bookkeeping besides adding it to the network's layers vector.
 */
void
NeuralNetwork::addNode(Neuron *neuron, unsigned layer)
{
  assert(layer < layers_.size());
  assert(layer != 0 || neuron->getPreds().size() == 0);

  layers_[layer].push_back(neuron);
}

/**
 * assertComplete - Assert that the feedforward neural network is complete and
 * correct, i.e., all inputs are up one layer, all outputs are down one layer,
 * and the graph is fully connected in one direction with no cycles.
 */
void
NeuralNetwork::assertComplete()
{
  unsigned i;
  vector<vector<Neuron *> >::iterator it;
  vector<vector<Neuron *> >::reverse_iterator itr;
  vector<Neuron *>::iterator jt;
  vector<Synapse>::iterator kt;

  set<Neuron *> seen;
  vector<set<Neuron *> > seen_by_layer;

  // Assert that the input layer has no inputs.
  for (jt = inputs_.begin(); jt != inputs_.end(); ++jt) {
    assert((*jt)->getPreds().size() == 0);
  }

  // Assert that the output layer has no outputs.
  for (jt = outputs_.begin(); jt != outputs_.end(); ++jt) {
    assert((*jt)->getSuccs().size() == 0);
  }

  seen_by_layer = vector<set<Neuron *> >(layers_.size());

  // Assert that each layer's inputs are in the previous layer and that no
  // neuron appears more than once.
  for (it = layers_.begin(), i = 0; it != layers_.end(); ++it, ++i) {
    for (jt = it->begin(); jt != it->end(); ++jt) {
      if (i > 0) {
        vector<Synapse>& synapses = (*jt)->getPreds();
        set<Neuron *>& seen_prev = seen_by_layer[i - 1];

        for (kt = synapses.begin(); kt != synapses.end(); ++kt) {
          assert(seen_prev.find(kt->neuron_) != seen_prev.end());
        }
        assert(synapses.size() == seen_prev.size());
      }

      assert(seen.find(*jt) == seen.end());

      seen.insert(*jt);
      seen_by_layer[i].insert(*jt);
    }
  }

  seen_by_layer = vector<set<Neuron *> >(layers_.size());

  // Assert that each layer's outputs are in the next layer.
  for (itr = layers_.rbegin(), i = 0; itr != layers_.rend(); ++itr, ++i) {
    for (jt = itr->begin(); jt != itr->end(); ++jt) {
      if (i > 0) {
        vector<Synapse>& synapses = (*jt)->getSuccs();
        set<Neuron *>& seen_next = seen_by_layer[i - 1];

        for (kt = synapses.begin(); kt != synapses.end(); ++kt) {
          assert(seen_next.find(kt->neuron_) != seen_next.end());
        }
        assert(synapses.size() == seen_next.size());
      }

      seen_by_layer[i].insert(*jt);
    }
  }
}

/**
 * feedForward - Set the activations of the network's input nodes, then
 * propagate activations through the network.
 */
void
NeuralNetwork::feedForward(vector<double> const& input)
{
  vector<vector<Neuron *> >::iterator it;
  vector<Neuron *>::iterator jt;

  // Assert that we have as many input values as input-layer neurons.
  assert(inputs_.size() == input.size());

  for (jt = inputs_.begin(); jt != inputs_.end(); ++jt) {
    (*jt)->setValueForInput(input[jt - inputs_.begin()]);
  }

  for (it = layers_.begin() + 1; it != layers_.end(); ++it) {
    for (jt = it->begin(); jt != it->end(); ++jt) {
      (*jt)->computeActivation();
    }
  }
}

/**
 * backPropagate - Run the back propagation algorithm on the network.
 */
void
NeuralNetwork::backPropagate(vector<double> const& target, double rate)
{
  vector<vector<Neuron *> >::reverse_iterator it;
  vector<Neuron *>::iterator jt;

  // Assert that we have as many target values as output-layer neurons.
  assert(outputs_.size() == target.size());

  for (jt = outputs_.begin(); jt != outputs_.end(); ++jt) {
    (*jt)->computeDescentForOutput(target[jt - outputs_.begin()]);
  }

  for (it = layers_.rbegin() + 1; it != layers_.rend(); ++it) {
    for (jt = it->begin(); jt != it->end(); ++jt) {
      (*jt)->computeDescent();
    }
  }

  for (it = layers_.rbegin(); it != layers_.rend(); ++it) {
    for (jt = it->begin(); jt != it->end(); ++jt) {
      (*jt)->backPropagate(rate);
    }
  }
}

/**
 * save - Save the state of the network as a vector of weights, including the
 * bias weight.
 */
vector<double>
NeuralNetwork::save()
{
  vector<double> weights;
  vector<double *>::iterator it;

  for (it = weights_.begin(); it != weights_.end(); ++it) {
    weights.push_back(**it);
  }

  return weights;
}

/**
 * restore - Restore the state of the network from a vector of weights.
 */
void
NeuralNetwork::restore(std::vector<double> const& weights)
{
  vector<double *>::iterator it;

  assert(weights.size() == weights_.size());

  for (it = weights_.begin(); it != weights_.end(); ++it) {
    **it = weights[it - weights_.begin()];
  }
}

/**
 * train - Train the network.
 */
void
NeuralNetwork::train(vector<Example> const& train_set,
    vector<Example> const& valid_set, double rate, int epochs)
{
  int i, max_epoch = 0;
  double train_perf, valid_perf, max_perf = 0.0;
  vector<Example>::const_iterator it;
  vector<double> weights;

  assert(epochs > 0);

  for (i = 0; i < epochs; ++i) {
    for (it = train_set.begin(); it != train_set.end(); ++it) {
      feedForward(it->input);
      backPropagate(it->target, rate);
    }
    train_perf = performance(train_set);
    valid_perf = performance(valid_set);

    if (verbose_) {
      printf("%u %2.6f %2.6f\n", i, train_perf, valid_perf);
    }

    // If this is the optimal network so far, save its state.
    if (valid_perf >= max_perf) {
      max_epoch = i;
      max_perf = valid_perf;
      weights = save();
    }
  }

  // If we passed the optimal network, restore it.
  if (max_epoch != epochs - 1) {
    restore(weights);
  }

  // Output the number of training epochs the optimal network underwent.
  if (verbose_) {
    printf("FINAL EPOCH: %d\n", max_epoch);
  }
}


///////////////////////////////////////////////////////////////////////////////
//
//  NeuralNetwork output methods
//

/**
 * actuate - Propagate the signal from an input vector through the neural
 * network and return the output, defined as the index of the output node with
 * the highest activation.
 */
int
NeuralNetwork::actuate(vector<double> const& input)
{
  unsigned i;
  double a;
  pair<int, double> max(0, 0.0);

  assert(inputs_.size() == input.size());
  feedForward(input);

  for (i = 0; i < outputs_.size(); ++i) {
    a = outputs_[i]->getActivation();
    if (a > max.second) {
      max = pair<int, double>(i, a);
    }
  }

  return max.first;
}

/**
 * verify - Test on an example, returning 1 if our output matches the label,
 * else 0.
 */
int
NeuralNetwork::verify(Example const& example)
{
  return example.target[actuate(example.input)] ? 1 : 0;
}

/**
 * performance - Compute the network's performance on a set of examples.
 */
double
NeuralNetwork::performance(vector<Example> const& examples)
{
  int successes = 0;
  vector<Example>::const_iterator it;

  for (it = examples.begin(); it != examples.end(); ++it) {
    successes += verify(*it);
  }

  return (float)successes / examples.size();
}
