"""L3 §4 叠加攻击 (d') — match case 体 × with 清理链：注入伪 `continue` 的**可观测**后果。

背景：`l3_o4_overlay_matchguard_with_comp.py` 的 `o4` 单元中，产物在 match 的
case 体末尾**注入**了源码不存在的 `continue`；但该探针的 `with` 在 `for` **之外**，
且 case 体是 for 体的最后一条语句 ⇒ 该 `continue` 在语义上**惰性**（no-op），
不能作为「注入伪语句 ⇒ 语义差」的证据。本探针把 `with` 放进 `for` 内部，
并在 match **之后**追加真实语句，使注入的 `continue` 变为**可观测**的语义差：
  - 源语义：每轮迭代都必须执行 `out.append("after")`；
  - 若产物注入 `continue`，则 `out.append("after")` 被跳过 ⇒ `out` 长度/内容不同。

同时给出第二单元 `o6b`：match 的 case 体**不是** for 体最后一条语句，
且 with 体在 for 体内 ⇒ 检验注入 `continue` 是否令 `__exit__` 配对次数变化。

判据问题：B70g（with 体内 if 的清理块过滤补口）与 B61k（match 宿主于 for/with/try
时的 case 体内嵌 if）叠加时，case 体的**最后一条真实语句**是否被替换成占位
`continue`？
"""


def o6(vals, res):
    """with 在 for 体内；match 之后还有真实语句 ⇒ 注入的 continue 必然被观测到。"""
    out = []
    for v in vals:
        with res as r:
            match v:
                case int() if v > 0:
                    out.append(v)
                case _:
                    out.append(-1)
            out.append("after")
    return out


def o6b(vals, res):
    """match 的 case 体之后还有真实语句；with 体在 for 体内（`__exit__` 配对可观测）。"""
    out = []
    for v in vals:
        with res as r:
            match v:
                case int() if v > 0:
                    out.append(v)
                case _:
                    out.append(-1)
            out.append("tail")
            out.append(r)
    return out
