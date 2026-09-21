# -*- coding: utf-8 -*-
"""R17-A 27 度量盲区证据：与 04 同一形状，但外层 merge 首指令与尾随首指令签名相同。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 while + 尾随 `clamped.append(name)`），
链后是 `values[name] = n`。
实测：block=44 first_else=62 inner_merge=166 merge_=242 inloop=True term=False，
pre-patch 确实展平（反编译结果把 while/append 外提到链后，None 分支也会执行它们），
但 CPython 为 `values[name] = n` 先发射 `LOAD_FAST n`，与 while 头块
（`LOAD_FAST n; LOAD_FAST limit; COMPARE_OP`）首指令逐字相同，
strict_compare 的单指令终点签名无法区分 ⇒ 实测 MATCH。
角色：尺子盲区（两世界均 MATCH，标 UNCONFIRMED），说明 ④ 的真实影响面大于
target_diff 计数。"""


def clamp(values, limit, clamped):
    for name, raw in values.items():
        if raw is None:
            n = 0
        else:
            if isinstance(raw, int):
                n = raw
            else:
                n = int(float(raw))
            while n > limit:
                n = n // 2
            clamped.append(name)
        values[name] = n
    return values
