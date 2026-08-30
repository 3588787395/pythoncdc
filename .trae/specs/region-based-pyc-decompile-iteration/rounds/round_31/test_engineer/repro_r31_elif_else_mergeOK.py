# Source Generated with Decompyle++ (Python version)
# File: repro_r31_elif_else_merge.pyc (Python 3.11)

__doc__ = """Round 31 最小复现：elif 链 final-else 内嵌套 if/else + 尾随 merge 语句。

对应 future_position.pyc::make_trade 真实源码结构：
  if/elif 链（前两臂 return），final else 内是嵌套 if/else
  （嵌套 else 有真实语句），嵌套 if/else 之后还有 merge 尾随语句（以 return 结尾）。

触发渲染 bug：_generate_elif_or_else 把嵌套 if 归约出的 elif 与其后 merge
兄弟语句一起渲染时，merge 兄弟成了 else 体，嵌套 if 的 orelse（两条赋值）被丢弃。
"""
class Obj:
    def __init__(self):
        self.m = 0.0
        self.c = 0.0
        self.r = 0.0
        self.p = 0.0
        self.q = ''
    def close(self, amt):
        return amt
def make(x, amt, obj):
    if x == 1:
        return 10
    elif x == 2:
        return 20
    elif amt - x != 0:
        obj.p = (obj.p * amt + x * amt) / (amt - x)
    else:
        obj.q = x
        obj.p = 0.0
    old = obj.m
    obj.c += amt
    d = obj.close(amt)
    obj.r += d
    return old - obj.m + d
