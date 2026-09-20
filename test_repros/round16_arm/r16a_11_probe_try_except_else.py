# -*- coding: utf-8 -*-
"""R16-A 11 探针：try/except/**else** 且 try 体首语句即 BoolOp。

真实目标里 TryExceptRegion.has_else=True、else_blocks=[238]（即那条
`JUMP_FORWARD 290`，被算进 else_blocks）。本项检验：若 try 找回来了，
else 臂是否也一起回来（还是只回 try+except、把 else 吞掉）。

用于给候选修复定验收口径：01/02/03 的 `orig-decomp` 差额必须为 0，本项亦然。
"""


def check_try_except_else(value):
    if isinstance(value, str):
        try:
            valid = int(value) > 0 and int(value) < 100
        except ValueError:
            valid = False
        else:
            print('checked')
        return valid
    return False
