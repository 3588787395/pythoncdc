"""repro_03: BUILD_CONST_KEY_MAP 消费模式 — 循环内 dict 构造 (loop body consumption)。

测试 aspect: dict 构造位于 for 循环体内，BUILD_CONST_KEY_MAP+STORE_SUBSCR 作为循环
主体的归约节点。循环每轮构造一个 dict 并通过 STORE_SUBSCR 写入容器下标。三元 value 的
merge_block 在循环 FOR_ITER 反向边之前消费。反编译器需保证 dict 构造作为循环体内的
单条语句归约，不被拆散到循环 region 之外。

    for i in items:
        result[i] = {'k': v if cond else 0, 'w': w}
"""


def f(items, w):
    result = {}
    for i in items:
        cond = i > 0
        result[i] = {
            'k': i if cond else 0,
            'w': w,
        }
    return result
