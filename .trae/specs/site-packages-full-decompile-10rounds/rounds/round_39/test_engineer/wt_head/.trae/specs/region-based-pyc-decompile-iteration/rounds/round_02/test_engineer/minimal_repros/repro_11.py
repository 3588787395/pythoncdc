# family: F7 — STORE_ATTR 的值为三元 `a if a is not None else f()` 时，该语句及之后全部丢失，末句被提升为 return
# 预期字节码模式: LOAD_FAST p; POP_JUMP_FORWARD_IF_NONE; LOAD_FAST p; JUMP_FORWARD; PUSH_NULL; LOAD_GLOBAL set; PRECALL; CALL; LOAD_FAST self; STORE_ATTR y
# 实际反编译输出: 三元赋值和后续 `self.z = 0` 一起消失，`self.register_event()` 变成 `return self.register_event()`
# 关联 pyc: site-packages/IQEngine/account/base_account.pyc  __init__  baseline first_diff idx=10 (orig 25 -> decomp 14)
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
