"""Debug repro_r2_07 - check block 148 membership"""
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
        try_set = set(b.start_offset for b in r.try_blocks)
        else_set = set(b.start_offset for b in r.else_blocks) if r.else_blocks else set()
        fin_set = set(b.start_offset for b in r.finally_blocks)
        h_set = set()
        for et, en, hbs in r.except_handlers:
            h_set.update(b.start_offset for b in hbs)
        he_set = set(b.start_offset for b in r.handler_entry_blocks)
        fc_keys = set(getattr(r, 'finally_copy_blocks', {}).keys())
        print(f"block 148 in try={148 in try_set}, else={148 in else_set}, fin={148 in fin_set}, handler={148 in h_set}, h_entry={148 in he_set}, fc_keys={148 in fc_keys}")
        for fc_o in fc_keys:
            fcb = cfg.get_block_by_offset(fc_o)
            if fcb:
                print(f"fc block {fc_o} succs: {[s.start_offset for s in fcb.successors]}")
