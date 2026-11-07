# Source Generated with Decompyle++ (Python version)
# File: E1_deref_listcomp_closure.pyc (Python 3.11)

import random
class N:
    def samples(self, n):
        gauss = random.gauss if seed is None else random.Random(seed).gauss
        mu = self._mu
        return [gauss(mu, sigma) for i in range(n)]
