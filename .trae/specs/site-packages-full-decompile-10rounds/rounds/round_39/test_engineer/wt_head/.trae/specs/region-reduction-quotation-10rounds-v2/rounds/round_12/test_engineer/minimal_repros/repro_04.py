"""repro_04: IfRegion(continue) else 含兄弟 LoopRegion + TernaryRegion
区域类型: Loop + IfRegion(continue) + LoopRegion + TernaryRegion
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: get_str_data (LoopRegion@760 + TernaryRegion@844/@1226 在 IfRegion@614 else)
缺陷镜像: `for x in xs: if not x: continue; for j in range(...): ...; v = a if c else b`
  IfRegion(not x) 的 else_blocks 同时包含兄弟 LoopRegion 和 TernaryRegion 的 entry。
  现有 _if_generate_else_branch phase 1 收集 Try/With/Loop children（LoopRegion 被收集），
  但不收集 TernaryRegion/BoolOpRegion（表达式区域被漏）。
  违反原则 3（所有嵌套区域都应作为抽象节点）+ 原则 4（else 应引用所有子区域 entry）。
"""


def f(xs, a, b):
    out = []
    for x in xs:
        if not x:
            continue
        cnt = 0
        for j in range(x):
            cnt += j
        v = a if cnt > 0 else b
        out.append(v)
    return out
