"""复现 08：后置循环含方法调用（LOAD_METHOD + CALL）。

模式：后置循环体调用 append 方法（与 build_future_fill_time @idx637-645 一致）。
循环块结构：LOAD_FAST + GET_ITER + FOR_ITER(exit=hi) + ... + JUMP_BACKWARD(->FOR_ITER)。
"""
def f(flag, keys, vals):
    buf = []
    if flag:
        for k in keys:
            buf.append(k)
    for v in vals:
        buf.append(v.strip())
    return buf
