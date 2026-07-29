"""R23-N2 调试：精确追踪 convert_to_list elif 条件处理路径"""
import sys
sys.path.insert(0, '/workspace')

import core.cfg.region_ast_generator as rag_mod

# Patch _if_extract_condition_from_instructions 来追踪
_orig = rag_mod.RegionASTGenerator._if_extract_condition_from_instructions

def _patched(self, region, cond_block, cond_instrs):
    cb_off = cond_block.start_offset if cond_block else None
    # 找到 then_blocks 的 offset 集合
    then_offs = [b.start_offset for b in getattr(region, 'then_blocks', [])]
    # 是否有 BoolOpRegion
    boolop_r = None
    for r in self.regions:
        if isinstance(r, BoolOpRegion) and cond_block in r.blocks:
            boolop_r = r
            break
    boolop_chain = None
    boolop_merge = None
    if boolop_r:
        boolop_chain = [(b.start_offset, op) for b, op in boolop_r.op_chain]
        boolop_merge = boolop_r.merge_block.start_offset if boolop_r.merge_block else None
    # 只对潜在 convert_to_list 的 elif 输出（offset 40 周围）
    if cb_off is not None and 30 <= cb_off <= 50:
        print(f"\n[TRACE _if_extract_condition_from_instructions]")
        print(f"  cond_block offset: {cb_off}")
        print(f"  then_blocks: {then_offs}")
        print(f"  cond_instrs opnames: {[i.opname for i in cond_instrs[:5]]}")
        print(f"  BoolOpRegion found: {boolop_r is not None}")
        if boolop_r:
            print(f"    op_chain: {boolop_chain}")
            print(f"    merge: {boolop_merge}")
        # 调用原始方法
        result = _orig(self, region, cond_block, cond_instrs)
        print(f"  RESULT: {result}")
        return result
    return _orig(self, region, cond_block, cond_instrs)

rag_mod.RegionASTGenerator._if_extract_condition_from_instructions = _patched

# 反编译
from pycdc import decompile_pyc
PYC = '/workspace/quotation.pyc'
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)

import re
m = re.search(r'def convert_to_list\(item\):.*?(?=\ndef [a-z]|\nclass )', src, re.DOTALL)
if m:
    print("\n=== Decompiled convert_to_list ===")
    print(m.group(0))
else:
    print("convert_to_list not found, dumping all match")
    for m in re.finditer(r'def (\w+)\(', src):
        print(f"  found: {m.group(1)}")
