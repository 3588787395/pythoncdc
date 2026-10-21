"""L3 §5 — B143（finally 体内 break 的 finalbody 子区域派发）最小复现 + 兄弟形。

B143 登记于 rounds/round6/FIX.md:92-93 / round8/REVIEW.md:139-140（稀窝）；
ATTACK_SURFACE.md 指向的原始复现名为 `s_b140_break_in_finally_loop`（仓内未找到该文件）。

源语义（o_break_in_finally）：
  for 体：try 体 append(x) → finally 体 append(0)，若 x>2 则 **break**（跳出 for）。
  ⇒ x>2 的元素：append(x) 与 append(0) 各一次，循环终止；
    x<=2 的元素：append(x) 与 append(0) 各一次，继续下一轮。
  ⇒ 关键：break 必须出现在 finally 体内，且必须**终止循环**（不得被降级为
    pass / 被吞掉 / 被移出 finally）。

兄弟形：带 handler（break 在 finally 内、try 体可抛异常）。
"""


def o_break_in_finally(xs):
    out = []
    for x in xs:
        try:
            out.append(x)
        finally:
            out.append(0)
            if x > 2:
                break
    return out


def o_break_in_finally_handler(xs):
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
            if x > 2:
                break
    return out
