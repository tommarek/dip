#!/usr/bin/env python

import numpy as np
import cvxopt
import cvxopt.solvers

from src.kernels import *

class SVM():
    '''
    SVM class
    '''

    def __init__(self, kernel, C=None):
        self.kernel = kernel
        if C:
            self.C = float(C)
        else:
            self.C = None
        # learned svm params
        self.lm = None
        self.lm_count = 0
        self.all_lm_count = 0
        self.b = None
        self.w = None

    def train(self, X, Y):
        '''
        Method for training
        @param X 
        @param Y 
        '''
        n_samples, n_features = X.shape

        # create gram matrix (kernel matrix)
        gram = np.zeros((n_samples, n_samples))
        for i in xrange(n_samples):
            for j in xrange(n_samples):
                gram[i,j] = self.kernel(X[i], X[j])

        # quadratic members coefficient vector
        P = cvxopt.matrix(np.outer(Y, Y) * gram)
        # linear members coefficient vector
        q = cvxopt.matrix(np.ones(n_samples) * -1)

        # set constraints
        # equality constraints left side matrix
        A = cvxopt.matrix(Y, (1, n_samples))
        # equality constraints right side matrix
        b = cvxopt.matrix(0.0)
        # left and right side of inequality constraints matrix
        if self.C:
            tmp1 = np.diag(np.ones(n_samples) * -1)
            tmp2 = np.identity(n_samples)
            G = cvxopt.matrix(np.vstack((tmp1, tmp2)))
            tmp1 = np.zeros(n_samples)
            tmp2 = np.ones(n_samples) * self.C
            h = cvxopt.matrix(np.hstack((tmp1, tmp2)))
        else:
            G = cvxopt.matrix(np.diag(np.ones(n_samples) * -1))
            h = cvxopt.matrix(np.zeros(n_samples))

        # solve QP problem
        solution = cvxopt.solvers.qp(P, q, G, h, A, b)

        # get lagrange multipliers
        all_lm = np.ravel(solution['x'])
        self.all_lm_count = len(all_lm)

        # support vector have only non-zero lagrange multipliers
        nonzero_mask = all_lm > 0
        nonzero_i = np.arange(len(all_lm))[nonzero_mask]
        # store nonzero lagrange multipliers
        self.lm = all_lm[nonzero_mask]
        self.lm_count = len(self.lm)
        if self.lm_count == 0:
            print '0 support vectors found - no solution!!!'
            self.model_exists = False
            return
        # store training set and Y for nonzero lm
        self.X = X[nonzero_mask]
        self.Y = Y[nonzero_mask]
        self.model_exists = True
        print "Using {0} SV out of {1} points".format(len(self.lm), n_samples)

        # Intercept value
        self.b = 0
        for n in xrange(self.lm_count):
            self.b += self.Y[n]
            self.b -= np.sum(self.lm * self.Y * gram[nonzero_i[n], nonzero_mask])
        self.b /= len(self.lm)

        # create Weight vector for linear kernel function
        if isinstance(self.kernel, LinearKernel):
            self.w = np.zeros(n_features)
            for n in range(self.lm_count):
                self.w += self.lm[n] * self.X[n] * self.Y[n]
        else:
            self.w = None

    def predict(self, X):
        if self.w is not None:
            return np.sign(np.dot(X, self.w) + self.b)
        else:
            predict = np.zeros(len(X))
            for i in xrange(len(X)):
                s = 0
                for lm, x, y in zip(self.lm, self.X, self.Y):
                    s += lm * y * self.kernel(X[i], x)
                predict[i] = s
            return np.sign(predict + self.b)