# Source Generated with Decompyle++ (Python version)
# File: c09_class_import_global.pyc (Python 3.11)

global G
__doc__ = 'c09: class-level import and method-level global.'
class CImp:
    import os as _os
    from collections import OrderedDict as _OD
    _M = _os.name if _os else ''
    def m(self):
        return self._M
G = 0
class CGlobal:
    def set_g(self, v):
        global G
        G = v
        if v:
            for i in range(v):
                if i:
                    try:
                        G += 1
                    finally:
                        pass
        return G
    def get_g(self):
        return G
