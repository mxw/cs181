#!/usr/bin/python
# CS 181, HW 3

from random import *
from utils import *
from math import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy

DATAFILE = "adults.txt"
SDATAFILE = "adults-small.txt"

# parse a CSV
def parse_file(filename):
    fin = open(filename, 'r')
    lines = [line.strip().split(',') for line in fin.readlines()]
    fin.close()

    data = [[float(x) for x in row if x.strip() != ''] for row in lines]
    return data


def kmeans(data, K, return_clusters=False):
    N = len(data)
    # pick K distinct points as initial centroids
    centroids = sample(data, min(N,K))
    
    data_centroids = [centroids[0] for i in range(N)]
    changed = True
    while changed:
        changed = False
        for i in range(N):
            new_centroid = argmin(centroids, lambda c : square_distance(data[i], c))
            if new_centroid != data_centroids[i]:
                changed = True
            data_centroids[i] = new_centroid

        centroids = [centroid([data[i] for i in range(N) if data_centroids[i] == c]) for c in centroids]

    
    

    # return clusters if necessary
    if return_clusters:
        clusters = []
        for c in set([tuple(c) for c in centroids]):
            clusters.append([data[i] for i in range(N) if data_centroids[i] == list(c)])

        return clusters

    print centroids, [data_centroids.count(c) for c in centroids]
    # calculate mean squared error
    mse = 0
    for i in range(N):
        mse += square_distance(data_centroids[i], data[i])

    mse /= N
    return mse

def hac(data, K, cf): 
    N = len(data)
    clusts = [[data[i]] for i in range(N)]
    
    while len(clusts) > K:
        b = (0, 1)
        min_dist = 1000000000
        for i in range(len(clusts) - 1):
            for j in range(i + 1, len(clusts)):
                dist = cf(clusts[i], clusts[j], square_distance)
                if dist < min_dist:
                    min_dist = dist
                    b = (i, j)
    
        (i, j) = b
        clusts = [clusts[i] + clusts[j]] + clusts[0:i] + clusts[i + 1:j] + clusts[j+1:]

    #print [len(clust) for clust in clusts]
    print [centroid(clust) for clust in clusts]
    return clusts



# logsumexp a list of logs
def logsumexp(l):
    maxlog = max(l)
    return maxlog + log(sum(exp(x - maxlog) for x in l))


# safe log function
def lg(x):
    if x != 0:
        return log(x)
    else:
        return -(1e300)

# get bounds of a list
def bounds(l):
    return [min(l), max(l)]

# categorical pdf
def categorical(x, bins, ps):
    for i in range(len(bins)):
        if bins[i][0] <= x <= bins[i][1]:
            return ps[i]

def binof(x, bins):
    for i in range(len(bins)):
        if bins[i][0] <= x <= bins[i][1]:
            return i

def rand_sum_to(s, k):
    ret = []
    t = s
    for i in range(k - 1):
        ret.append(uniform(0, t))
        t -= ret[-1]
    ret.append(s - sum(ret))
    return ret

def flatten(l):
    return [x for sl in l for x in sl]

def autoclass(data, K):

    N, D = len(data), len(data[0])

    # discretize each continuous variable into N_BINS bins, using K-means to select bin ranges for each attribue
    N_BINS = 5
    values = [kmeans([[x] for x in sorted(list(set([row[d] for row in data])))], N_BINS, True) for d in range(D)]
    values = [[[x[0] for x in y] for y in row] for row in values]
    bins = [sorted([bounds(bin) for bin in row]) for row in values]

    # params for each categorical distribution
    ps = [[rand_sum_to(1, len(bins[i])) for i in range(D)] for k in range(K)]
    
    # intermediate products and gamma_{nk}
    P = [[0 for k in range(K)] for n in range(N)]
    gamma = [[0 for k in range(K)] for n in range(N)]

    # P(Y_n = k)
    py = [1.0 / K for k in range(K)]

    likelihoods = []

    while True:
        # E step
        for n in range(N):
            for k in range(K):
                P[n][k] = sum(lg(categorical(data[n][d], bins[d], ps[k][d])) for d in range(D))

            # need to normalize the gammas
            denom = logsumexp([lg(py[k]) + P[n][k] for k in range(K)])
            for k in range(K):
                gamma[n][k] = exp(lg(py[k]) + P[n][k] - denom)

        # calculate log-likelihood
        likelihood = 0
        for n in range(N):
            for k in range(K):
                likelihood += gamma[n][k] * (log(py[k]) + P[n][k])
        print likelihood
        likelihoods.append(likelihood)

        # store old parameters
        oldps = flatten(flatten(ps))
        Nhat = [sum(gamma[n][k] for n in range(N)) for k in range(K)]
        # print Nhat

        # M step
        for k in range(K):
            for d in range(D):
                for i in range(len(ps[k][d])):
                    ps[k][d][i] = (1 / Nhat[k]) * sum(gamma[n][k] for n in range(N) if i == binof(data[n][d], bins[d]))
    
        newps = flatten(flatten(ps))

        # check convergence condition on parameters
        if square_distance(oldps, newps) < 10**(-5):
            break


    # calculate clusters
    clusters = [[] for k in range(K)]
    for n in range(N):
        for k in range(K):
            P[n][k] = sum(lg(categorical(data[n][d], bins[d], ps[k][d])) for d in range(D))

        denom = logsumexp([lg(py[k]) + P[n][k] for k in range(K)])
        # classify using argmax of gammas
        maxk, maxgamma = 0, 0
        
        for k in range(K):
            gamma[n][k] = exp(lg(py[k]) + P[n][k] - denom)
            if gamma[n][k] > maxgamma:
                maxgamma = gamma[n][k]
                maxk = k
        clusters[maxk].append(data[n])

    print [len(c) for c in clusters]
    centroids = [centroid(c) for c in clusters]
    print "Centroids:", centroids

    mse = 0
    for i in range(K):
        mse += sum(square_distance(centroids[i], d) for d in clusters[i])

    mse /= N
    print "MSE:", mse


    return likelihoods

def scatter_3D(clusts, metric):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    colors = 'rbgyo'

    N = 0
    for i in range(len(clusts)):
        N += len(clusts[i])
        xs = [clusts[i][j][0] for j in range(len(clusts[i]))]
        ys = [clusts[i][j][1] for j in range(len(clusts[i]))]
        zs = [clusts[i][j][2] for j in range(len(clusts[i]))]
        ax.scatter(xs, ys, zs, color=colors[i])

    plt.title("HAC, K = %d, N = %d, %s metric" % (len(clusts), N, metric))
    plt.savefig("HAC_%d_%d_%s.pdf" % (len(clusts), N, metric))


def main():
    seed()

    # change these to run particular experiments
    DO_KMEANS = False

    if DO_KMEANS:
        data = parse_file(DATAFILE)
        mses = []
        for K in range(2, 11):
            mses.append(kmeans(data[:1000], K))

        print mses


        plt.plot(range(2,11), mses)
        plt.xlabel("K")
        plt.ylabel("Mean squared error")
        plt.title("Number of clusters (K) vs Mean squared error")
        plt.show()


    DO_HAC = False
    if DO_HAC:
        data = parse_file(SDATAFILE)
        clusts = hac(data[:100], 4, cmin)
        scatter_3D(clusts, "min")

        clusts = hac(data[:100], 4, cmax)
        scatter_3D(clusts, "max")

        clusts = hac(data[:200], 4, cmean)
        scatter_3D(clusts, "mean")

        clusts = hac(data[:200], 4, ccent)
        scatter_3D(clusts, "cent")

    DO_AUTOCLASS = True

    if DO_AUTOCLASS:
        data = parse_file(DATAFILE)
        autoclass(data[:1000], 4)

        # con_likelihoods = []
        # for K in range(2, 11):
        #     print K
        #     likelihoods = autoclass(data[:1000], K)
        #     con_likelihoods.append(likelihoods[-1])

        # plt.plot(range(2, 11), con_likelihoods)
        # plt.xlabel("K")
        # plt.ylabel("log-likelihood")
        # plt.title("AutoClass: Number of clusters vs ending log-likelihood")
        # plt.show()
        # autoclass()


if __name__ == '__main__':
    main()

