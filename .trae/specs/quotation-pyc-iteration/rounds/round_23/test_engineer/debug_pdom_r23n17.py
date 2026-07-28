"""R23-N17: 调试 get_index_stocks 的后支配树"""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for co in code_obj.co_consts:
    if isinstance(co, types.CodeType) and co.co_name == 'get_index_stocks':
        target = co
        break

cfg = build_cfg(target)
dom = DominatorAnalyzer(cfg)
dom.analyze()

blocks = {b.start_offset: b for b in cfg.blocks.values()}

# Check post-dominators of key blocks
for off in [0, 6, 8, 76, 124, 126, 128, 146, 198, 202, 204, 210, 286, 316, 352]:
    if off not in blocks:
        continue
    b = blocks[off]
    pdoms = sorted(p.start_offset for p in b.post_dominators)
    ipdom = b.immediate_post_dominator.start_offset if b.immediate_post_dominator else None
    print(f"  @{off:4d} ipdom={ipdom} pdoms={pdoms}")

# Check NCPD of @6 and @210
print(f"\nNCPD(@6, @210) = {dom.find_nearest_common_post_dominator_two(blocks[6], blocks[210])}")
if dom.find_nearest_common_post_dominator_two(blocks[6], blocks[210]):
    print(f"  offset = {dom.find_nearest_common_post_dominator_two(blocks[6], blocks[210]).start_offset}")

# Check NCPD of @6 and @286
ncpd = dom.find_nearest_common_post_dominator_two(blocks[6], blocks[286])
print(f"NCPD(@6, @286) = {ncpd.start_offset if ncpd else None}")

# Check predecessors of @286 and @316
for off in [286, 316, 352]:
    b = blocks[off]
    print(f"\n  @{off} predecessors={[p.start_offset for p in b.predecessors]}")
    print(f"  @{off} successors={[s.start_offset for s in b.successors]}")
