"""repro_06: IfRegion(continue) + 嵌套 IfRegion 在 else（非 continue 模式）
区域类型: Loop + IfRegion(continue) + IfRegion
违反原则: 4 (入口引用语义)
对应函数: get_str_data (IfRegion@762/@788 在 IfRegion@614 else)
缺陷镜像: `for x in xs: if not x: continue; if x > 5: out.append(x)`
  IfRegion(x > 5) 的 entry 在 IfRegion(not x) 的 else_blocks 中。
  现有 phase 2 收集 IfRegion children，但若 IfRegion 是 sibling（非 children）则漏。
  违反原则 4（else 应引用所有子区域 entry，含 sibling IfRegion）。
"""


def f(xs):
    out = []
    for x in xs:
        if not x:
            continue
        if x > 5:
            out.append(x)
    return out
