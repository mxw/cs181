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
# sample_average - Treat the examples list as a list of samples; for each
# sample_size elements, average ntake of them.
#
def sample_average(examples, sample_size, ntake)
  examples.each_slice(sample_size).map do |sample|
    sample.take(ntake).mean
  end
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
    if prev == clusters
      puts 'MSE: %f' % mean_squared_error(clusters)
      break means
    end

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
# logsumexp - Given an array [ln(x_1), ..., ln(x_n)], make use of log
# identities to compute ln(x_1 + ... + x_n).
#
def logsumexp(logs)
  ml = logs.max
  ml + Math.log(logs.inject(0.0) { |a, l| a + Math.exp(l - ml) })
end

#
# Autoclass algorithm.
#
def autoclass_cluster(examples, ksize, epsilon)
  prng = Random.new(0)
  dsize = examples.first.size

  # Parameter of cluster distribution.  Modeled by a categorical distribution
  # and thus equal to p(C = k).
  theta_c = Array.new(ksize) { 1 / ksize.to_f }

  # Parameters of feature distribution conditional on cluster.  This is modeled
  # by a Bernoulli distribution and is equal to p(X_d = 1 | C = k).
  theta_attrs = Array.new(ksize) { Array.new(dsize) { prng.rand } }

  # Posterior probabilities of clusters; p(C = k | X = x_i).
  gamma = Array.new(examples.size) { Array.new(ksize) { 0.0 } }

  loop do
    # Expected cluster sizes.
    n = Array.new(ksize) { 0.0 }

    # Expected number of examples with feature d in each cluster.
    n_attrs = Array.new(ksize) { Array.new(dsize) { 0.0 } }

    # Re-estimate posterior probability.
    examples.each_with_index do |x, i|
      # log of p(C = k) p(x | C = k).
      p = Array.new(ksize) { 0.0 }

      ksize.times do |k|
        p[k] = dsize.times.inject(Math.log(theta_c[k])) do |p, d|
          p + Math.log(x[d] > 0.5 ? theta_attrs[k][d] : 1 - theta_attrs[k][d])
        end
      end

      denom = logsumexp(p)

      ksize.times do |k|
        # Compute the posterior.
        gamma[i][k] = p[k] / denom

        # Update our expectations.
        n[k] += gamma[i][k]
        dsize.times do |d|
          n_attrs[k][d] += gamma[i][k] if x[d] > 0.5
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

    break if converged
  end

  clusters = Array.new(ksize) { [] }

  # Choose clusters based on the maximum posterior.
  examples.size.times do |i|
    clusters[gamma[i].each_with_index.max.last] << examples[i]
  end
  puts 'MSE: %f' % mean_squared_error(clusters)

  clusters.map(&:mean)
end


###############################################################################
#
#  Main routine.
#

SAMPLES = 10

@options = OpenStruct.new
@options.file = '../data/plants0.dat'
@options.test = '../data/plants1.dat'
@options.k = [3, 1]
@options.n = 10000
@options.eps = 0.000001
@options.samps = nil
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
    abort 'Please provide two values of K' unless o.size == 2
    @options.k = o.map { |k| k.to_i }
  end

  opts.on("-n", "--num-examples N", Integer, "Number of examples") do |o|
    @options.n = o
  end

  opts.on("-e", "--epsilon E", Float, "Convergence epsilon") do |o|
    @options.eps = o
  end

  opts.on("-s", "--sample-size S0,S1", Array, "Average S from each sample") do |o|
    abort 'Please provide two values of S' unless o.size == 2
    @options.samps = o.map { |s| s.to_i }
  end

  opts.on("-r", "--raw-output", "Print raw output for writeup") do |o|
    @options.raw = o
  end
end.parse!

abort USAGE if ARGV[0].nil?

# Extract plant images.
poisonous, nutritious = parse_input(@options.file, @options.n)
ptest, ntest = parse_input(@options.test, @options.n)

if not @options.samps.nil?
  poisonous = sample_average(poisonous, SAMPLES, @options.samps[0])
  nutritious = sample_average(nutritious, SAMPLES, @options.samps[0])
  ptest = sample_average(ptest, SAMPLES, @options.samps[1])
  ntest = sample_average(ntest, SAMPLES, @options.samps[1])
end

case ARGV[0]
when 'kmeans'
  pmeans = k_means_cluster(poisonous, @options.k[0])
  nmeans = k_means_cluster(nutritious, @options.k[1])
when 'autoclass'
  pmeans = autoclass_cluster(poisonous, @options.k[0], @options.eps)
  nmeans = autoclass_cluster(nutritious, @options.k[1], @options.eps)
else
  abort 'Invalid clustering algorithm'
end

# Test performance.
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
