"""Round 7 复核批变体探针（r7v7r_*）——新破口 B121 最小复现（复核批发现）。

形态：宿主 if（条件非循环变量）与 while 循环的假边共享同一出口目标
（POP_JUMP_FORWARD_IF_FALSE 同落循环汇合块）时，识别侧把宿主 if 条件
吸收为 while 头条件（`if gate: while rest:` 被重建为
`while gate: while rest:`）——gate 由「进入前测一次」变为「每迭代重测」。
控制流语义改变（若 body 修改 gate 则死循环/提前退出差异；字节层面出口
边拓扑不同）。复核批实测：49e5301b 基线与修复批代码同样失败
（基线 r7v7r_b117_f2tail 5/7、修复 6/7，失败单元均为
b117r_while_host_deep 同型）⇒ 与 B117–B120 四守卫无关的存量缺口，
由本复核批变体攻击（B117 while 宿主变体）首次登记。
"""

def b121r_minimal(items, gate):
    rest = list(items)
    if gate:
        while rest:
            rest.pop()
    return len(rest)


def b121r_minimal_shallow(items, gate):
    rest = list(items)
    if gate:
        while rest:
            rest.pop()
    return len(rest)


def b121r_min_continue(items, gate, flag):
    rest = list(items)
    if gate:
        while rest:
            rest.pop()
            if flag:
                continue
    return len(rest)


def b121r_min_continue_deep(items, gate, flag, gate2):
    rest = list(items)
    if gate2:
        if gate:
            while rest:
                rest.pop()
                if flag:
                    continue
    return len(rest)
