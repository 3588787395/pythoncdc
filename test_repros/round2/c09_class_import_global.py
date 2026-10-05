"""c09: class-level import and method-level global."""
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
                while i:
                    try:
                        G += 1
                        break
                    finally:
                        pass
        return G

    def get_g(self):
        global G
        return G
