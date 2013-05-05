/**
 * image.cpp - Image representation.
 */

#include <cstring>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <iostream>

#include "image.h"
#include "neural_network.h"

using namespace std;

/**
 * getPixelEncoding - Return a flattened and normalized pixel matrix.
 */
vector<double>
Image::getPixelEncoding()
{
  vector<vector<double> >::iterator it;
  vector<double>::iterator jt;
  vector<double> encoding;

  for (it = this->pixels.begin(); it != this->pixels.end(); ++it) {
    for (jt = it->begin(); jt != it->end(); ++jt) {
      encoding.push_back((double)*jt);
    }
  }

  return encoding;
}

/**
 * getLabelEncoding - Return a NLABELS vector of 0.0's except in the index of
 * the label, which is 1.0.
 */
vector<double>
Image::getLabelEncoding()
{
  vector<double> encoding(NLABELS, 0.0);

  encoding[this->label] = 1.0;
  return encoding;
}

vector<Image>
file_get_images(const char *filename, int limit)
{
  ifstream f(filename);
  string line;
  int pixel;
  vector<Image> images;

  while (getline(f, line)) {
    if (strchr(line.c_str(), '#') != NULL) {
      // If we found a new image but have hit our limit, quit.
      if ((int)images.size() >= limit && limit != -1) {
        break;
      }

      // Add a new labeled image.
      images.push_back(Image());
      images.back().label = atoi(line.c_str() + 1);
    } else {
      images.back().pixels.push_back(vector<double>());

      istringstream iss(line);
      while (iss >> pixel) {
        images.back().pixels.back().push_back(pixel);
      }
    }
  }

  return images;
}

vector<Example>
encode_images(vector<Image> images)
{
  vector<Image>::iterator it;
  vector<Example> examples;

  for (it = images.begin(); it != images.end(); ++it) {
    examples.push_back(Example(it->getPixelEncoding(), it->getLabelEncoding()));
  }

  return examples;
}
