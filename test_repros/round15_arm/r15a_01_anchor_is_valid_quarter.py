# -*- coding: utf-8 -*-
"""R15-A 01 anchor is valid quarter
01 锚点：`_is_valid_quarter` 的最小化真实形状。

真实目标：site-packages/IQCommon/arg_checker.pyc `<module>.ArgumentChecker._is_valid_quarter`
（同名重复源 3 份：IQCommon、IQData/utils、IQEngine/utils，现均 48/49）。
形状 = 「值上下文 BoolOp 的 merge 块同时是下一条 `if <同一名字>:` 的入口块」，
且该 if 的 then 臂整体是一个 TryExceptRegion。

假设（待实测）：IfRegion 整条丢失，产物只剩 `valid = ... and ...` + 挂到祖父臂上的 try，
严格尺子 seq_len 少 2 条（`LOAD_FAST valid; POP_JUMP_FORWARD_IF_FALSE`）。
"""

def check_quarter(value):
    if value is None:
        valid = True
    else:
        valid = isinstance(value, str) and value[-1] == 'q'
        if valid:
            try:
                valid = 1990 <= int(value[:-1]) <= 9999
            except (ValueError, TypeError):
                valid = False
    if not valid:
        raise ValueError(value)
    return valid
