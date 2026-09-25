
class C:
    def t1(self, a, c, b):
        self.log.debug(f'p{a if c else b}q')
        x = 1
        return x

    def t2(self, a, c, b):
        self.log.debug(f'p{a if c else b}')
        x = 1
        return x

    def t3(self, a, c, b):
        self.log.debug(f'{a if c else b}')
        x = 1
        return x

    def t4(self, a, c, b):
        return f'p{a if c else b}q'

    def t5(self, a, c, b):
        x = f'p{a if c else b}q'
        return x

    def t6(self, a, c, b):
        print(f'p{a if c else b}q')
        x = 1
        return x

    def t7(self, a, c, b):
        self.log.debug(f'p{a if c else b}q{a}')
        x = 1
        return x

    def t8(self, a, c, b):
        d = f'p{a if c else b}q'
        return d

    def t9(self, s):
        self.log.debug(f'a{s[:10]}b')
        return 1
