"""R23-N2 调试：追踪 _if_generate_elif_chain 中 elif 条件构建路径"""
import sys
sys.path.insert(0, '/workspace')

import core.cfg.region_ast_generator as rag_mod

# Patch _if_generate_elif_chain 来追踪每个 elif 条件
_orig_elif = rag_mod.RegionASTGenerator._if_generate_elif_chain

def _patched_elif(self, region):
    if not getattr(region, 'elif_conditions', None):
        return _orig_elif(self, region)
    # 输出 elif 信息
    elif_conds = getattr(region, 'elif_conditions', [])
    elif_bodies = getattr(region, 'elif_bodies', [])
    print(f"\n[TRACE _if_generate_elif_chain]")
    print(f"  condition_block: {region.condition_block.start_offset if region.condition_block else None}")
    print(f"  elif_conditions: {[ec.start_offset for ec in elif_conds]}")
    if elif_bodies:
        print(f"  elif_bodies[0]: {[b.start_offset for b in elif_bodies[0]]}")
    if region.elif_final_else:
        print(f"  elif_final_else: {[b.start_offset for b in region.elif_final_else]}")
    # 检查每个 elif_cond_block 是否在 BoolOpRegion 中
    for ec in elif_conds:
        boolop_r = None
        for r in self.regions:
            if isinstance(r, rag_mod.BoolOpRegion) and ec in r.blocks:
                boolop_r = r
                break
        if boolop_r:
            print(f"  elif_cond {ec.start_offset}: BoolOpRegion op_chain={[(b.start_offset, op) for b, op in boolop_r.op_chain]} merge={boolop_r.merge_block.start_offset if boolop_r.merge_block else None}")
        else:
            print(f"  elif_cond {ec.start_offset}: NO BoolOpRegion")
            # 显示该块的最后指令
            last = ec.get_last_instruction()
            if last:
                print(f"    last instr: {last.opname} argval={last.argval}")
    result = _orig_elif(self, region)
    if isinstance(result, list):
        for i, r in enumerate(result):
            if isinstance(r, dict) and r.get('type') == 'If':
                test = r.get('test')
                if isinstance(test, dict):
                    print(f"  result[{i}] If test type: {test.get('type')}")
    return result

rag_mod.RegionASTGenerator._if_generate_elif_chain = _patched_elif

from pycdc import decompile_pyc
PYC = '/workspace/quotation.pyc'
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)

import re
m = re.search(r'def convert_to_list\(item\):(?:.|\n)*?(?=\ndef [a-z]|\nclass |\Z)', src)
if m:
    print("\n=== convert_to_list ===")
    print(m.group(0)[:2000])
