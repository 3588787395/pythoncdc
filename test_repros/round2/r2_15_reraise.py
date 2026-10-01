# r2_15 try 内 raise 重抛裸 raise
# 焦点：RERAISE 裸重抛（3.11 RERAISE 语义）


def f(x):
    try:
        try:
            if x < 0:
                raise ValueError("neg")
            x += 1
        except ValueError:
            if x == -1:
                raise
            x = -x
    except ValueError as e:
        return -100
    return x
