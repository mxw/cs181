#
# clust.rb - Cluster ALL the adults.
#

require 'rubygems'

require 'matrix'
require 'optparse'
require 'ostruct'
require 'set'
require 'rubystats'

USAGE = "Usage: ./clust.rb [options] algorithm"

class Array
  def mean
    begin
      inject(:+) / size.to_f
    rescue NoMethodError
      nil
    end
  end

  def variance
    mu = mean
    map { |i| (i - mu)**2 } / size
  end

  def std_dev
    Math.sqrt(variance)
  end
end


###############################################################################
#
#  Utility routines.
#

#
# parse_input - Parse n lines of data from an image file as flat vectors,
# stratified by classification.
#
def parse_input(fname, n)
  examples = Array.new(2) { Array.new }

  File.open(fname, 'r').each.take(7*n).each_slice(7) do |img|
    i = img.shift[1..-1].to_i
    examples[i] << Vector[*img.join.strip.split.map(&:to_f)]
  end

  examples
end

#
# Compute the square distance between two vectors.
#
def square_distance(x, y)
  x.collect2(y) { |xi, yi| (xi - yi) ** 2 }.inject(:+).to_f
end

#
# Compute the mean squared error for a clustering.
#
def mean_squared_error(clusters)
  clusters.inject(0.0) do |error, c|
    mean = c.mean
    c.inject(error) { |error, x| error + square_distance(x, mean) }
  end / clusters.flatten(1).size
end


###############################################################################
#
#  K-Means Clustering.
#

#
# K-means algorithm.
#
def k_means_cluster(examples, ksize)
  clusters = Array.new(ksize) { [] }
  means = Array.new(ksize) { examples.sample }

  loop do
    prev = clusters
    clusters = Array.new(ksize) { [] }

    # Determine the nearest prototype for each x.
    examples.each do |x|
      kmin = ksize.times.min_by { |k| square_distance(x, means[k]) }
      clusters[kmin] << x
    end

    # Check for convergence.
    break means if prev == clusters

    # Update means.  If we found an empty cluster, initialize its corresponding
    # mean to a random example.
    means = clusters.map(&:mean)
    means.map { |mu| if mu.nil? then examples.sample else mu end }
  end
end

#
# nearest_k_mean - Determines the mean closest to a given example, along with
# its square distance from the mean.
#
def nearest_k_mean(x, means)
  means.map { |mu| [mu, square_distance(mu, x)] }.min_by(&:last)
end


###############################################################################
#
#  Autoclass Clustering.
#

#
# Autoclass errors.
#
class AutoclassVectorMismatchError < StandardError; end
class AutoclassAttrKindError < StandardError; end

class BernoulliParams
  def initialize(examples)
    @p = prng.rand
  end

  def prob(feature)
    feature ? @p : 1 - @p
  end
end

class GaussianParams
  def initialize(examples)
    @mu = examples.mean
    @sig = examples.variance
  end

  def prob(feature)
    Rubystats::NormalDistribution.new(@mu, @sig).pdf(feature)
  end
end

#
# Autoclass algorithm.
#
def autoclass_cluster(examples, ksize, epsilon, attr_kinds)
  unless attr_kinds.size == examples.first.size
    raise AutoclassVectorMismatchError
  end

  prng = Random.new(0)
  dsize = attr_kinds.size

  # Parameter of cluster distribution.  Modeled by a categorical distribution
  # and thus equal to p(C = k).
  theta_c = Array.new(ksize) { 1 / ksize.to_f }

  # Perform k-means clustering to initialize continuous parameters.
  k_clusts = k_means_cluster(examples, ksize)

  # Parameter(s) of feature distribution conditional on cluster.
  #
  # For binary attributes, this is modeled by a Bernoulli distribution and thus
  # is equal to p(X_d >= 0.5 | C = k).  (Note that we assume binary features
  # range between 0.0 and 1.0 and should be divided at the midpoint.)
  #
  # For continuous attributes, this is modeled by a Gaussian distribution and
  # is the array [mu, sigma^2] of the Gaussian parameters.
  theta_attrs = Array.new(ksize) do |k|
    Array.new(dsize) do |d|
      case attr_kinds[d]
      when :bin
        # Choose a random p for Bernoulli.
        prng.rand
      when :cn
        # Initialize mu and sigma^2 based on k-means clusters.
        attrs = k_clusts[k].map { |x| x[d] }
        [attrs.mean, attrs.variance]
      else
        raise AutoclassAttrKindError
      end
    end
  end

  # Posterior probabilities of clusters; p(C = k | x).
  gamma = Array.new(examples.size) { Array.new(ksize) { 0.0 } }

  loop do
    # Expected cluster sizes.
    n = Array.new(ksize) { 0.0 }

    # Expected number of examples in each cluster with positive binary feature
    # d.  Ignored for continuous features.
    n_attrs = Array.new(ksize) { Array.new(dsize) { 0.0 } }

    # Expected likelihood; p(x).
    px = Array.new(examples.size) { 0.0 }

    # Re-estimate posterior probability.
    examples.each_with_index do |x, i|
      # p(C = k) p(x | C = k)
      p = Array.new(ksize) { 0.0 }

      ksize.times do |k|
        p[k] = dsize.times.inject(theta_c[k]) do |p, d|
          case attr_kinds[d]
          when :bin
            p * (x[d] ? theta_attrs[k][d] : 1 - theta_attrs[k][d])
          when :cn
            p * gaussian(x[d], *theta_attrs[k][d])
          end
        end
      end

      px[i] = p.inject(:+)

      # Update the posteriors.
      ksize.times do |k|
        gamma[i][k] = p[k] / px[i]
        n[k] += gamma[i][k]

        dsize.times do |d|
          if attr_kinds[d] == :bin and x[d] > 0.5
            n_attrs[k][d] += gamma[i][k]
          end
        end
      end
    end

    # Maximize and check convergence.
    converged = ksize.times.inject(true) do |converged, k|
      prev = theta_c[k]
      theta_c[k] = n[k] / examples.size

      converged = converged && ((theta_c[k] - prev).abs < epsilon)

      dsize.times.inject(converged) do |converged, d|
        prev = theta_attrs[k][d]
        theta_attrs[k][d] = n_attrs[k][d] / n[k]

        converged && ((theta_attrs[k][d] - prev).abs < epsilon)
      end
    end

    # Print log likelihood.
    puts px.map { |p| Math.log(p) }.inject(:+) if @options.raw

    break if converged
  end

  clusters = Array.new(ksize) { [] }

  # Choose clusters.
  examples.size.times do |i|
    clusters[gamma[i].each_with_index.min.last] << examples[i]
  end

  clusters
end


###############################################################################
#
#  Main routine.
#

@options = OpenStruct.new
@options.file = '../data/plants0.dat'
@options.test = '../data/plants1.dat'
@options.k = [3, 1]
@options.n = 10000
@options.raw = false

OptionParser.new do |opts|
  opts.banner = USAGE

  opts.on("-f", "--inputfile FILE", String, "Data file") do |o|
    @options.file = o
  end

  opts.on("-t", "--testfile FILE", String, "Test file") do |o|
    @options.test = o
  end

  opts.on("-k", "--num-clusters K0,K1", Array, "Number of clusters") do |o|
    abort 'Two k-values required' unless o.size == 2
    @options.k = o
  end

  opts.on("-n", "--num-examples N", Integer, "Number of examples") do |o|
    @options.n = o
  end

  opts.on("-r", "--raw-output", "Print raw output for writeup") do |o|
    @options.raw = o
  end
end.parse!

abort USAGE if ARGV[0].nil?

# Extract plant images.
poisonous, nutritious = parse_input(@options.file, @options.n)
ptest, ntest = parse_input(@options.test, @options.n)

case ARGV[0]
when 'kmeans'
  pmeans = k_means_cluster(poisonous, @options.k[0])
  nmeans = k_means_cluster(nutritious, @options.k[1])

  correct = 0

  ntest.each do |x|
    _, ndist = nearest_k_mean(x, nmeans)
    _, pdist = nearest_k_mean(x, pmeans)

    correct += 1 if ndist < pdist
  end

  ptest.each do |x|
    _, ndist = nearest_k_mean(x, nmeans)
    _, pdist = nearest_k_mean(x, pmeans)

    correct += 1 if pdist < ndist
  end

  puts 'Performance: %f' % (correct / (ntest.size + ptest.size).to_f)
when 'autoclass'
  abort 'Autoclass unimplemented'
else
  abort 'Invalid clustering algorithm'
end
