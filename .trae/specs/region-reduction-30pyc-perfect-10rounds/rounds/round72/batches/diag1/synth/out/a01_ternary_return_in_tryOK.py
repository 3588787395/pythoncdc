# Source Generated with Decompyle++ (Python version)
# File: a01_ternary_return_in_try.pyc (Python 3.11)

import numpy as np
class BarData:
    @property
    def limit_up(self):
        try:
            v = self._data['limit_up']
            if v != 0:
                return v
            else:
                return np.nan
        except (KeyError, ValueError):
            return np.nan
