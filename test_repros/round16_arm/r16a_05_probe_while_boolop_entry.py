# -*- coding: utf-8 -*-
"""R16-A 05 探针：被抢入口的是 **LoopRegion** 而不是 TryExceptRegion。

`while A and B:` 的条件 BoolOp 与循环区域共享入口块（条件就在循环头块里），
与 try 的情形同构。候选谓词把 LoopRegion 一并列为「结构兄弟」，本项即检验
这一泛化是否真的必要 / 是否有效。

若 MATCH ⇒ 循环入口未被动过（Loop 走 _loop_entry_generate 的另一条判据），
候选里的 LoopRegion 一项应降为「防御性、非必需」。
"""


def check_while_boolop(value):
    n = int(value)
    if n > 0:
        while n > 0 and n < 100:
            n -= 1
    return n
