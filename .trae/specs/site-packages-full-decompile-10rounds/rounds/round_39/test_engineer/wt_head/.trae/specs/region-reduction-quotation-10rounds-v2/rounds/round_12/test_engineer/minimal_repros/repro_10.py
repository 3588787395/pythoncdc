"""repro_10: 综合镜像 - IfRegion(continue) else 含 LoopRegion + TernaryRegion chain
区域类型: Loop + IfRegion(continue) + LoopRegion + TernaryRegion chain
违反原则: 2 + 3 + 4 (综合违反)
对应函数: get_str_data (综合所有 R12 缺陷模式)
缺陷镜像: 完整复现 get_str_data 的 LoopRegion@610 结构：
  - IfRegion@614 (if datas: continue) merge=loop header
  - LoopRegion@760 (for j in range(...)) sibling in else
  - TernaryRegion@844 (merge=1226, compare) sibling in else
  - TernaryRegion@1226 (entry=1226=前驱 merge, store) chain successor
  验证 _if_generate_else_branch 修复后：
  1. LoopRegion@760 被 phase 1 收集分发
  2. TernaryRegion@844 被 R12 新增 phase 3 收集分发
  3. TernaryRegion@1226 的 entry(1226) 不被 @844 标记 generated，可独立生成
  综合验证原则 2（共享 merge 不独占）+ 3（嵌套即抽象节点）+ 4（else 引用子区域 entry）。
"""


def f(xs):
    out = []
    for x in xs:
        if not x:
            continue
        cnt = 0
        for j in range(x):
            cnt += j
        a = x if cnt > 0 else 0
        b = x + 1 if cnt > 1 else 1
        out.append((a, b))
    return out
