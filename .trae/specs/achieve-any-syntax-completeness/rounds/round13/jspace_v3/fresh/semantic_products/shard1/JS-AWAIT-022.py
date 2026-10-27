# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b47_ternary.pyc (Python 3.11)

"""R4 synth: 三元臂 await 交叉变体（B47 族）。"""
async def s_true_arm(io, flag):
    return await io.a() if flag else None
async def s_false_arm(io, flag, xs):
    v = xs[0] if flag else await io.b()
    return v
async def s_both_binop(io, flag):
    r = await io.a() + 1 if flag else await io.b() + 2
    return r
