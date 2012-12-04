#!/usr/bin/env python

import numpy as np
import cvxopt
import cvxopt.solvers

def linear_kernel(x1, x2):
    return np.dot(x1, x2)

def polynomial_kernel(x, y, p=3):
    return (1 + np.dot(x, y)) ** p

def RBF_kernel(x, y, sigma=5.0):
    return np.exp(-np.linalg.norm(x-y)**2 / (2 * (sigma ** 2)))

class SVM():
    '''
    SVM class
    '''

    def __init__(self, kernel=linear_kernel, kernel_param=None, C=None):
        self.kernel = kernel
        self.kernel_param = kernel_param
        if C:
            self.C = float(C)
        else:
            self.C = None

    def train(self, X, Y):
        '''
        Method for training
        @param X 
        @param Y 
        '''
        n_samples, n_features = X.shape

        # create gram matrix (kernel matrix)
        gram = np.zeros((n_samples, n_samples))
        if self.kernel_param:
            for i in xrange(n_samples):
                for j in xrange(n_samples):
                    gram[i,j] = self.kernel(X[i], X[j], self.kernel_param)
        else:
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

        # support vector have only non-zero lagrange multipliers
        nonzero_mask = all_lm > 1e-5
        nonzero_i = np.arange(len(all_lm))[nonzero_mask]
        # store nonzero lagrange multipliers
        self.lm = all_lm[nonzero_mask]
        self.lm_count = len(self.lm)
        # store training set and Y for nonzero lm
        self.X = X[nonzero_mask]
        self.Y = Y[nonzero_mask]
        print "Using {0} SV out of {1} points".format(len(self.lm), n_samples)

        # Intercept value
        self.b = 0
        for n in xrange(self.lm_count):
            self.b += self.Y[n]
            self.b -= np.sum(self.lm * self.Y * gram[nonzero_i[n], nonzero_mask])
        self.b /= len(self.lm)

        # create Weight vector for linear kernel function
        if self.kernel == linear_kernel:
            self.w = np.zeros(n_features)
            for n in range(self.lm_count):
                self.w += self.lm[n] * self.X[n] * self.Y[n]
        else:
            self.w = None

    def project(self, test_set):
        if self.w is not None:
            return np.dot(test_set, self.w) + self.b
        else:
            predict = np.zeros(len(test_set))
            for i in xrange(len(test_set)):
                s = 0
                for lm, x, y in zip(self.lm, self.X, self.Y):
                    if self.kernel_param:
                        s += lm * y * self.kernel(test_set[i], x, self.kernel_param)
                    else:
                        s += lm * y * self.kernel(test_set[i], x)
                predict[i] = s
            return predict + self.b

    def predict(self, X):
        return np.sign(self.project(X))

if __name__ == "__main__":
    import pylab as pl

    def gen_lin_separable_data():
        # generate training data in the 2-d case
        mean1 = np.array([0, 2])
        mean2 = np.array([2, 0])
        cov = np.array([[0.8, 0.6], [0.6, 0.8]])
        X1 = np.random.multivariate_normal(mean1, cov, 100)
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 100)
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2

    def gen_non_lin_separable_data():
        mean1 = [-1, 2]
        mean2 = [1, -1]
        mean3 = [4, -4]
        mean4 = [-4, 4]
        cov = [[1.0,0.8], [0.8, 1.0]]
        X1 = np.random.multivariate_normal(mean1, cov, 50)
        X1 = np.vstack((X1, np.random.multivariate_normal(mean3, cov, 50)))
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 50)
        X2 = np.vstack((X2, np.random.multivariate_normal(mean4, cov, 50)))
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2

    def gen_lin_separable_overlap_data():
        # generate training data in the 2-d case
        mean1 = np.array([0, 2])
        mean2 = np.array([2, 0])
        cov = np.array([[1.5, 1.0], [1.0, 1.5]])
        X1 = np.random.multivariate_normal(mean1, cov, 100)
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 100)
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2

    def split_train(X1, y1, X2, y2):
        X1_train = X1[:90]
        y1_train = y1[:90]
        X2_train = X2[:90]
        y2_train = y2[:90]
        X_train = np.vstack((X1_train, X2_train))
        y_train = np.hstack((y1_train, y2_train))
        return X_train, y_train

    def split_test(X1, y1, X2, y2):
        X1_test = X1[90:]
        y1_test = y1[90:]
        X2_test = X2[90:]
        y2_test = y2[90:]
        X_test = np.vstack((X1_test, X2_test))
        y_test = np.hstack((y1_test, y2_test))
        return X_test, y_test

    def plot_margin(X1_train, X2_train, clf):
        def f(x, w, b, c=0):
            # given x, return y such that [x,y] in on the line
            # w.x + b = c
            return (-w[0] * x - b + c) / w[1]

        pl.plot(X1_train[:,0], X1_train[:,1], "ro")
        pl.plot(X2_train[:,0], X2_train[:,1], "bo")
        pl.scatter(clf.sv[:,0], clf.sv[:,1], s=100, c="g")

        # w.x + b = 0
        a0 = -4; a1 = f(a0, clf.w, clf.b)
        b0 = 4; b1 = f(b0, clf.w, clf.b)
        pl.plot([a0,b0], [a1,b1], "k")

        # w.x + b = 1
        a0 = -4; a1 = f(a0, clf.w, clf.b, 1)
        b0 = 4; b1 = f(b0, clf.w, clf.b, 1)
        pl.plot([a0,b0], [a1,b1], "k--")

        # w.x + b = -1
        a0 = -4; a1 = f(a0, clf.w, clf.b, -1)
        b0 = 4; b1 = f(b0, clf.w, clf.b, -1)
        pl.plot([a0,b0], [a1,b1], "k--")

        pl.axis("tight")
        pl.show()

    def plot_contour(X1_train, X2_train, clf):
        pl.plot(X1_train[:,0], X1_train[:,1], "ro")
        pl.plot(X2_train[:,0], X2_train[:,1], "bo")
        pl.scatter(clf.X[:,0], clf.X[:,1], s=100, c="g")

        X1, X2 = np.meshgrid(np.linspace(-6,6,50), np.linspace(-6,6,50))
        X = np.array([[x1, x2] for x1, x2 in zip(np.ravel(X1), np.ravel(X2))])
        Z = clf.project(X).reshape(X1.shape)
        pl.contour(X1, X2, Z, [0.0], colors='k', linewidths=1, origin='lower')
        pl.contour(X1, X2, Z + 1, [0.0], colors='grey', linewidths=1, origin='lower')
        pl.contour(X1, X2, Z - 1, [0.0], colors='grey', linewidths=1, origin='lower')

        pl.axis("tight")
        pl.show()

    def test_linear():
        X1, y1, X2, y2 = gen_lin_separable_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM()
        clf.train(X_train, y_train)

        y_predict = clf.predict(X_test)
        correct = np.sum(y_predict == y_test)
        print "%d out of %d predictions correct" % (correct, len(y_predict))

        plot_margin(X_train[y_train==1], X_train[y_train==-1], clf)

    def test_non_linear():
        X1, y1, X2, y2 = gen_non_lin_separable_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM(kernel=RBF_kernel, kernel_param=5)
        clf.train(X_train, y_train)

        y_predict = clf.predict(X_test)
        correct = np.sum(y_predict == y_test)
        print "%d out of %d predictions correct" % (correct, len(y_predict))

        plot_contour(X_train[y_train==1], X_train[y_train==-1], clf)

    def test_soft():
        X1, y1, X2, y2 = gen_lin_separable_overlap_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM(kernel=linear_kernel, C=0.1)
        clf.train(X_train, y_train)

        y_predict = clf.predict(X_test)
        correct = np.sum(y_predict == y_test)
        print "%d out of %d predictions correct" % (correct, len(y_predict))

        plot_contour(X_train[y_train==1], X_train[y_train==-1], clf)

    test_non_linear()
