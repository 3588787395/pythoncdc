"""Debug how block 20 is handled"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

for r in ra.regions:
    if hasattr(r, 'has_finally'):
        print(f"Region entry={r.entry.start_offset}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
        print(f"  try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  finally_blocks={[b.start_offset for b in r.finally_blocks]}")
        print(f"  finally_copy_blocks={r.finally_copy_blocks}")
        
        # block 20 is in region.blocks but not in any known part
        all_known = set()
        for b in r.try_blocks: all_known.add(b.start_offset)
        for b in r.else_blocks: all_known.add(b.start_offset)
        for b in r.finally_blocks: all_known.add(b.start_offset)
        for et, en, hbs in r.except_handlers:
            for b in hbs: all_known.add(b.start_offset)
        for b in r.handler_entry_blocks: all_known.add(b.start_offset)
        all_known.update(r.finally_copy_blocks.keys())
        
        for b in r.blocks:
            if b.start_offset not in all_known:
                print(f"  UNCLASSIFIED block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
                print(f"    role: {ra.get_block_role(b)}")
                print(f"    successors: {[s.start_offset for s in b.successors]}")
