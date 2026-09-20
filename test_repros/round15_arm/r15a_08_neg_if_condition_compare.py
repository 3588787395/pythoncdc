# -*- coding: utf-8 -*-
"""R15-A 08 neg if condition compare
08 子 if 的条件是**比较式**而不是刚被赋的那个名字——原设计当负对照，实测被否证。

真实目标：同上。实测 **MISMATCH（41→37）** ⇒ 缺陷不依赖「merge 块尾是裸名复读」这一
形态；条件表达式样式只影响丢失条数，不影响归属判定 ⇒ 修复必须落在**臂边界归属**，
不得针对「裸名条件」写判据。
"""

def check_cmp(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag != 'q':
            try:
                flag = bool(value)
            except ValueError:
                flag = False
    return flag
