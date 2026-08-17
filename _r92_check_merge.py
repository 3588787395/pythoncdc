#!/usr/bin/env python3
"""R92 check: is IfRegion@0's merge_block correctly generated?"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
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
ast_gen = RegionASTGenerator(cfg, analyzer)

for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        print(f"IfRegion@0: type={r.region_type.name} merge={r.merge_block.start_offset}")
        print(f"  merge_block in then_blocks: {r.merge_block in r.then_blocks}")
        print(f"  merge_block in else_blocks: {r.merge_block in (r.else_blocks or [])}")
        
        # Generate and check
        result = ast_gen._generate_if(r)
        
        # Check the full function AST to see what's generated
        print(f"\nGenerated blocks: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
        
        # Now check the full decompiled source
        from pycdc import decompile_pyc
        decomp_src = decompile_pyc(target_pyc)
        
        # Compile and check bytecode at offset 820
        decomp_code = compile(decomp_src, '<decompiled>', 'exec')
        decomp_func = find_function(decomp_code, 'get_multiminute_his_data')
        
        print("\nDecompiled bytecode around offset 810-830:")
        for instr in dis.get_instructions(decomp_func):
            if 810 <= instr.offset <= 830:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        
        print("\nOriginal bytecode around offset 810-830:")
        orig_instrs = list(dis.get_instructions(func_code))
        for instr in orig_instrs:
            if 810 <= instr.offset <= 830:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        
        # Find what's at offset 820 in the decompiled source
        # The offset 820 corresponds to the JUMP_FORWARD in the original
        # Let me check what's generated at that point
        print("\nDecompiled source around the problematic area:")
        lines = decomp_src.split('\n')
        in_func = False
        for i, line in enumerate(lines):
            if 'def get_multiminute_his_data' in line:
                in_func = True
            if in_func:
                if 'return his_data_dict' in line.lower() or 'if len(his_data_dict)' in line.lower():
                    # Print context around this line
                    for j in range(max(0, i-3), min(len(lines), i+5)):
                        print(f"  {j+1:4d}: {lines[j]}")
                    print("  ...")
        break
