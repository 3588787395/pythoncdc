# e12f: e12 拆分补测——「yield 表达式作 boolop 操作数」单元单独隔离（强制括号缺失 → 预期 compile_error）
def f_yield_in_boolop(xs):
    for i in range(3):
        if i:
            yield (yield i) or 0
    return
