# F-TERNARY (bar limit_up / limit_down): `return v if cond else nan` inside try
# compiles to JUMP_FORWARD to one shared return block under a single exception
# range; the decompiler emits if/else with two inline returns (range splits).
import numpy as np


class BarData:
    @property
    def limit_up(self):
        try:
            v = self._data['limit_up']
            return v if v != 0 else np.nan
        except (KeyError, ValueError):
            return np.nan
