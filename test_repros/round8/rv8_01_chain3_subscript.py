# rv8_01: B54 判据面变体攻击 —— 三目标链式赋值 × 下标 RHS / 混合容器目标链 / 链后 return 表达式
# 判据边界：_b54_scan_chain_continuation 的「非末目标 COPY 1 前导 / 末目标直接消费」
# 对 n=3 链、下标值 RHS（BINARY_SUBSCR 在值段）、Name+Attr+Subscript 混合目标的适用性。


def chain3_subscript_rhs(xs, i, j):
    a = b = c = xs[i] + xs[j]
    return a + b + c


def chain3_all_subscript(m, v):
    m['x'] = m['y'] = m['z'] = v
    return m


def chain_mixed_targets(o, p, m, v):
    o.a = p.b = m['k'] = v
    return o, p, m


def chain_then_return_expr(xs, i):
    a = b = xs[i]
    return a * 2 + b


def chain_value_boolop(x, y):
    a = b = c = (x or y) and (x and y)
    return a, b, c


def single_assign_negctrl(q, w):
    q = w
    return q
