# Source Generated with Decompyle++ (Python version)
# File: l3_g7c_r8_finally_sideeffect_return.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检（可观测化·2）— 族 R8：finally 体含 **return + 副作用** 时的副本重复。

机理：CPython 3.11 在 try 体含 `return`/`raise` 的正常出口路径上**内联**一份
finally 体的副本（与 finalbody 区域那份并存）。若归约把「正常路径副本」误当作
try 体/handler 体的语句（=B142 的同一根因：正常路径 finally 副本归属错误），
则 finally 体的**副作用语句会被执行两次** ⇒ 可观测语义差。

`l3_g7_r8_finally_conditional_return` 的 finally 体只含 return ⇒ 不可观测；
`l3_g7b` 的 finally 体无控制转移 ⇒ 编译器不内联副本 ⇒ 也不可观测。
本探针 finally 体同时含**副作用**与**return** ⇒ 副本重复可观测。
"""
LAST = []
def r8_fin_sideeffect_return(xs):
    out = []
    for x in xs:
        try:
            if x:
                out.append('fin')
                if x < 0:
                    return 'finally'
                else:
                    return 'body'
            else:
                raise ValueError(x)
        except ValueError:
            out.append('fin')
            if x < 0:
                return 'finally'
            else:
                return 'handler'
        finally:
            out.append('fin')
            if x < 0:
                return 'finally'
    return 'end'
def r8_fin_sideeffect_return_raise(xs):
    out = []
    for x in xs:
        try:
            if x:
                out.append('fin')
                if x < 0:
                    return 'finally'
                else:
                    return 'body'
            else:
                raise ValueError(x)
        except ValueError:
            raise KeyError(x)
        finally:
            out.append('fin')
            if x < 0:
                return 'finally'
    return 'end'
