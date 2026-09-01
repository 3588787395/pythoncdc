"""repro_05: IfRegion(continue) else 含 BoolOpRegion（表达式区域）
区域类型: Loop + IfRegion(continue) + BoolOpRegion
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: get_str_data (BoolOpRegion 兄弟在 IfRegion else)
缺陷镜像: `for x in xs: if not x: continue; v = a or b; out.append(v)`
  BoolOpRegion(a or b) 的 entry 在 IfRegion(not x) 的 else_blocks 中。
  _if_generate_else_branch 不收集 BoolOpRegion，将其 entry 当作普通块平坦化。
  违反原则 3（BoolOpRegion 应作为抽象节点）+ 原则 4（else 应引用子区域 entry）。
"""


def f(xs, a, b):
    out = []
    for x in xs:
        if not x:
            continue
        v = a or b
        out.append(v)
    return out
