"""L3 §3 通用性抽检（执行级可观测化）— 族 R6：handler 内 continue 被丢弃的**可观测**后果。

背景：`l3_g5b_r6_handler_continue_matrix.py` 的 {while × continue 前有语句} 格
已被判定器判红（Different control flow），但其默认输入下两侧**返回值相同**
（handler 的 `i += 1` 恰好补偿了被丢弃的 continue 所带来的迭代推进）⇒
「判红」不等于「语义差可观测」。

本探针把 handler 的推进量改成 `i += 2`（与循环体自身的 `i += 1` 不同），
使被丢弃的 `continue` 造成**可观测**的差异：
  - 源语义：handler 内 `continue` ⇒ 回到循环头 ⇒ 跳过本轮 `out.append(xs[i])`
             ⇒ 返回 [3, -1]（不越界）；
  - 产物语义：continue 被丢弃 ⇒ 落到 `out.append(xs[i])` ⇒ i 已 +2 ⇒ **越界 IndexError**。
"""

def r6_while_stmt_continue_obs(xs):
    out = []
    i = 0
    while i < len(xs):
        try:
            if xs[i] < 0:
                raise ValueError(xs[i])
        except ValueError:
            out.append(-1)
            i += 2
            continue
        out.append(xs[i])
        i += 1
    return out
