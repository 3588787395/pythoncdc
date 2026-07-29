"""repro_02: IfRegion(continue) 的 else_blocks 包含兄弟 TernaryRegion entry
区域类型: Loop + IfRegion + TernaryRegion
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: get_str_data (TernaryRegion@844/@1226 被误吞)
缺陷镜像: `for x in xs: if not x: continue; v = a if cond else b; out.append(v)`
  IfRegion(not x) 的 else_blocks 包含 TernaryRegion(a if cond else b) 的 entry。
  _if_generate_else_branch 不查询 get_entry_region_for_block，将 TernaryRegion entry
  当作普通顺序块处理，平坦化为 _process_if_blocks 输出，标记 generated。
  违反原则 3（TernaryRegion 应作为抽象节点）+ 原则 4（else 应引用子区域 entry）。
"""


def f(xs, a, b):
    out = []
    for x in xs:
        if not x:
            continue
        cond = x > 0
        v = a if cond else b
        out.append(v)
    return out
