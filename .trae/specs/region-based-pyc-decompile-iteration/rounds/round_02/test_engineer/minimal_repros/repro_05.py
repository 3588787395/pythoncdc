# family: F4 — `assert` 之前的那条局部赋值被丢弃，变量退化为全局 LOAD_GLOBAL
# 预期字节码模式: LOAD_FAST trade; LOAD_ATTR amount; STORE_FAST amount; ... assert ...
# 实际反编译输出: `amount = trade.amount` 整条消失，后面的 amount 变成全局名
# 关联 pyc: site-packages/IQEngine/account/order.pyc  fill  baseline first_diff idx=1: LOAD_FAST trade -> LOAD_FAST self
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount
    self.filled_amount += amount
    return [trade]
