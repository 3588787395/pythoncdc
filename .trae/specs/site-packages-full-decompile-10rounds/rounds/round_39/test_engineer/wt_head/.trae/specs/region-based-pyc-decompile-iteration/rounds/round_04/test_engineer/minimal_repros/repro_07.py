# family: G1  yield 表达式赋值
def f(items):
    for x in items:
        y = yield x
        print(y)
