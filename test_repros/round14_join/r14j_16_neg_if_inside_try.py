# -*- coding: utf-8 -*-
"""R14-J 16 负对照：**反向嵌套** `try: if b: …`（try 在外、if 在内）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
成分与 r14j_12 完全相同（BoolOp 赋值 + if + try），只把嵌套方向反过来。
此时 `if b:` 的头块是 `LOAD b | POP_JUMP_IF_FALSE`，**不再**同时是 BoolOp 的
merge 块（BoolOp 的值 STORE 已在 try 体首块里被消费），
IfRegion 正常建立、try 在外层，归约顺序天然正确，
⇒ 证明「BoolOp merge 块 == if 头块」才是必要条件，而不是 try 区域
   在 block_to_region 里抢块（任务书里的原假设，已被否决：
   真实区域树里根本没有抢块行为，IfRegion 压根没被创建）。

实测（严格尺子）：<module> **MATCH**。
"""
a = 1
b = a and 2
try:
    if b:
        c = 1
except ValueError:
    pass
