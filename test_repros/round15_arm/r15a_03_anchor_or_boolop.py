# -*- coding: utf-8 -*-
"""R15-A 03 anchor or boolop
03 BoolOp 用 `or` 而不是 `and`（条件短路方向相反）。

真实目标：同上。`or` 的 merge 块里同样是 `STORE flag | LOAD flag | POP_JUMP_IF_FALSE`，
所以「双角色块」判据与 op 类型无关；若 `or` 不复现，说明认领逻辑对 op 有隐含偏向。
"""

def check_or(value):
    if value is None:
        flag = True
    else:
        flag = value or 'q'
        if flag:
            try:
                flag = 1990 <= int(flag) <= 9999
            except (ValueError, TypeError):
                flag = False
    return flag
