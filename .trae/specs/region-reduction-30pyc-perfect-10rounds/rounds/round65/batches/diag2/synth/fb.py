# -*- coding: utf-8 -*-
"""diag2 class-B synth: f-string with complex interpolations (slice / nested CALL)."""


class T:
    def b1(self, a, out):
        print(f'x{a[:10]}y')
        return 1

    def b2(self, a, out):
        print(f'x{len(a)}y')
        return 1

    def b3(self, a, out):
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        return 1

    def b4(self, a, out):
        v = f'x{a[:10]}y{len(a)}z'
        return v

    def b5(self, a, out):
        self.log.debug(f'x{a}y')
        return 1

    def b6(self, a, out):
        while not out and len(a) < 3:
            out = 1
        return out

    def b7(self, a, out):
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def b8(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        c = 0
        while not out and c < 3:
            c += 1
        return c
