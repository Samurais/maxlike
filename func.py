import numpy as np


def vector_func(g):
    def wrapper(obj, param=[], i=None):
        if i is not None:
            return g(obj, param, i)
        else:
            return map(lambda i: g(obj, param, i), range(len(param)))
    return wrapper


def matrix_func(h):
    def wrapper(obj, param=[], i=None, j=None):
        if i is not None and j is not None:
            return h(obj, param, i, j)
        else:
            return map(lambda i:
                       map(lambda j: h(obj, param, i, j), range(i + 1)),
                       range(len(param)))
    return wrapper


class func:
    def __init__(self):
        self.params = []

    def eval(self, param):
        raise NotImplementedError

    def grad(self, param, i):
        raise NotImplementedError

    def hess(self, param, i=None, j=None):
        raise NotImplementedError

    def __add__(self, b):
        return affine(self, 1, b)

    def __sub__(self, b):
        return affine(self, 1, -b)

    def __neg__(self):
        return affine(self, -1, 0)

    def __mul__(self, a):
        return affine(self, a, 0)

    def __div__(self, a):
        return affine(self, 1.0 / a, 0)


class affine(func):
    def __init__(self, base, a, b):
        if isinstance(base, affine):
            self.base = base.base
            self.a = a * base.a
            self.b = a * base.b + b
        else:
            self.base = base
            self.a = a
            self.b = b

    def eval(self, param):
        return self.a * self.base.eval(param) + self.b

    @vector_func
    def grad(self, param, i):
        return self.a * self.base.grad(param, i)

    @matrix_func
    def hess(self, param, i=None, j=None):
        return self.a * self.base.hess(param, i, j)


class power(func):
    def __init__(self, base, p):
        if isinstance(base, power):
            self.base = base.base
            self.p = p * base.p
        else:
            self.base = base
            self.p = p

    def eval(self, param):
        f = self.base.eval(param)
        return np.sign(f) * np.power(np.abs(f), self.p)

    @vector_func
    def grad(self, param, i):
        f = self.base.eval(param)
        if self.p == 0:
            return np.zeros(f.shape + param[i].shape)
        if self.p == 1:
            return self.base.grad(param, i)
        else:
            return self.p * np.power(np.abs(f), self.p - 1) * \
                self.base.grad(param, i)

    @matrix_func
    def hess(self, param, i, j):
        f = self.base.eval(param)
        if self.p == 0:
            return np.zeros(f.shape + param[i].shape + param[j].shape)
        elif self.p == 1:
            return self.base.hess(param, i, j)
        else:
            slc_feat = [slice(None)] * f.ndim
            slc_i = [slice(None)] * param[i].ndim
            slc_j = [slice(None)] * param[j].ndim
            slc_expd_i = [None] * param[i].ndim
            slc_expd_j = [None] * param[j].ndim
            h = (self.p * (self.p - 1) * np.sign(f) *
                 np.power(np.abs(f), self.p - 2) *
                 self.base.grad(param, i)[slc_feat + slc_i + slc_expd_j] *
                 self.base.grad(param, j)[slc_feat + slc_expd_i + slc_j]) - \
                (self.p * np.power(np.abs(f), self.p - 1) *
                 self.base.hess(param, i, j))
            return h


class linear(func):
    def __init__(self):
        self.weight = []

    def eval(self, param):
        if not isinstance(param, (tuple, list)):
            return sum(param * self.weight[0])
        else:
            return sum([sum(param[i] * self.weight[i])
                        for i in range(len(param))])

    @vector_func
    def grad(self, param, i):
        return self.weight[i]

    @matrix_func
    def hess(self, param, i=None, j=None):
        if i is not None and j is not None:
            return np.multiply.outer(
                np.zeros(self.weight[j].shape),
                np.zeros(self.weight[i].shape))
        else:
            return self._hess_matrix(param)

    def add_feature(self, shape, weight):
        self.weight.append(weight * np.ones(shape))


class onehot(func):
    def __init__(self):
        pass

    def eval(self, param):
        return np.array(param)[0]

    @vector_func
    def grad(self, param, i):
        return np.diag(np.ones(param[0].size)).reshape(param[0].shape * 2)

    @matrix_func
    def hess(self, param, i, j):
        return np.zeros(param[0].shape * 3)


class constant(func):
    def __init__(self, vector):
        self.vector = np.array(vector)

    def eval(self, param=None):
        return self.vector

    @vector_func
    def grad(self, param, i):
        return np.zeros()

    @matrix_func
    def hess(self, param, i, j):
        return np.zeros()


class vector(func):
    def __init__(self, vector):
        self.vector = np.array(vector)

    def eval(self, param):
        return param * self.vector

    @vector_func
    def grad(self, param, i):
        return self.vector

    @matrix_func
    def hess(self, param, i, j):
        return np.zeros((self.vector.size))
