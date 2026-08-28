# family: F7 — STORE_ATTR 的值为三元，但条件用 `if a is None` 形式（变体 2：验证是否为 is-not-None 专属）
# 预期字节码模式: LOAD_FAST p; POP_JUMP_FORWARD_IF_NONE; ...; LOAD_FAST self; STORE_ATTR y
# 实际反编译输出（预期）: 三元赋值与后续语句丢失，末句提升为 return
# 关联 pyc: 与 F7 同族（STORE_ATTR 值为三元）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

class A:
    def __init__(self, total_cash, processed_trade=None):
        self._total_cash = total_cash
        self._processed = set() if processed_trade is None else processed_trade
        self._transaction_cost = 0
        self.register_event()
