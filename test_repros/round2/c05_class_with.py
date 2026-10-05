"""c05: class-level with."""
class CWith:
    with _CM() as cm:
        HANDLE = cm

    def use(self):
        return self.HANDLE


class CWithDeep:
    with _CM() as a:
        for i in range(2):
            try:
                if i:
                    with _CM() as b:
                        VAL = (a, b, i)
            finally:
                FLAG = i

    def get(self):
        return self.VAL
