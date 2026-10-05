"""c01: class-level assignment forms."""
class CAssign:
    A = 1
    B, C = 2, 3
    D = E = {'k': (A, B)}
    F: int = 4
    G = A + B
    H = [x for x in range(A)]
    I = (lambda v: v * B)(2)
    J = f'v={A!r:>4}'
    K = None

    def get(self):
        return (A if A else C, D['k'], H[0], I, J)
