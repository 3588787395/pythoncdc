# Source Generated with Decompyle++ (Python version)
# File: l3_o1_overlay_six.pyc (Python 3.11)

__doc__ = """L3 §4 叠加攻击 (a) — 单函数内 if×for×try×match×with×async，嵌套深度 >= 3。

关注：守卫族优先级冲突（谁的守卫先命中）、叠加缺口（某一族被另一族抢走）。
"""
from contextlib import asynccontextmanager
async def o1(xs, res, sres):
    out = []
    async with res as r:
        for x in xs:
            if x:
                try:
                    with sres as sr:
                        match x:
                            case int() if x > 0:
                                pass
                            case _:
                                pass
                except ValueError:
                    out.append(0)
            else:
                continue
    return out
async def o1b(xs, res):
    out = []
    async with res as r:
        for x in xs:
            if x:
                try:
                    match x:
                        case int() if x > 0:
                            pass
                        case _:
                            pass
                except ValueError:
                    out.append(0)
    return out
