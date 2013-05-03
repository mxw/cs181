/**
 * util.c - Various mathy utilities for neural networks.
 */

#include <cmath>
#include <random>

using namespace std;

double
frand(double fmin, double fmax)
{
  static default_random_engine generator;
  static uniform_real_distribution<double> unif(fmin, fmax);

  return unif(generator);
}

double
sigmoid(double x)
{
  double denom;

  denom = 1 + exp(-x);
  if (denom != 0.0) {
    return 1.0 / denom;
  }
  return x < 0 ? 0.0 : 1.0;
}
