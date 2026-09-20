# -*- coding: utf-8 -*-
"""R16-S 13 probe tail with try except
else 臂 = 嵌套 if/else + **try/except 尾随语句**（for 内）。
真实缺陷里尾随语句是直线代码 + `if ... is None: return`；本探针把尾随换成 try，
检验同一展平路径遇到异常区域是否也终点漂移（Round 14/15 的 try-in-arm 家族）。

真实目标：同 r16s_01，但尾随区域类型换为 TryExcept。

实测结论（当前核）：**展平确实发生，但尺子看不见 ⇒ 标 UNCONFIRMED**。
  · 区域层 trace：header=8 first_else=26 inner_merge=60 merge_=162 inloop=True
    → 走 FLATTEN-BY-LOOP-EXEMPTION(4)，与 r16s_04 完全同一条路径；
  · 反编译结果把 `try/except` 尾随外提到链后，`flag_a` 臂因此也会执行 try（语义已改写）；
  · 但 orig 的臂出口 JUMP_FORWARD 落点 off=162 = `LOAD_FAST out`，
    decomp 的落点 off=60（NOP 之后第一条语义指令）= `LOAD_FAST out` ——
    **两个终点的指令签名逐字相同**，strict_compare 的 target 判据（比较
    `(argval, opname)` 签名）无法区分，故实测 MATCH。
意义：本文件不是「负对照」，而是**度量盲区证据**——同族缺陷的真实覆盖面比
target_diff 计数更大（IQData/IQEngine 两个 set_engine 只是签名恰好不同的那两例）。
"""


def classify(items, flag_a, flag_c, log):
    for name, val in items:
        if flag_a:
            out = 1
        else:
            if flag_c:
                out = val.x
            else:
                out = val.z
            try:
                out = out + val.w
            except TypeError:
                out = 0
            log.append(out)
        items[name] = out
    return items
