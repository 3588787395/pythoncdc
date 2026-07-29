"""R23-N10: 验证load_get_exrights的merge_block生成触发情况"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r: return r
    return None

co = find(code_obj, 'load_get_exrights')
print(f"Found: {co.co_name}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(co)

analyzer = RegionAnalyzer(cfg, co)
analyzer.analyze()

target_if = None
target_loop = None
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 830:
        target_if = r
    if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 996:
        target_loop = r

print(f"\nTarget IfRegion: entry={target_if.entry.start_offset if target_if else None}")
print(f"  merge_block={target_if.merge_block.start_offset if target_if and target_if.merge_block else None}")
print(f"  then_blocks={[b.start_offset for b in target_if.then_blocks] if target_if else []}")
print(f"  else_blocks={[b.start_offset for b in target_if.else_blocks] if target_if and target_if.else_blocks else []}")
print(f"  elif_conditions={[b.start_offset for b in target_if.elif_conditions] if target_if and hasattr(target_if, 'elif_conditions') and target_if.elif_conditions else []}")

print(f"\nTarget LoopRegion: entry={target_loop.entry.start_offset if target_loop else None}")
print(f"  else_blocks={[b.start_offset for b in target_loop.else_blocks] if target_loop else []}")
print(f"  blocks={[b.start_offset for b in target_loop.blocks] if target_loop else []}")

print("\n=== R18-N5 触发条件检查 ===")
if target_if and target_loop and target_if.merge_block:
    mb = target_if.merge_block
    cond1 = mb is not None
    cond2 = mb not in target_if.then_blocks
    cond3 = mb not in (target_if.else_blocks or [])
    print(f"  1. merge_block not None: {cond1}")
    print(f"  2. merge_block not in then_blocks: {cond2}")
    print(f"  3. merge_block not in else_blocks: {cond3}")

    _mb_in_nested_structural = False
    for _nr in analyzer.regions:
        if _nr is target_if:
            continue
        if not isinstance(_nr, (TryExceptRegion, WithRegion, MatchRegion)):
            continue
        if mb in _nr.blocks:
            _mb_in_nested_structural = True
            break
    print(f"  4. merge_block in nested structural region: {_mb_in_nested_structural}")

    _should_emit = False
    if not _mb_in_nested_structural:
        _then_block_set = set(target_if.then_blocks)
        _else_block_set = set(target_if.else_blocks or [])
        for _lr in analyzer.regions:
            if not isinstance(_lr, LoopRegion):
                continue
            if _lr is target_if:
                continue
            if mb not in _lr.else_blocks:
                continue
            if _lr.entry is not None and (_lr.entry in _then_block_set or _lr.entry in _else_block_set):
                _should_emit = True
                print(f"  -> matched LoopRegion entry={_lr.entry.start_offset}")
                break
    print(f"  5. _should_emit: {_should_emit}")

    print(f"\n  merge_block.start_offset: {mb.start_offset}")
    print(f"  LoopRegion.entry: {target_loop.entry}")
    print(f"  LoopRegion.entry in else_blocks: {target_loop.entry in (target_if.else_blocks or [])}")
    print(f"  LoopRegion.entry in then_blocks: {target_loop.entry in (target_if.then_blocks or [])}")
