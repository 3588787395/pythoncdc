"""repro_03: get_str_data 根因 B — _process_if_blocks 遗漏兄弟表达式子区域。

模拟 get_str_data 的 IfRegion@614：循环体内 if not datas: continue，else 分支包含
兄弟 TernaryRegion（parent 是外层 LoopRegion，非 IfRegion）。_process_if_blocks 仅从
region.children 收集，遗漏 else_blocks 中的兄弟三元，导致 entry 被平坦化为顺序块。

违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。

后续迭代建议：在 BUILD_CONST_KEY_MAP 消费模式建模稳定后，扩展 _process_if_blocks
从 then_blocks/else_blocks 收集兄弟表达式子区域。
"""


def f(datas):
    out = {}
    i = 0
    for datas in datas_list:
        if not datas:
            continue
        else:
            out[i] = datas if len(datas) > 0 else None
        i += 1
    return out


datas_list = [[1], [], [2, 3]]
