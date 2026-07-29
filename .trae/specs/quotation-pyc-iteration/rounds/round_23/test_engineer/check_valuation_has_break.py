"""R24-N1 调试：检查 valuation 的 LoopRegion has_break 属性"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_func(const, name)
            if result:
                return result
    return None

val_co = find_func(code_obj, 'valuation')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(val_co)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

for r in analyzer.regions:
    if r.__class__.__name__ == 'LoopRegion' and r.entry and r.entry.start_offset == 520:
        print(f"LoopRegion@520:")
        print(f"  has_break: {getattr(r, 'has_break', 'NOT SET')}")
        print(f"  break_blocks: {[b.start_offset for b in getattr(r, 'break_blocks', [])]}")
        print(f"  body_blocks: {sorted(b.start_offset for b in r.body_blocks)}")
        print(f"  else_blocks: {sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else 'None'}")
        print(f"  children: {[(c.__class__.__name__, c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")
        # Check each child
        for c in (r.children or []):
            if c.__class__.__name__ == 'TryExceptRegion':
                print(f"\n  Child TryExceptRegion@{c.entry.start_offset}:")
                print(f"    blocks: {sorted(b.start_offset for b in c.blocks)}")
                print(f"    entry in else_blocks: {c.entry in r.else_blocks if r.else_blocks else False}")
                print(f"    entry in body_blocks: {c.entry in r.body_blocks if r.body_blocks else False}")
        break
