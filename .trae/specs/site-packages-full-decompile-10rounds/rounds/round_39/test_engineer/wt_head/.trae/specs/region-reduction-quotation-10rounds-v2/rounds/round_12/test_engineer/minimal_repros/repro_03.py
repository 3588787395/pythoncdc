"""repro_03: TernaryRegion 链 (共享 merge_block) - 前驱 merge 是后继 entry
区域类型: TernaryRegion chain
违反原则: 2 (每块唯一归属) + 3 (嵌套即抽象节点)
对应函数: get_str_data (TernaryRegion@844 merge=1226 = TernaryRegion@1226 entry)
缺陷镜像: 连续两个三元赋值 `x = a if c1 else b; y = m if c2 else n`，
  Python 字节码将第一个 ternary 的 STORE_x 与第二个 ternary 的 LOAD_c2 + POP_JUMP_IF_FALSE
  合并到同一基本块（共享 merge_block）。
  _generate_ternary 检测到 _shared_with_next_ternary 后不发射 extra 语句（正确），
  但 CALLER 标记 region.blocks（含共享 merge_block）为 generated，导致后继 TernaryRegion
  entry 已 generated 被跳过。违反原则 2（共享块不应被前驱独占标记）。
"""


def f(c1, c2, a, b, m, n):
    x = a if c1 else b
    y = m if c2 else n
    return (x, y)
