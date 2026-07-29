"""repro_01: 复现 fill_minute_or_day_blank 反编译缺陷（ternary merge block 后续赋值丢失）。

缺陷模式：`x = a if cond else b`（三元，merge block 含 STORE_FAST）后跟
`y = foo(); z = bar(); if len(z) > 0: ...` —— ternary STORE_* 与 if 条件之间
的独立赋值（y=, z=）被丢弃。

根因：region_ast_generator.py _if_extract_cond_instructions 中 _cond_block_is_ternary_merge
标志对 cond_block（TernaryRegion.merge_block）内所有 STORE_* 生效，导致 ternary
STORE_* 之后的独立赋值被跳过（IfRegion 条件块内前置赋值丢失）。

R4 该函数 diff=-42，R5 修复 _cond_block_is_ternary_merge 清除后恢复 3 条赋值，diff 改善至 -30。
"""


def fill_blank(nowend, nowstart, seq):
    if nowend >= nowstart:
        code = seq[0] if seq else ''
        source_start = seq[0]
        source_end = seq[1]
        dts = list(seq)
        if len(dts) > 0:
            klines = dts
    return klines
