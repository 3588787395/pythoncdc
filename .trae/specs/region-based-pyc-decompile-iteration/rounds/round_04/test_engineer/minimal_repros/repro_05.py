# family: G1  yield 在 if 分支
def f(items):
    for x in items:
        if x > 0:
            yield x
