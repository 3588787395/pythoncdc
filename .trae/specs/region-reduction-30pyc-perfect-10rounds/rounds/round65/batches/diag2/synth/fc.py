# -*- coding: utf-8 -*-
"""diag2 class-B controls: what exactly dies at an if/elif merge-block head?"""


class T:
    def chain(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass

    def c1(self, a, out):
        v = 1
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c2(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        v = 1
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c3(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug('plain')
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c4(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug(f'x{a}y')
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c5(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        v = 1
        w = 2
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c6(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        return 7

    def c7(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        out = f'x{a[:10]}y{len(a)}z'
        c = 0
        while not out and c < 3:
            c += 1
        return c

    def c8(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        c = 0
        while c < 3:
            c += 1
        return c

    def c9(self, a, out):
        if isinstance(a, str):
            pass
        elif isinstance(a, list):
            for i in a:
                pass
        self.log.debug(f'x{a[:10]}y{len(a)}z')
        c = 0
        while not out and len(a) < 3:
            c += 1
        return c
