# F-TERNARY (bar.BarData.limit_up without the try): `return v if cond else nan`
# should emit one JUMP_FORWARD to a shared return block; decompiler emits if/else
# with two inline returns (44 JUMP_FORWARD to 68 vs 44 RETURN_VALUE).
class BarData:
    def __init__(self, data):
        self._data = data

    @property
    def limit_up(self):
        v = self._data['limit_up']
        return v if v != 0 else float('nan')
