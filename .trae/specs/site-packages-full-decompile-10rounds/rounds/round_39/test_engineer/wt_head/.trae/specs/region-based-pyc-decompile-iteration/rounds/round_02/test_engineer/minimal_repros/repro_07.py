# family: F4 — F4 的属性形式：`y = self.compute(x)` 在 assert 前被丢弃
# 预期字节码模式: LOAD_FAST self; LOAD_METHOD compute; ...; STORE_FAST y
# 实际反编译输出: `y = self.compute(x)` 消失，assert 里的 y 变成全局名
# 关联 pyc: 同上 order.pyc / fill（同族）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(self, x):
    y = self.compute(x)
    assert y is not None
    self.result = y
