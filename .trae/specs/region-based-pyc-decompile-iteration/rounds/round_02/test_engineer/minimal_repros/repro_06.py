# family: F4 — F4 带 assert 消息的形式（同样丢赋值）
# 预期字节码模式: STORE_FAST amount 之后 LOAD_ASSERTION_ERROR / RAISE_VARARGS
# 实际反编译输出: `amount = trade.amount` 消失
# 关联 pyc: 同上 order.pyc / fill
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount, 'over fill'
    return [trade]
