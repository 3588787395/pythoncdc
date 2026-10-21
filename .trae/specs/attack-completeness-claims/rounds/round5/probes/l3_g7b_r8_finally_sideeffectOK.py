# Source Generated with Decompyle++ (Python version)
# File: l3_g7b_r8_finally_sideeffect.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检（可观测化）— 族 R8：finally 体内 return 的**副本重复**是否可观测。

`l3_g7_r8_finally_conditional_return` 的 finally 体只含 return，
产品把 finally 体**复制**进 try 体与 handler 体时语义仍等价（return 值相同）⇒ 不可观测。
本探针把 finally 体换成**带副作用**的语句（out.append），使「finally 体被执行了
几次」成为可观测量；源语义：finally 体每个元素**恰好执行一次**。

同时枚举 finally 体被复制的宿主：try 体 / handler 体 / else 体。
"""
def r8_fin_sideeffect(xs):
    out = []
    for x in xs:
        try:
            if x:
                return 'body'
            else:
                raise ValueError(x)
        except ValueError:
            return 'handler'
        finally:
            out.append('fin')
    return out
def r8_fin_sideeffect_noloop(xs):
    out = []
    for x in xs:
        try:
            out.append(x)
        except ValueError:
            out.append(-1)
        finally:
            out.append('fin')
    return out
def r8_fin_sideeffect_nested(xs):
    out = []
    for x in xs:
        try:
            out.append(x)
        finally:
            out.append('inner-fin')
        out.append('outer-fin')
    return out
