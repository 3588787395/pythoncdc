# Source Generated with Decompyle++ (Python version)
# File: repro_17_nested_if_else.pyc (Python 3.11)

class Foo:
    def func(self, x):
        if x.dir == 1:
            if x.sub == 0:
                return 1
            else:
                return 2
        else:
            return 3
