"""Check final_integration_test TryExceptRegion details"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = 'decompiler_test_comprehensive.cpython-311.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'final_integration_test':
                func_code = cc
                break
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)

# Find TryExceptRegion
from core.cfg.region_ast_generator import TryExceptRegion
for r in gen.regions:
    if isinstance(r, TryExceptRegion):
        print(f"=== TryExceptRegion: entry={r.entry_block.start_offset} ===")
        print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        print(f"  finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
        print(f"  finally_copy_blocks: {list(r.finally_copy_blocks.keys())}")
        print(f"  handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
        for et, en, hbs in r.except_handlers:
            print(f"  handler: type={et}, name={en}, blocks={[b.start_offset for b in hbs]}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        
        # Check else_blocks successors
        if r.else_blocks:
            for eb in r.else_blocks:
                print(f"\n  else_block {eb.start_offset} successors:")
                for s in eb.successors:
                    print(f"    -> {s.start_offset}")
        
        # Check finally_copy_blocks successors
        for fc_off in r.finally_copy_blocks:
            fc_block = cfg.get_block_by_offset(fc_off)
            if fc_block:
                print(f"\n  finally_copy_block {fc_off} successors:")
                for s in fc_block.successors:
                    print(f"    -> {s.start_offset}")
        
        # Check _region_block_set
        _region_block_set = set(r.blocks)
        print(f"\n  region blocks (offsets): {[b.start_offset for b in r.blocks]}")
        
        # Check what block has RETURN_VALUE (return None)
        for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
            for instr in b.instructions:
                if instr.opname == 'RETURN_VALUE':
                    # Check if previous is LOAD_CONST None
                    idx = b.instructions.index(instr)
                    if idx > 0 and b.instructions[idx-1].opname == 'LOAD_CONST' and b.instructions[idx-1].argval is None:
                        print(f"\n  block {b.start_offset} has LOAD_CONST None + RETURN_VALUE")
        break
