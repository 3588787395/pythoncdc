"""R23-N2 调试：追踪所有 _if_extract_condition_from_instructions 调用"""
import sys
sys.path.insert(0, '/workspace')

import core.cfg.region_ast_generator as rag_mod

_orig = rag_mod.RegionASTGenerator._if_extract_condition_from_instructions

def _patched(self, region, cond_block, cond_instrs):
    cb_off = cond_block.start_offset if cond_block else None
    then_offs = [b.start_offset for b in getattr(region, 'then_blocks', [])]
    boolop_r = None
    for r in self.regions:
        if isinstance(r, rag_mod.BoolOpRegion) and cond_block in r.blocks:
            boolop_r = r
            break
    boolop_chain = [(b.start_offset, op) for b, op in boolop_r.op_chain] if boolop_r else None
    boolop_merge = boolop_r.merge_block.start_offset if boolop_r and boolop_r.merge_block else None
    print(f"[TRACE] cond_block={cb_off} then={then_offs} boolop={boolop_chain} merge={boolop_merge}")
    result = _orig(self, region, cond_block, cond_instrs)
    # 只对潜在 a and not(b or c) 模式输出结果
    if boolop_chain and len(boolop_chain) >= 2 and 'and' in [op for _, op in boolop_chain] and 'or' in [op for _, op in boolop_chain]:
        print(f"  RESULT for mixed and/or: {result}")
    return result

rag_mod.RegionASTGenerator._if_extract_condition_from_instructions = _patched

from pycdc import decompile_pyc
PYC = '/workspace/quotation.pyc'
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)

# 写入文件再读
with open('/tmp/r23n2_trace.py', 'w', encoding='utf-8') as f:
    f.write(src)

import re
m = re.search(r'def convert_to_list\(item\):(?:.|\n)*?(?=\ndef [a-z]|\nclass |\Z)', src)
if m:
    print("\n=== convert_to_list ===")
    print(m.group(0)[:1500])
