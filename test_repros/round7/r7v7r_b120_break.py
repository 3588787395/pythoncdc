"""Round 7 复核批变体探针（r7v7r_*）——B120 守卫变体面。

评审工程师独立攻击（任务 7.3）：验证祖先汇合块守卫的触发边界
（全 MATCH 预期）：
- b120r_own_break_target：break 落点专属本循环（函数级尾随块，无祖先
  merge_block 同一性）——守卫必须不触发；
- b120r_fin_break：try/finally 内 break（fin_break 形态，r10_21 家族
  变体）——守卫必须不触发；
- b120r_forelse_own：for-else + 独占 break 落点（B120 家族但无宿主
  if 汇合共享）——守卫必须不触发；
- b120r_host_if_shared：宿主 if 假边与 break 边共享循环后汇合块
  （守卫正向适用形态：祖先 merge 命中，交宿主层发射）。
"""
DEFAULT_ITEMS = [3, 1, -2, 0, 5]


def b120r_own_break_target(items, flag):
    out = []
    for x in items:
        if x > 10:
            break
        out.append(x)
    out.append(flag)
    return out


def b120r_own_break_target_deep(items, flag, gate):
    out = []
    if gate:
        for x in items:
            if x > 10:
                break
            out.append(x)
    out.append(flag)
    return out


def b120r_fin_break(rows):
    total = 0
    for r in rows:
        try:
            total += r
        finally:
            if total > 100:
                break
    return total


def b120r_forelse_own(items, flag):
    acc = 0
    for x in items:
        if x < 0:
            break
        acc += x
    else:
        acc += 100
    acc += 1
    return acc


def b120r_host_if_shared(items, flag):
    acc = 0
    if flag:
        for x in items:
            if x < 0:
                break
            acc += x
    return acc


def b120r_host_if_shared_deep(items, flag, gate):
    acc = 0
    if flag:
        if gate:
            for x in items:
                if x < 0:
                    break
                acc += x
    return acc
