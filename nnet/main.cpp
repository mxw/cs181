/**
 * main.cpp
 */

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unistd.h>

#include "neural_network.h"
#include "image.h"
#include "util.h"

using namespace std;

#define USAGE "Usage: ./main -e EPOCHS -r RATE -l LAYERS [-h HIDDENS]\n"

#define IMGSIZE 36
#define SAMPLES 20
#define LIMIT   75000

#define TRAIN_FILE  "../data/plants0.dat"
#define VALID_FILE  "../data/plants1.dat"
#define TEST_FILE   "../data/plants2.dat"

int
main(int argc, char *argv[])
{
  int c, n, epochs, layers;
  double rate;
  bool verbose;
  vector<unsigned> samples;
  vector<unsigned> hiddens;
  istringstream iss;
  ofstream f;

  epochs = 0;
  layers = 0;
  rate = 0.0;
  verbose = false;

  if (argc < 7) {
    fprintf(stderr, USAGE);
    return 1;
  }

  while ((c = getopt(argc, argv, "e:r:l:h:s:v")) != -1) {
    switch (c) {
      case 'e':
        epochs = atoi(optarg);
        break;

      case 'r':
        rate = atof(optarg);
        break;

      case 'l':
        layers = atoi(optarg);
        break;

      case 'h':
        iss.clear();
        iss.str(optarg);

        while (iss >> n) {
          hiddens.push_back(n);

          // Skip a comma.
          n = iss.get();
          if (n != -1 && n != ',') {
            fprintf(stderr, "Hidden node counts must be comma-separated.\n");
          }
        }
        break;

      case 's':
        iss.clear();
        iss.str(optarg);

        while (iss >> n) {
          samples.push_back(n);

          // Skip a comma.
          n = iss.get();
          if (n != -1 && n != ',') {
            fprintf(stderr, "Sample sizes must be comma-separated.\n");
          }
        }
        break;

      case 'v':
        verbose = true;
        break;

      case '?':
        fprintf(stderr, USAGE);
        return 1;

      default:
        abort();
    }
  }

  if (epochs <= 0) {
    fprintf(stderr, "Number of epochs must be positive.\n");
    return 2;
  }
  if (layers <= 0) {
    fprintf(stderr, "Number of layers must be positive.\n");
    return 2;
  }
  if (layers <= 2 && hiddens.size() != 0) {
    fprintf(stderr, "No hidden nodes allowed for < 3 layers.\n");
    return 2;
  }
  if (layers > 2 && hiddens.size() + 2 != (unsigned)layers) {
    fprintf(stderr, "Must specify n-2 hidden node counts for n layers.\n");
    return 2;
  }
  if (samples.size() != 0 && samples.size() != 2) {
    fprintf(stderr, "Must specify exactly two sample sizes.\n");
    return 2;
  }
  if (rate <= 0.0) {
    fprintf(stderr, "Learning rate must be positive.\n");
    return 2;
  }

  srand(time(NULL));

  vector<Example> train_set, valid_set, test_set;

  train_set = encode_images(file_get_images(TRAIN_FILE, LIMIT));
  valid_set = encode_images(file_get_images(VALID_FILE, LIMIT / 10));
  test_set  = encode_images(file_get_images(TEST_FILE,  LIMIT / 10));

  if (samples.size() != 0) {
    train_set = sample_average(train_set, SAMPLES, samples[0]);
    valid_set = sample_average(valid_set, SAMPLES, samples[0]);
    test_set  = sample_average(test_set,  SAMPLES, samples[1]);
  }

  // Create the neural network.
  vector<unsigned> spec;
  spec.push_back(IMGSIZE);
  spec.insert(spec.end(), hiddens.begin(), hiddens.end());
  spec.push_back(NLABELS);

  NeuralNetwork network(spec, -0.01, 0.01);
  network.setVerbose(verbose);

  // Train.
  network.train(train_set, valid_set, rate, epochs);

  // Write out the final weights.
  f.open("weights.out");
  vector<double>::iterator it;
  vector<double> weights = network.save();

  for (it = weights.begin(); it != weights.end(); ++it) {
    f << *it << " ";
  }

  printf(
      "Performance\n"
      "  training:   %lf\n"
      "  validation: %lf\n"
      "  test:       %lf\n",
      network.performance(train_set),
      network.performance(valid_set),
      network.performance(test_set)
  );

  return 0;
}
