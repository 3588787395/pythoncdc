"""Round 31 最小复现 v2：镜像 future_position.pyc::make_trade 的完整结构。

源码形态（与原 pyc 语义一致）：
  if 链首臂（内含嵌套 if/else + merge + return），
  elif 臂（return），
  final else 臂（内含嵌套 if/else，嵌套 else 有真实语句 + merge 尾随 return）。

目标：触发 final else 的嵌套 if/else 被拍平为 elif 后，其 orelse（两条赋值）
被 merge 尾随语句顶替丢弃的渲染 bug。
"""

BUY = 1
SELL = 2
OPEN = 10
CLOSE = 20


class Obj:
    def __init__(self):
        self.m = 100.0
        self.c = 0.0
        self.r = 0.0
        self.p = 0.0
        self.q = ''
        self.t = ''
        self.u = ''
        self.h = []

    def set(self, t):
        self.q = t

    def cal(self, amt, price):
        return amt * price

    def close(self, amt):
        return amt


def make(trade_d, trade_f, amt, price, obj):
    if trade_d == BUY:
        if trade_f == OPEN:
            if obj.c == 0:
                obj.t = 'c'
            obj.set('r')
            obj.p = (obj.p * obj.c + amt * price) * 2 / ((obj.c + amt) * 2)
            obj.c += amt
            obj.h.insert(0, (price, amt))
            return -1 * obj.cal(amt, price)
        else:
            if obj.c - amt != 0:
                obj.p = (obj.p * obj.c - amt * price) * 2 / ((obj.c - amt) * 2)
            else:
                obj.u = 'u'
                obj.p = 0.0
            old = obj.m
            obj.c += amt
            d = obj.close(amt)
            obj.r += d
            return old - obj.m + d
    elif trade_f == OPEN:
        if obj.c == 0:
            obj.u = 'c'
        obj.set('v')
        obj.p = (obj.p * obj.c + amt * price) * 2 / ((obj.c + amt) * 2)
        obj.c += amt
        obj.h.insert(0, (price, amt))
        return -1 * obj.cal(amt, price)
    else:
        if obj.c - amt != 0:
            obj.p = (obj.p * obj.c - amt * price) * 2 / ((obj.c - amt) * 2)
        else:
            obj.q = 'q'
            obj.p = 0.0
        old = obj.m
        obj.c += amt
        d = obj.close(amt)
        obj.r += d
        return old - obj.m + d
