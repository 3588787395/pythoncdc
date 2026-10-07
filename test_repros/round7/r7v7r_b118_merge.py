"""Round 7 复核批变体探针（r7v7r_*）——B118 守卫变体面。

评审工程师独立攻击（任务 7.3）：验证 else-break 出口边显式认领守卫的
触发边界（全 MATCH 预期）：
- b118r_then_reaches_merge：then 臂可达 merge 的共享汇合形态（两臂都
  以 break 终结、假边与真臂尾跳共享出口块）——守卫条件③必须拦住
  （orelse 不得二次注入 Break）；
- b118r_then_fallthrough：then 臂尾跳共享汇合 + 循环体尾随语句（无
  else）——守卫条件②必须拦住（merge 不是 break 落点）；
- b118r_while_host：while 宿主 else-break（守卫正向适用形态变体，
  while 出口布局与 for 不同）——守卫应正确认领 orelse=[Break]。
"""
DEFAULT_ITEMS = [3, 1, -2, 0, 5]


def b118r_then_reaches_merge(items, flag):
    seen = 0
    for x in items:
        if flag:
            seen += 1
            break
        else:
            break
    return seen


def b118r_then_reaches_merge_deep(items, flag, gate):
    seen = 0
    if gate:
        for x in items:
            if flag:
                seen += 1
                break
            else:
                break
    return seen


def b118r_then_fallthrough(items, flag):
    total = 0
    for x in items:
        if flag:
            total += x
            break
        total += 1
    return total


def b118r_then_fallthrough_deep(items, flag, gate):
    total = 0
    if gate:
        for x in items:
            if flag:
                total += x
                break
            total += 1
    return total


def b118r_while_host(items, flag):
    kept = []
    rest = list(items)
    while rest:
        x = rest.pop()
        if x > 0:
            kept.append(x)
        else:
            break
    return kept


def b118r_while_host_deep(items, flag, gate):
    kept = []
    rest = list(items)
    if gate:
        while rest:
            x = rest.pop()
            if x > 0:
                kept.append(x)
            else:
                break
    return kept
