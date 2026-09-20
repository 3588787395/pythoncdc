# -*- coding: utf-8 -*-
"""R16-A 09 差分负对照：同一 entry-steal 形状，但 try 挂在 **else 臂**。

这是「生成层 vs 结构层」的关键判决实验：区域树里 Try@<入口> 与 BoolOp@<同一入口>
在两个臂里是同一个分析层产物（parent/children 完全对称），唯一区别是消费方：
  * then 臂 = `_if_generate_then_branch`：表达式子区域**先**预生成（13947 起），
    随后 `_process_if_blocks` 才拿到已被污染的 generated_blocks；
  * else 臂 = `_try_collect_c3`：**先**收结构子区域（14665-14668），BoolOp/Ternary
    排在其后（14677-14680）。

预测：本项 MATCH、01/02/03 MISMATCH ⇒ 差异纯在生成层的两臂顺序不对称，
候选修复即「让 then 臂复用 else 臂的收集顺序」。
"""


def check_try_in_else_arm(value):
    if value is None:
        valid = True
    else:
        valid = isinstance(value, str) and len(value) == 5
    if valid:
        print('ok')
    else:
        try:
            valid = 1990 <= int(value) <= 9999 and 1 <= int(value) <= 4
        except (ValueError, TypeError):
            valid = False
    print(valid)
