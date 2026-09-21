# -*- coding: utf-8 -*-
"""R17-A 06 anchor：尾随语句是 **with 块**。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 with + 尾随赋值），链后再一条赋值。
with 在 3.11 生成 SETUP_WITH/异常边，inner_merge 落在 with 入口块。
实测：block=44 first_else=62 inner_merge=140 merge_=282 inloop=True term=False；
pre-patch MISMATCH（target_diff #13 orig=('n',LOAD_FAST) decomp=('store',LOAD_FAST)）
→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def snapshot(state, store):
    for name, value in state.items():
        if value is None:
            n = 0
        else:
            if isinstance(value, int):
                n = value
            else:
                n = len(value)
            with store.lock():
                store.write(name, n)
            state[name] = n
        state['last'] = n
    return state
