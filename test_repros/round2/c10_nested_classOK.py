# Source Generated with Decompyle++ (Python version)
# File: c10_nested_class.pyc (Python 3.11)

__doc__ = 'c10: nested classes with body statements at each level.'
class Outer:
    OA = 1
    class Mid:
        MA = 2
        if MA:
            MB = [i for i in range(MA)]
        class Inner:
            IA = 3
            for _q in range(2):
                QL = _q
            def get(self):
                try:
                    if self.IA:
                        for k in range(2):
                            while k:
                                k -= 1
                finally:
                    pass
                return self.IA
        def mid_get(self):
            return self.IA
    def outer_get(self):
        return self.OA
