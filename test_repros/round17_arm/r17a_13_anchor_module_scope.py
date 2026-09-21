# -*- coding: utf-8 -*-
"""R17-A 13 anchor：同一形状放在 **模块级 for 循环**（不包在函数里）。

形状：module → for → if/else（else 臂 = 嵌套 if/else + 两条尾随赋值），链后一条赋值。
判据④只看循环归属、不看作用域层级，故模块级 `<module>` 码对象同样中招。
实测：block=18 first_else=36 inner_merge=136 merge_=188 inloop=True term=False；
pre-patch MISMATCH（target_diff #16 JUMP 终点 orig=('text',LOAD_NAME)
decomp=(4,'LOAD_CONST')）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


TUNED = {}


def _pad(text, width):
    return text + ' ' * width


for key, val in (('a', 'x'), ('b', None), ('c', 12), ('d', None)):
    if val is None:
        text = ''
    else:
        if isinstance(val, str) and len(val) > 1:
            text = repr(val)
        else:
            text = str(val)
        width = 4 - len(text)
        text = _pad(text, width)
    TUNED[key] = text
