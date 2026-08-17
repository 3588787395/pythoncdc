#!/usr/bin/env python3
"""R93 trace: how block 2758 is generated and where JUMP_FORWARD is replaced"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion
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

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Check all IfRegions that have merge_block=2758
print("IfRegions with merge_block=2758:")
for r in regions:
    if isinstance(r, IfRegion) and r.merge_block and r.merge_block.start_offset == 2758:
        print(f"  IfRegion@{r.entry.start_offset} type={r.region_type.name} "
              f"then={len(r.then_blocks or [])} else={len(r.else_blocks or [])}")

# Check block 820's owners
block_820 = cfg.get_block_by_offset(820)
if block_820:
    print(f"\nBlock@820:")
    print(f"  predecessors: {[p.start_offset for p in block_820.predecessors]}")
    print(f"  successors: {[s.start_offset for s in block_820.successors]}")
    for instr in block_820.instructions:
        print(f"  {instr.offset:4d} {instr.opname:30s} {getattr(instr, 'argval', getattr(instr, 'arg', ''))}")
    
    # Check which region owns block 820
    owner = analyzer.get_region_for_block(block_820)
    print(f"  owner: {type(owner).__name__ if owner else 'None'}")
    if owner and hasattr(owner, 'entry'):
        print(f"  owner entry: {owner.entry.start_offset if owner.entry else '?'}")
    
    # Check block role
    role = analyzer.get_block_role(block_820)
    print(f"  role: {role}")

# Check block 2758's owners
block_2758 = cfg.get_block_by_offset(2758)
if block_2758:
    print(f"\nBlock@2758:")
    print(f"  predecessors: {[p.start_offset for p in block_2758.predecessors]}")
    for instr in block_2758.instructions:
        print(f"  {instr.offset:4d} {instr.opname:30s} {getattr(instr, 'argval', getattr(instr, 'arg', ''))}")
    
    owner = analyzer.get_region_for_block(block_2758)
    print(f"  owner: {type(owner).__name__ if owner else 'None'}")
    if owner and hasattr(owner, 'entry'):
        print(f"  owner entry: {owner.entry.start_offset if owner.entry else '?'}")
    
    role = analyzer.get_block_role(block_2758)
    print(f"  role: {role}")

# Now generate the full function AST and check the decompiled source
ast_gen = RegionASTGenerator(cfg, analyzer)
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        result = ast_gen._generate_if(r)
        
        # Check if block 2710 (merge) was generated as post-if
        print(f"\nBlock 2710 in generated: {2710 in [b.start_offset for b in ast_gen.generated_blocks]}")
        print(f"Block 2758 in generated: {2758 in [b.start_offset for b in ast_gen.generated_blocks]}")
        
        # Check the result structure
        if isinstance(result, list):
            print(f"Result: list of {len(result)} items")
            for i, item in enumerate(result):
                t = item.get('type') if isinstance(item, dict) else type(item).__name__
                print(f"  [{i}] type={t}")
        elif isinstance(result, dict):
            print(f"Result: type={result.get('type')}")
        break

# Also check: does the decompiled source have 'return None' at the end of the then branch?
from pycdc import decompile_pyc
decomp_src = decompile_pyc(target_pyc)
lines = decomp_src.split('\n')
in_func = False
func_lines = []
for i, line in enumerate(lines):
    if 'def get_multiminute_his_data' in line:
        in_func = True
    if in_func:
        func_lines.append((i+1, line))
        if len(func_lines) > 60:
            break

# Find return None statements
print("\nLines with 'return' in get_multiminute_his_data:")
for lineno, line in func_lines:
    if 'return' in line.lower():
        print(f"  {lineno:4d}: {line}")
