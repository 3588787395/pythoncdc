# Source Generated with Decompyle++ (Python version)
# File: c01_class_assign.pyc (Python 3.11)

__doc__ = 'c01: class-level assignment forms.'
class CAssign:
    A = 1
    B, C = 2, 3
    D = {'k': (A, B)}
    F = 4
    __annotations__['F'] = int
    G = A + B
    H = [x for x in range(A)]
    I = (lambda v: v * B)(2)
    J = f"v={A!r:'>4'}"
    K = None
    def get(self):
        return (A if A else C, D['k'], H[0], I, J)
