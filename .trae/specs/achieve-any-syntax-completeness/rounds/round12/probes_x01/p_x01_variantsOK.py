# Source Generated with Decompyle++ (Python version)
# File: p_x01_variants.pyc (Python 3.11)

"""x01 族合成变体：折叠常量控制行头 + 行标记 NOP 计数/对齐 + docstring。

覆盖族（Task 3.2/3.3 修复的结构族，I.4 白名单判据，无任何测试名特判）：
  A. 折叠 if 行头 + 内联体（1 NOP 头 + 体语句）      → v1_head_inline
  B. 折叠 if 行头 + pass 体（非末位，2 NOP 游程）     → v2_head_pass
  C. while 1 宿主内折叠 if 头（回边目标 = 体首 NOP）  → v3_while_host
  D. try/if1/try/if1/体 finally（内联副本行位 NOP）   → v4_try_fin
  E. 模块 docstring 字面量 + 函数 docstring           → 本文件头 + 各函数
所有函数均可调用（call_exprs 覆盖 R1 执行语义）。
"""
DOC_CONST = 'module-level docstring is restored as a literal expression'
def v1_head_inline():
    """折叠 if 行头直落体：行头 NOP + 体语句同块。"""
    if 1:
        R = 1
    return R
def v2_head_pass():
    """折叠 if 行头 + pass 体（非末位）：if 行 + pass 行双 NOP 游程。"""
    if 1:
        pass
    R = 2
    return R
def v3_while_host(n):
    """while 1 宿主内折叠 if 头：回边目标为体首行 NOP（可执行出口）。"""
    if 1:
        pass
    R = n + 1
    """"""
    return R
def v4_try_fin():
    """try/if1/try/if1/体 finally：finally 内联副本行位 NOP 再生。"""
    try:
        if 1:
            try:
                if 1:
                    R = 11
            finally:
                F = 1
    except ValueError:
        R = 22
    return R
def v5_head_orphan():
    """孤立折叠残留（while False: pass）与折叠行头同函数共存。"""
    while False:
        pass
    if 1:
        R = 5
    return R
def main():
    return [v1_head_inline(), v2_head_pass(), v3_while_host(41), v4_try_fin(), v5_head_orphan()]
