"""c07: statements interleaved between method definitions."""
class CBetween:
    def first(self):
        return 1
    MID = 'between'
    if MID:
        TAG = MID

    def second(self, v):
        return v + 1
    del MID

    def third(self):
        for i in range(2):
            if i:
                while i:
                    try:
                        i -= 1
                    finally:
                        pass
        return i
    assert True
    import json as _json
    _OTHER = _json

    def fourth(self):
        return 4
