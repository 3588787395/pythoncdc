"""Dump regions for a specific function to debug BoolOpRegion classification."""
import sys, types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()


def walk(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, sub_prefix, sink)
    return sink


cos = walk(code_obj)
target = sys.argv[1] if len(sys.argv) > 1 else 'load_bars_from_hundsun'
if target not in cos:
    print(f"NOT FOUND: {target}")
    sys.exit(1)

cfg = build_cfg(cos[target])
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
analyzer = gen.region_analyzer
regions = gen.regions

print(f"===== {target}: {len(regions)} regions =====")
for r in regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if r.entry else None
    blocks = sorted([b.start_offset for b in getattr(r, 'blocks', [])])
    merge = getattr(r, 'merge_block', None)
    merge_off = merge.start_offset if merge else None
    is_cond = getattr(r, 'is_condition_context', None)
    vt = getattr(r, 'value_target', None)
    rt = getattr(getattr(r, 'region_type', None), 'name', None)
    elif_conds = [b.start_offset for b in getattr(r, 'elif_conditions', [])] if hasattr(r, 'elif_conditions') else None
    then_b = sorted([b.start_offset for b in getattr(r, 'then_blocks', [])]) if hasattr(r, 'then_blocks') and getattr(r, 'then_blocks', None) else []
    else_b = sorted([b.start_offset for b in getattr(r, 'else_blocks', [])]) if hasattr(r, 'else_blocks') and getattr(r, 'else_blocks', None) else []
    cond_b = getattr(r, 'condition_block', None)
    cond_off = cond_b.start_offset if cond_b else None
    if rtype in ('IfRegion', 'BoolOpRegion'):
        print(f"  {rtype}@{entry} blocks={blocks} merge={merge_off} is_cond={is_cond} vt={vt!r} rtype={rt} elif={elif_conds}")
        print(f"    then_blocks={then_b} else_blocks={else_b} cond_block={cond_off}")
