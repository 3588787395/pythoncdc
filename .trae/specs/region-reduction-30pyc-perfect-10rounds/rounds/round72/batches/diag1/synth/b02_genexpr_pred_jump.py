# F-OTHER (position_model FuturePosition/LiveFuturePosition/OptionPosition,
# `<genexpr>` x10): a generator expression with a trailing `if` predicate compiles
# to a FORWARD conditional jump in the original but a BACKWARD one in the product
# (POP_JUMP_FORWARD_IF_FALSE to 42  vs  POP_JUMP_BACKWARD_IF_FALSE to 6),
# instruction count identical (24/24) -- only the jump direction/target differ.
class P:
    def buy_open_order_amount(self):
        amount = sum(o.amount for o in self._orders if o.side == BUY)
        return amount

    def sell_open_order_amount(self):
        amount = sum(o.amount for o in self._orders if o.side == SELL)
        return amount

    def close_today_amount(self):
        return sum(o.amount for o in self._orders if o.offset == CLOSE_TODAY)
