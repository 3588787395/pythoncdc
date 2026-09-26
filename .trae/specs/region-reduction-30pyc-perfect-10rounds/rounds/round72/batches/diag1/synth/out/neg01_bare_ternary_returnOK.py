# Source Generated with Decompyle++ (Python version)
# File: neg01_bare_ternary_return.pyc (Python 3.11)

class BarData:
    def __init__(self, data):
        self._data = data
    @property
    def limit_up(self):
        v = self._data['limit_up']
        return v if v != 0 else float('nan')
