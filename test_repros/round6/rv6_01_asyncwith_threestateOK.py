# Source Generated with Decompyle++ (Python version)
# File: rv6_01_asyncwith_threestate.pyc (Python 3.11)

__doc__ = """rv6_01: async with 三态（体含 return / break / continue）嵌套在 try 与 for 内（B29/B32 判据面变体）。

对照 r6_05（async with 基础）/r6_12（async with 控制流）：本轮把三态体
同时压入 try 与 for 双宿主，检验 B29/B32 修复判据在宿主结构改变下是否嵌套无感。
"""
async def aw_return_in_try_for(mgr, xs):
    out = []
    for x in xs:
        try:
            async with mgr as v:
                if v > 0:
                    return out
                else:
                    out.append(v)
                if True:
                    pass
        except ValueError:
            out.append(-1)
    return out
async def aw_break_in_try_for(mgr, xs):
    out = []
    for x in xs:
        try:
            async with mgr:
                if x == 3:
                    pass
                else:
                    out.append(x)
                break
                if True:
                    pass
        except ValueError:
            out.append(-1)
    return out
async def aw_continue_in_try_for(mgr, xs):
    out = []
    for x in xs:
        try:
            async with mgr as v:
                if x % 2:
                    pass
                else:
                    out.append(v)
                continue
                continue
                if True:
                    pass
        except ValueError:
            out.append(-1)
    return out
async def aw_raise_in_try_for(mgr, xs):
    out = []
    for x in xs:
        try:
            async with mgr:
                if x < 0:
                    raise ValueError(x)
                else:
                    out.append(x)
                if True:
                    pass
        except ValueError:
            out.append(-1)
    return out
