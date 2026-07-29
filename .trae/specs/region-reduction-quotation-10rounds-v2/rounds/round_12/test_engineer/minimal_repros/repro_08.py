"""repro_08: IfRegion(continue) merge=loop header（else 自然延伸到循环尾）
区域类型: Loop + IfRegion(continue)
违反原则: 4 (入口引用语义)
对应函数: get_str_data (IfRegion@614 merge=610=loop header)
缺陷镜像: `for x in xs: if not x: continue; out.append(x)`
  IfRegion(not x) 的 then=JUMP_BACKWARD(continue)，else=循环体剩余块，
  merge_block=loop header（then 与 else 都回到循环头）。
  IfRegion.else_blocks 包含循环体所有后续块（含兄弟子区域 entry）。
  这是 IfRegion(continue) 的标准结构，但 else_blocks 范围过大，
  _if_generate_else_branch 必须正确分发 else 中的所有子区域。
  违反原则 4（else 应引用子区域 entry，不展开子区域块）。
"""


def f(xs):
    out = []
    for x in xs:
        if not x:
            continue
        out.append(x)
    return out
