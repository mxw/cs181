/**
 * main.cpp
 */

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <unistd.h>

#include "neural_network.h"
#include "image.h"
#include "util.h"

using namespace std;

#define USAGE "Usage: ./main -e EPOCHS -r RATE -l LAYERS [-h HIDDENS]\n"

int
main(int argc, char *argv[])
{
  int c, n, epochs, layers;
  double rate;
  bool verbose;
  vector<unsigned> hiddens;
  istringstream iss;

  epochs = 0;
  layers = 0;
  rate = 0.0;
  verbose = false;

  while ((c = getopt(argc, argv, "e:r:l:h:v")) != -1) {
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
        iss.str(optarg);

        while (iss >> n) {
          if (n <= 0) {
            fprintf(stderr, "Number of hidden nodes must be positive.\n");
            return 2;
          }
          hiddens.push_back(n);

          // Skip a comma.
          n = iss.get();
          if (n != -1 && n != ',') {
            fprintf(stderr, "Hidden node counts must be comma-separated.\n");
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
    fprintf(stderr, "Must specify n - 2 hidden node counts for n layers.\n");
    return 2;
  }
  if (rate <= 0.0) {
    fprintf(stderr, "Learning rate must be positive.\n");
    return 2;
  }

  srand(time(NULL));

  vector<Example> train_set, valid_set, test_set;

  train_set = encode_images(file_get_images("corpus/training-9k.txt", -1));
  valid_set = encode_images(file_get_images("corpus/validation-1k.txt", -1));
  test_set  = encode_images(file_get_images("corpus/test-1k.txt", -1));

  vector<unsigned> spec;
  spec.push_back(196);
  spec.insert(spec.end(), hiddens.begin(), hiddens.end());
  spec.push_back(NLABELS);

  NeuralNetwork network(spec, -0.01, 0.01);
  network.setVerbose(verbose);

  network.train(train_set, valid_set, rate, epochs);

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
