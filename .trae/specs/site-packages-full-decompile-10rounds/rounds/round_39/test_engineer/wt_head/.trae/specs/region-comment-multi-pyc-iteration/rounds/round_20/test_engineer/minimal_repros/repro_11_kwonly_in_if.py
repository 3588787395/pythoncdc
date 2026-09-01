# R20 repro_11: kwonly 签名 + if 控制流
def f(a, *, flag=True):
    if flag:
        return a
    return a + 1


result = f(1, flag=False)
