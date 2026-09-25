
class C:
    def v1(self, a, c, b):
        x = f'p{a if c else b}q'
        return x

    def v2(self, a, c, b):
        return f'p{a if c else b}q'

    def v3(self, a, c, b):
        print(f'p{a if c else b}q')
        return 1

    def v4(self, a, c, b):
        self.log.debug(f'p{a if c else b}q')
        x = 1
        return x

    def v5(self, universe):
        self.log.quote.debug(f'init{universe[:10]}n{len(universe)}')
        y = 2
        return y

    def v6(self, a, c, b):
        d = [f'p{a if c else b}q', 1]
        return d

    def v7(self, a, c, b, d):
        for i in d:
            self.log.debug(f'p{a if c else b}q{i}')
        return 1

    def v8(self, a, c, b):
        self.log.quote.debug(f'A{a[:1]}B{a if c else b}C{b}D{c}E')
        z = 3
        return z
