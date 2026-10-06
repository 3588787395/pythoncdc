# Source Generated with Decompyle++ (Python version)
# File: c4_14_relative_import.pyc (Python 3.11)

from  import mod
from sub import name as n2
from pkg import other as o2
def e01_use():
    return (mod, n2, o2)
def e02_deep():
    r = 0
    for i in range(2):
        if i:
            r = mod.attr
    return r
class CRI:
    def m(self):
        return n2
_G = mod
if _G is not None:
    _x = n2
else:
    _x = o2
