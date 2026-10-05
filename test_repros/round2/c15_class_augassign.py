"""c15: class-level augassign including ternary RHS (B46 cross)."""
class CAug:
    N = 1
    N += 2
    M = 3
    M *= 2 if N else 1
    L = [1]
    L[0] += M

    def r(self):
        return (self.N, self.M, self.L)
