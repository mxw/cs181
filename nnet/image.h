/**
 * image.h - Image representation.
 */
#ifndef __NEURAL_NETWORK_IMAGES_H__
#define __NEURAL_NETWORK_IMAGES_H__

#include <vector>

#include "neural_network.h"

#define NLABELS 2

class Image {
public:
  std::vector<std::vector<double> > pixels;
  unsigned label;

  std::vector<double> getPixelEncoding();
  std::vector<double> getLabelEncoding();
};

std::vector<Image> file_get_images(const char *filename, int limit);
std::vector<Example> encode_images(std::vector<Image> images);

#endif /* __NEURAL_NETWORK_IMAGES_H__ */
