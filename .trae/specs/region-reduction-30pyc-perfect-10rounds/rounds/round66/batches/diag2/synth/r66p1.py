class C:
    def w1(self, s, c, b):
        self.log.debug(f'A{s[:10]}B{len(s) if c else 1}C{b}D')
        return 1

    def w2(self, s, c, b):
        self.log.debug(f'A{s[0]}B{len(s) if c else 1}C{sorted(s)}D')
        return 2

    def w3(self, s, c, b):
        x = f'A{s[:10]}B{len(s) if c else 1}C'
        return x
