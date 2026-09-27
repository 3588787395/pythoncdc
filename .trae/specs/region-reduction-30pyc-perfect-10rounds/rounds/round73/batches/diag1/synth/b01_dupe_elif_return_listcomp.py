# F-EXTRA (broker get_orders / get_open_orders, trade_live_broker get_orders):
# if/elif chain where every non-default arm returns a listcomp.  The decompiler
# emits the arm's terminal `return [...]` TWICE (shadow claiming of the arm
# exit), so the recompiled product carries extra `<listcomp>` code objects that
# have no counterpart in the original -> "Extra bytecode".
class B:
    def get_orders(self, x=None):
        if x is None:
            return self._orders
        elif isinstance(x, str):
            return [o for o in self._orders if o.symbol == x]
        elif valid(x):
            return [o for o in self._orders if o.symbol == x.symbol]
        elif isinstance(x, Order):
            return [o for o in self._orders if o == x]
        else:
            return []

    def get_open_orders(self, x=None):
        if x is None:
            return [o for a, o in self._open]
        elif isinstance(x, str):
            return [o for a, o in self._open if o.symbol == x]
        elif valid(x):
            return [o for a, o in self._open if o.symbol == x.symbol]
        elif isinstance(x, Order):
            return [o for a, o in self._open if o == x]
        else:
            return []
