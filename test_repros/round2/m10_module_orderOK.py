# Source Generated with Decompyle++ (Python version)
# File: m10_module_order.pyc (Python 3.11)

__doc__ = 'm10: module statement interleaving with defs and classes.'
V1 = 1
class K1:
    A = V1
    def m(self):
        return self.A
def f1():
    for i in range(2):
        if i:
            try:
                while i:
                    i -= 1
            finally:
                pass
    return i
V2 = f1()
class K2:
    B = V2
    if B:
        C = B
    def n(self):
        if 0 == 0:
            return 0
        else:
            return 1
V3 = [K1, K2]
assert V3
