"""R19 测试工程师：检查 check_frequency 的 IfRegion merge_block"""
import sys

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'

for target_name in ['check_frequency', 'api_get']:
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == target_name:
            target = const
            break

    builder = CFGBuilder()
    cfg = builder.build(target)
    ra = RegionAnalyzer(cfg)
    ra.analyze()

    print(f'=== {target_name} IfRegions ===')
    for r in ra.regions:
        if isinstance(r, IfRegion):
            print(f'  IfRegion: blocks={sorted([b.start_offset for b in r.blocks])}, entry={r.entry.start_offset if r.entry else None}')
            print(f'    merge_block: {r.merge_block.start_offset if r.merge_block else None}')
            print(f'    then_blocks: {[b.start_offset for b in r.then_blocks]}')
            print(f'    else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}')

    # Find TryExceptRegion
    for r in ra.regions:
        if isinstance(r, TryExceptRegion):
            print(f'  TryExceptRegion: entry={r.entry.start_offset if r.entry else None}, parent={type(r.parent).__name__ if r.parent else None}')
            if r.parent and isinstance(r.parent, IfRegion):
                print(f'    parent IfRegion merge_block: {r.parent.merge_block.start_offset if r.parent.merge_block else None}')
    print()
