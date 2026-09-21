# -*- coding: utf-8 -*-
# R22 锚点 28 —— J3' 边界 NOP 折叠：elif 链尾 `else: pass` 被全局判据拒绝还原。
#
# 规则站点 core/cfg/region_ast_generator.py::_is_orphan_boundary_nop
# 被删除的 [A4/V-M] 子句（base 41230-41237）：
#     for blk in self.cfg.get_blocks_in_order():        # 全 CFG 扫描
#         for bi2 in blk.instructions:
#             if (bi2.opname in CONDITIONAL_JUMP_OPS
#                     and getattr(bi2, 'argval', None) == nop_off):
#                 return False                          # ← 全局（跨区域）判据
# 该 NOP 正是本结构自己那条 elif 条件跳转的落点，属"由外层条件结构自动再生"
# 的语句边界锚点，但判据不带区域归属信息 → 只要 CFG 里**任何地方**有一条条件
# 跳转指向它就拒绝折叠。
#
# 语料锚点 site-packages/fly/common/flytools.pyc <module>.whitelist_filter
#   base: seq_len orig=116 decomp=114（两个 elif 链的 else 臂各丢一条 JUMP_FORWARD）
#   after: ok（产物补回两处 `else: while False: pass`）
# 本复现（<module>.f，orig=29）：base=MISMATCH decomp=28，after=MATCH。
# 类别 FIX（仅 mirror/j3 可修；J1'/J2' 单独都无效）。
def f(mode, b):
    if mode == 1:
        if b:
            print(1)
    elif mode == 2:
        if b:
            print(2)
    else:
        pass
    print('tail')
