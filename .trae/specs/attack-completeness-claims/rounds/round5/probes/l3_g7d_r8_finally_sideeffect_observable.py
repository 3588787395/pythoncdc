"""L3 §3 通用性抽检（执行级可观测化·3）— 族 R8：finally 副本重复的**可观测**后果。

背景：`l3_g7c_r8_finally_sideeffect_return.py` 的 finally 体含 `out.append("fin")`
+ `return`，产物把 finally 体**复制进 try 体与 handler 体** ⇒ finally 体的副作用
被重复执行；但该探针的函数返回的是字符串（"body"/"handler"/"finally"），
局部 `out` 不可见 ⇒ 3 次执行**不可观测**（只能靠读产物文本断定）。

本探针让函数**返回该列表本身**，使「每元素执行几次」成为执行级可读数：
  - 源语义：每个元素 `out.append("fin")` 恰好 1 次；
  - 产物语义：finally 副本被计入 try 体/handler 体 ⇒ 每元素 3 次。
"""

def r8_fin_obs(xs):
    out = []
    for x in xs:
        try:
            out.append("body")
            return out
        finally:
            out.append("fin")
    return out


def r8_fin_obs_handler(xs):
    """异常路径：handler 体 + finally 副本。"""
    out = []
    for x in xs:
        try:
            if x < 0:
                raise ValueError(x)
            out.append("body")
            return out
        except ValueError:
            out.append("handler")
            return out
        finally:
            out.append("fin")
    return out
