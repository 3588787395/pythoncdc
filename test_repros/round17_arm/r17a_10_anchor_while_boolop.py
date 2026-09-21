# -*- coding: utf-8 -*-
"""R17-A 10 anchor while + boolop conditions.

外层循环换成 **while**（判据④用的是 `_find_enclosing_loop`，对所有循环等价），
外层 if 与内层 if 的条件都带 BoolOp（`and` / `or` 短路链）。
BoolOp 自身也会造 POP_JUMP_IF_* 归并点，是最容易与 elif 归并混淆的场景。

角色：锚点（anchor）。
"""


def drain(queue, flags, seen):
    while queue:
        name, weight = queue.pop(0)
        if flags.get('stop') and weight > 0:
            seen.append(name)
        else:
            if weight > 100 or name.startswith('x'):
                kept = weight // 2
            else:
                kept = weight
            seen.append(kept)
            queue.append((name, kept))
        if len(seen) > 3:
            break
    return seen
