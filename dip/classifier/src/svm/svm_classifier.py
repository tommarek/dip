#!/usr/bin/env python

import logging
import numpy as np
import cvxopt
import cvxopt.solvers
import pickle

from src.kernels import *

class SVM():
    '''
    Implementation of support vector machine classifier. It allows to train,
    classify and store/load svm classification models.
    '''

    def __init__(self, kernel, C=None, silent=False, qp_maxiter=200):
        '''
        init function
        @param kernel: kernel object
        @param C: C parameter for svm
        @param silent: set silent mode
        @param qp_maxiter: set maximal amount of iteration of qp
        '''
        self.kernel = kernel
        if C:
            self.C = float(C)
        else:
            self.C = None

        # qp config
        if silent:
            cvxopt.solvers.options['show_progress'] = False
        cvxopt.solvers.options['maxiters'] = qp_maxiter

        # learned svm params
        self.lm = None
        self.lm_count = 0
        self.all_lm_count = 0
        self.b = None
        self.w = None

    def train(self, X, Y):
        '''
        Method for training svm classifier
        @param X: training set
        @param Y: testing set
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
        '''
        Fucntion tries to predict input entries according to previous training.
        @param X: tokens mapped into numpy array
        @return: numpy array containing 1 and -1 for relevant and irelevante
                entries
        '''
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

    def store_model(self, path, token_list):
        '''
        Store classification model into some file for future classification.
        @param path path: to file, where the model will be stored
        @param token_list: list of token mapping for future classification
        @return: svm model pickle
        '''
        print 'Storing SVM model data...'
        model = {}
        model['lm'] = self.lm
        model['lm_count'] = self.lm_count
        model['all_lm_count'] =  self.all_lm_count
        model['C'] = self.C
        model['w'] = self.w
        model['b'] = self.b
        model['X'] = self.X
        model['Y'] = self.Y
        model['lm'] = self.lm
        model['kernel'] = self.kernel
        model['token_list'] = token_list

        # store model
        pickle.dump(model, open(path, 'wb'))

    def load_model(self, path):
        '''
        Load classification model from file.
        @param path: path to model file
        @return: list of token mapping for future classification
        '''
        model = pickle.load(open(path, 'rb'))
        self.lm = model['lm']
        self.lm_count = model['lm_count']
        self.all_lm_count = model['all_lm_count']
        self.C = model['C']
        self.w = model['w']
        self.b = model['b']
        self.X = model['X']
        self.Y = model['Y']
        self.lm = model['lm']
        self.kernel = model['kernel']

        return model['token_list']
