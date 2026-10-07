# Source Generated with Decompyle++ (Python version)
# File: r7v7r_b117_f2tail.pyc (Python 3.11)

__doc__ = """Round 7 复核批变体探针（r7v7r_*）——B117 守卫变体面。

评审工程师独立攻击（任务 7.3）：验证 then 臂吸收守卫与 else-continue
尾区域前置守卫在评审批未覆盖的变体形态下不误伤（全 MATCH 预期）：
- b117r_f2_shared_tail：f2 共享尾形态（回边块前驱全部在区域汇合侧，
  无区域外前驱）——吸收守卫必须不触发（否则 then_blocks 被错误摘除）；
- b117r_tail_depth2：深度 2 宿主下 if 区域仍覆盖整个循环体（尾区域）
  ——尾区域谓词必须放行既有降级重排（不误伤）；
- b117r_while_host：while 宿主 + 宿主顺序后继（B117 修复形态的 while
  变体）——守卫必须保住显式 else: continue（漏接检查）。
"""
DEFAULT_ITEMS = [3, 1, -2, 0, 5]
def b117r_f2_shared_tail(items, flag):
    acc = 0
    if flag:
        for x in items:
            if x > 0:
                acc += x
    return acc
def b117r_f2_shared_tail_deep(items, flag):
    acc = 0
    if flag and items:
        for x in items:
            if x > 0:
                acc += x
    return acc
def b117r_tail_depth2(items, flag):
    acc = 0
    if flag:
        for x in items:
            if x > 0:
                acc += x
                continue
    else:
        acc = -1
    return acc
def b117r_tail_depth2_deep(items, flag, gate):
    acc = 0
    if flag:
        if gate:
            for x in items:
                if x > 0:
                    acc += x
                    continue
    else:
        acc = -1
    return acc
def b117r_while_host(items, flag):
    acc = 0
    rest = list(items)
    while rest:
        x = rest.pop()
        if flag:
            if x > 0:
                acc += x
            else:
                continue
        acc += 1
    return acc
def b117r_while_host_deep(items, flag, gate):
    acc = 0
    rest = list(items)
    while gate:
        while rest:
            x = rest.pop()
            if flag:
                if x > 0:
                    acc += x
                else:
                    continue
            acc += 1
    return acc
