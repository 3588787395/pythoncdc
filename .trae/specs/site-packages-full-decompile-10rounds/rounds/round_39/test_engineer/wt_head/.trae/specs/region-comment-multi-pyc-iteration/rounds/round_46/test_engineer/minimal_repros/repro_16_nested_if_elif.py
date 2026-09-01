class Foo:
    def func(self, x):
        if x.dir == 1:
            if x.sub == 0:
                self.a = 1
                return -1
            else:
                self.a = 2
        elif x.dir == 2:
            self.a = 3
            return 4
        return 0
