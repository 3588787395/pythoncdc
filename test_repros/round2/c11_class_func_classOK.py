# Source Generated with Decompyle++ (Python version)
# File: c11_class_func_class.pyc (Python 3.11)

__doc__ = 'c11: function and class alternation, deep bodies.'
class CHolder:
    def make(self):
        class Local:
            LV = 1
            def get(self):
                if self.LV:
                    for i in range(1):
                        while i:
                            try:
                                pass
                            finally:
                                pass
                return self.LV
        return Local
    def use(self):
        return self.make()
def top_make(x):
    class Top:
        TV = x
        def t(self):
            return self.TV
    return Top
def deep():
    for i in range(1):
        return top_make(i)
