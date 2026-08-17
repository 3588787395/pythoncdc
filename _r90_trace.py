#!/usr/bin/env python3
"""R90 trace AST generation for get_kline_by_count_new"""
import sys, os, dis, marshal, types, json
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
if not func_code:
    print("Function not found!")
    sys.exit(1)

builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

block0 = cfg.get_block_by_offset(0)
if block0 is None:
    print("Block at offset 0 not found!")
    sys.exit(1)

print("=== Block at offset 0 instructions ===")
for instr in block0.instructions:
    argval = getattr(instr, 'argval', getattr(instr, 'arg', ''))
    print(f"  {instr.offset:4d} {instr.opname:30s} {argval}")

print(f"\nblock_role: {ast_gen.block_role(block0)}")
print(f"has_unpack: {any(i.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX') for i in block0.instructions)}")

# Try generating statements for this block
try:
    stmts = ast_gen._generate_block_statements(block0)
    print(f"\n=== Generated statements ({len(stmts)}) ===")
    for i, s in enumerate(stmts):
        print(f"  [{i}] {json.dumps(s, default=str, indent=2)}")
except Exception as e:
    import traceback
    print(f"\nError: {e}")
    traceback.print_exc()
