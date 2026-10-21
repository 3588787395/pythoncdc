# Source Generated with Decompyle++ (Python version)
# File: l3_o2_overlay_boolop_ternary_await.pyc (Python 3.11)

__doc__ = """L3 §4 叠加攻击 (b) — BoolOp + 三元 + await 同处一个条件式。

关注：R2 的 BoolOp/IfExp 合并守卫 与 R4 的 await 挂起链守卫 谁先命中；
     await 处于 BoolOp 右操作数内时，B112 的「上一显著操作码」判据是否仍成立。
"""
async def o2(res, flag, x):
    if await res.ready():
        if flag:
            if x:
                pass
        elif await res.other():
            return 1
    return 0
async def o2b(res, flag, x):
    if flag:
        if not x:
            pass
    elif await res.other() or await res.ready() and x:
        return 1
    else:
        return 0
