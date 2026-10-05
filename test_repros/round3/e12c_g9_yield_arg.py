# e12c: e12 拆分补测——「yield 表达式作调用实参」单元单独隔离（强制括号缺失 → 预期 compile_error）
def f_yield_expr_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink((yield i))
    return
