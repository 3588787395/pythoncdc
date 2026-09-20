# -*- coding: utf-8 -*-
"""R14-17 负对照：**set 字面量**里两个推导式（尾部消费者 BUILD_SET）→ 不坍缩。

形状：`{[x for x in t][0], [y for y in u][0]}`
（set 元素必须可哈希，故用 list 推导式取下标；关键是块内仍有两个相邻
 MAKE_FUNCTION，尾部消费者是 `BUILD_SET 2`。）
`_expr_build` 白名单含 'BUILD_SET' ⇒ 逃逸判据生效 ⇒ 正确重建。
与 r14_07（BUILD_LIST）/ r14_08（BUILD_TUPLE）合起来构成消费者 opcode 的
**三分量表**：BUILD_LIST/BUILD_TUPLE/BUILD_SET 正确，BUILD_CONST_KEY_MAP 与
CALL* 错误 —— 缺陷面被完整夹在「白名单缺项」这一个集合上。
期望：MATCH（负对照，必须保持一致）。
"""


def set_two_comps(t, u):
    return {[x for x in t][0], [y for y in u][0]}
