# Source Generated with Decompyle++ (Python version)
# File: rv3_05_b92_classderef_shadow.pyc (Python 3.11)

def make_top(x):
    class Top:
        TV = x
        other = x
        def get_x(self, x):
            return x
        def get_tv(self):
            return self.TV
    return Top
class ShadowCombo:
    def bind(self, y):
        z = y
        class Inner:
            IV = z
            def loc(self, z):
                return z + 1
        return Inner
