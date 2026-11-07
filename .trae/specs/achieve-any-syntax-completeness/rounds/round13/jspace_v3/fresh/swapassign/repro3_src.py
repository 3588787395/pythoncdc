import random
class N:
    def samples(self, n):
        gauss = random.gauss if seed is None else random.Random(seed).gauss
        mu, sigma = self._mu, self._sigma
        return [gauss(mu, sigma) for i in range(n)]
