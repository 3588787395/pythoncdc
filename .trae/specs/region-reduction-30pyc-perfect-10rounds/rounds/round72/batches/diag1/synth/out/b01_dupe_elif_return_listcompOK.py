# Source Generated with Decompyle++ (Python version)
# File: b01_dupe_elif_return_listcomp.pyc (Python 3.11)

class B:
    def get_orders(self, x=None):
        if x is None:
            return self._orders
        elif isinstance(x, str):
            return [o for o in self._orders if o.symbol == x]
            return [o for o in self._orders if o.symbol == x]
        elif valid(x):
            return [o for o in self._orders if o.symbol == x.symbol]
            return [o for o in self._orders if o.symbol == x.symbol]
        elif isinstance(x, Order):
            return [o for o in self._orders if o == x]
            return [o for o in self._orders if o == x]
        else:
            return []
    def get_open_orders(self, x=None):
        if x is None:
            return [o for a, o in self._open]
            return [o for a, o in self._open]
        elif isinstance(x, str):
            return [o for a, o in self._open if o.symbol == x]
            return [o for a, o in self._open if o.symbol == x]
        elif valid(x):
            return [o for a, o in self._open if o.symbol == x.symbol]
            return [o for a, o in self._open if o.symbol == x.symbol]
        elif isinstance(x, Order):
            return [o for a, o in self._open if o == x]
            return [o for a, o in self._open if o == x]
        else:
            return []
