# Source Generated with Decompyle++ (Python version)
# File: c02_class_if.pyc (Python 3.11)

__doc__ = 'c02: class-level if/else with deep arms.'
PY2 = 0
class CIf:
    if PY2:
        def items(self):
            return []
    else:
        ITEMS = tuple(((i, i * i) for i in range(3)))
        def items(self):
            for k, v in ITEMS:
                while v and k:
                    try:
                        k -= 1
                    finally:
                        pass
            return ITEMS
    if PY2:
        LEGACY = True
    else:
        LEGACY = False
class CIfShallow:
    if PY2:
        TAG = 'old'
    else:
        TAG = 'new'
    def tag(self):
        return self.TAG
