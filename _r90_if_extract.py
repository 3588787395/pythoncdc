#!/usr/bin/env python3
"""R90 验证 _if_extract_cond_instructions 的 pre_stmts 输出"""
import sys, os, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_kline_by_count_new')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

block0 = cfg.get_block_by_offset(0)

# Find the IfRegion that has block0 as condition_block
from core.cfg.region_analyzer import IfRegion
target_region = None
for r in regions:
    if isinstance(r, IfRegion) and r.condition_block is block0:
        target_region = r
        break

if target_region:
    print(f"Found IfRegion with condition_block=block0")
    print(f"IfRegion entry: {target_region.entry.start_offset if target_region.entry else '?'}")
    print(f"IfRegion condition_block: {target_region.condition_block.start_offset if target_region.condition_block else '?'}")
    
    # Call _if_extract_cond_instructions directly
    pre_stmts, cond_instrs = ast_gen._if_extract_cond_instructions(block0, target_region)
    
    print(f"\npre_stmts ({len(pre_stmts)}):")
    for i, s in enumerate(pre_stmts):
        print(f"  [{i}] {json.dumps(s, default=str)[:200]}")
    
    print(f"\ncond_instrs ({len(cond_instrs)}):")
    for i, instr in enumerate(cond_instrs):
        argval = getattr(instr, 'argval', getattr(instr, 'arg', ''))
        print(f"  [{i}] {instr.opname:30s} {argval}")
else:
    print("No IfRegion found with block0 as condition_block")
    # Check what region block0 belongs to
    for r in regions:
        if block0 in r.blocks:
            print(f"  block0 is in {type(r).__name__}, entry={r.entry_block.start_offset if hasattr(r, 'entry_block') else '?'}")
