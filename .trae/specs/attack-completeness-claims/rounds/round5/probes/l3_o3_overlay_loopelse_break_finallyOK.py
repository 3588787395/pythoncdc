# Source Generated with Decompyle++ (Python version)
# File: l3_o3_overlay_loopelse_break_finally.pyc (Python 3.11)

__doc__ = """L3 §4 叠加攻击 (c) — for-else + break + finally + handler 同函数。

关注：B144/B145（break 落点独占可达）、B140（handler break）、B155/B156
     （臂尾回边）、B157（finally 归属唯一化）四族在同函数内的优先级；
     源语义：for 的 else 仅在**无 break** 时执行。

注：Python 语法不允许 try/except/else/finally 四段并存，故 (c) 拆为
    try/except/finally 三段 + for-else 叠加。
"""
def o3(xs):
    out = []
    for x in xs:
        try:
            if x < 0:
                raise ValueError(x)
            out.append(x)
        except ValueError:
            out.append(-1)
        finally:
            out.append(0)
        break
    else:
        out.append('else')
    return out
def o3b(xs):
    """无 break 版本：for-else 与 try/except/finally 同时存在。"""
    out = []
    for x in xs:
        try:
            out.append(x)
        except ValueError:
            out.append(-1)
        finally:
            out.append(0)
    out.append('else')
    return out
def o3c(xs):
    """for-else + try/except/else（无 finally）+ break 在 handler 内。"""
    out = []
    for x in xs:
        try:
            out.append(x)
        except ValueError:
            out.append(-1)
            break
        out.append(1)
    out.append('else')
    return out
