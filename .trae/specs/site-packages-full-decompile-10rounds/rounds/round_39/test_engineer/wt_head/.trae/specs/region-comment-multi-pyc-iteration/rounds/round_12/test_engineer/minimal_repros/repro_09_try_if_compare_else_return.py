# repro_09: comparison condition (no BoolOp) in try if/else return (Pattern A2 core)
def f(x, a, b, c):
    try:
        if x > 10:
            return a
        else:
            return b
    except BaseException:
        return c
