#!/usr/bin/env python3
"""R90 verify _if_extract_cond_instructions for block0"""
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

# Test: Call _if_extract_cond_instructions directly (BoolOpRegion path: region=None)
print("=== _if_extract_cond_instructions(block0, None) ===")
pre_stmts, cond_instrs = ast_gen._if_extract_cond_instructions(block0, None)
print(f"pre_stmts ({len(pre_stmts)}):")
for i, s in enumerate(pre_stmts):
    print(f"  [{i}] {json.dumps(s, default=str)[:300]}")
print(f"\ncond_instrs ({len(cond_instrs)}):")
for i, instr in enumerate(cond_instrs):
    argval = getattr(instr, 'argval', getattr(instr, 'arg', ''))
    print(f"  [{i}] {instr.opname:30s} {argval}")
