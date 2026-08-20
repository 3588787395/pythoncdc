"""Check try_end_offset and handler entries for final_integration_test"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator, TryExceptRegion

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
gen.generate()  # This triggers region analysis

for r in gen.regions:
    if isinstance(r, TryExceptRegion):
        print(f"TryExceptRegion: entry={r.entry.start_offset}")
        print(f"  try_offset_end: {r.try_offset_end}")
        print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        print(f"  finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
        print(f"  handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"  finally_copy_blocks: {list(r.finally_copy_blocks.keys())}")
        print(f"  has_else: {r.has_else}")
        print(f"  has_finally: {r.has_finally}")
        
        # Check try_end_block
        teb = cfg.get_block_by_offset(r.try_offset_end) if r.try_offset_end else None
        if teb:
            print(f"\n  try_end_block {teb.start_offset}:")
            for i in teb.instructions:
                if i.opname not in ('NOP','CACHE','RESUME'):
                    print(f"    {i.offset}: {i.opname} {i.argval}")
            print(f"    successors: {[s.start_offset for s in teb.successors]}")
        
        # Check handler end blocks
        for et, en, hbs in r.except_handlers:
            for hb in hbs:
                last_i = hb.instructions[-1] if hb.instructions else None
                if last_i:
                    print(f"\n  handler_block {hb.start_offset} last: {last_i.opname} {last_i.argval}")
                    print(f"    successors: {[s.start_offset for s in hb.successors]}")
        break
