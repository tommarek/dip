#!/usr/bin/env python

import numpy as np

class Kernel():
    def __init__(self, param=None):
        self.param = param
    def change_param(self, new_param):
        self.param = new_param


class LinearKernel(Kernel):
    def __call__(self, x1, x2):
        return np.dot(x1, x2)

class PolynomialKernel(Kernel):
    def __call__(self, x1, x2):
        return (1 + np.dot(x1, x2)) ** self.param


class RBFKernel(Kernel):
    def __call__(self, x1, x2):
         return np.exp(-np.linalg.norm(x1 - x2) ** 2 / (2 * (self.param ** 2)))

str2kernel = {'RBF':RBFKernel, 'linear':LinearKernel, 'polynomial':PolynomialKernel}
