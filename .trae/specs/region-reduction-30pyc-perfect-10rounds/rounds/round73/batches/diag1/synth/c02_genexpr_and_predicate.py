# F-OTHER (position_model FuturePosition/LiveFuturePosition/OptionPosition,
# 10 `<genexpr>` units): comprehension whose `if` predicate is an `and` chain.
# Original: first test false -> POP_JUMP_FORWARD_IF_FALSE to the JUMP_BACKWARD
# "skip this element" block (52 -> 114), second test false -> POP_JUMP_BACKWARD
# (94 -> 8).  Product collapses both onto POP_JUMP_BACKWARD_IF_FALSE to 8
# (52 -> 8), so the first divergent instruction is
# POP_JUMP_FORWARD_IF_FALSE -> POP_JUMP_BACKWARD_IF_FALSE (24/24 instructions).
class P:
    def buy_open_order_amount(self):
        return sum(o.unfilled_amount for o in self.open_orders
                   if o.entrust_direction == EntrustDirection.BUY
                   and o.futures_direction == FuturesDirection.OPEN)

    def sell_open_order_amount(self):
        return sum(o.unfilled_amount for o in self.open_orders
                   if o.entrust_direction == EntrustDirection.SELL
                   and o.futures_direction == FuturesDirection.CLOSE)
