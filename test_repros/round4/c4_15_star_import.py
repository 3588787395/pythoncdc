from os.path import *
from collections import *


def e01_use():
    return join, path


def e02_deep(x):
    r = 0
    for i in range(2):
        if i:
            r = join(x, str(i))
    return r


class CSI:
    def m(self):
        return path


def e03_comp(xs):
    return [join(x, 'a') for x in xs]


_G = path
if _G is not None:
    _y = join
else:
    _y = None
