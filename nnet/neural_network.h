/**
 * neural_network.h - Neural network types.
 */
#ifndef __NEURAL_NETWORK_H__
#define __NEURAL_NETWORK_H__

#include <set>
#include <vector>
#include <utility>

class Neuron;

/**
 * Example for network actuation.
 */
struct Example {
  Example(std::vector<double> input, std::vector<double> target)
    : input(input), target(target) { }

  std::vector<double> input;
  std::vector<double> target;
};

std::vector<Example> sample_average(std::vector<Example> examples,
    int sample_size, int take);
std::vector<Example> sample_majority(std::vector<Example> examples,
    int sample_size, int take);

/**
 * Neural network edges.
 */
struct Synapse {
  Synapse(Neuron *neuron, double *weight)
    : neuron_(neuron), weight_(weight) { }

  Neuron *neuron_;
  double *weight_;
};

/**
 * Neural network node.
 *
 * Each node maintains a vector of synapses (i.e., edges) from the previous
 * layer and to the subsequent layer in the neural network.
 */
class Neuron {
public:
  Neuron() : bias_(0.5) { }
  ~Neuron();

  std::vector<Synapse>& getPreds() { return preds_; }
  std::vector<Synapse>& getSuccs() { return succs_; }

  void addPred(Neuron *neuron);
  void addPred(Neuron *neuron, double weight);
  void addSucc(Neuron *neuron);
  void addSucc(Neuron *neuron, double weight);

  double *getBiasPtr() { return &bias_; }
  double getActivation() { return activation_; }

  void setValueForInput(double x);
  void computeActivation();
  void computeDescentForOutput(double x);
  void computeDescent();
  void backPropagate(double rate);

private:
  double bias_;
  double activation_;
  double descent_;
  std::vector<Synapse> preds_;
  std::vector<Synapse> succs_;
};

/**
 * Feed-forward neural network.
 */
class NeuralNetwork {
public:
  NeuralNetwork() : NeuralNetwork(0) { }
  NeuralNetwork(unsigned layers) : layers_(layers, std::vector<Neuron *>()),
    inputs_(layers_.front()), outputs_(layers_.back()) { }

  NeuralNetwork(std::vector<unsigned> const& spec, double wmin, double wmax);

  void setVerbose(bool verbose) { verbose_ = verbose; }

  void train(std::vector<Example> const& train_set,
      std::vector<Example> const &valid_set, double rate, int epochs);

  int actuate(std::vector<double> const& input);
  int verify(Example const& example);
  double performance(std::vector<Example> const& examples);

  std::vector<double> save();

private:
  void assertComplete();
  void addNode(Neuron *neuron, unsigned layer);

  void feedForward(std::vector<double> const& input);
  void backPropagate(std::vector<double> const& target, double rate);

  void restore(std::vector<double> const& weights);

  bool verbose_;
  std::vector<std::vector<Neuron *> > layers_;
  std::vector<Neuron *>& inputs_;
  std::vector<Neuron *>& outputs_;
  std::vector<double *> weights_;
};

#endif /* __NEURAL_NETWORK_H__ */
