# Source Generated with Decompyle++ (Python version)
# File: r10_05_relative_star.pyc (Python 3.11)

__doc__ = 'r10_05: 相对导入层级 + star import 形态（表C relative_import/star_import）'
from . import sibling
from .pkg import leaf
from ..upper import faraway as faway
from .stars import *
def rel_level1(v):
    if v > 0:
        return sibling.help(v)
    else:
        return leaf(v)
def rel_level2_as(k):
    while k:
        if k % 2:
            return faway(k)
        k //= 2
    return None
def star_import_use(vals):
    out = []
    for v in vals:
        if v > 0:
            out.append(star_fn(v))
            continue
        elif v < 0:
            out.append(STAR_CONST)
    return out
