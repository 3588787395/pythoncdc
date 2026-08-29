# family: G1  多 yield while 体（P6）
def f():
    i = 0
    while i < 10:
        i += 1
        yield i
        yield i * 2
