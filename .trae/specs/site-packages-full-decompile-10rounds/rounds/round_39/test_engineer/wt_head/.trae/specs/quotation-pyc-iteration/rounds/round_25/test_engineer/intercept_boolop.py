"""R25: Intercept BoolOpRegion creation during analyze() for share_change"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'share_change':
        target = const
        break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)

analyzer = RegionAnalyzer(cfg)

# Monkey-patch _create_boolop_region_from_chain to log
original_create = analyzer._create_boolop_region_from_chain
def patched_create(chain, claimed):
    chain_desc = [(b.start_offset, op) for b, op in chain]
    result = original_create(chain, claimed)
    print(f"[INTERCEPT] _create_boolop_region_from_chain(chain={chain_desc}) -> {type(result).__name__ if result else None}")
    if result:
        print(f"  entry={result.entry.start_offset} merge={result.merge_block.start_offset if result.merge_block else None} blocks={[b.start_offset for b in result.blocks]}")
    return result
analyzer._create_boolop_region_from_chain = patched_create

# Also intercept _detect_boolop_chain_start
original_start = analyzer._detect_boolop_chain_start
def patched_start(block, claimed):
    result = original_start(block, claimed)
    if result:
        print(f"[INTERCEPT] _detect_boolop_chain_start(block={block.start_offset}) -> {[(b.start_offset, op) for b, op in result]}")
    return result
analyzer._detect_boolop_chain_start = patched_start

# Also intercept _detect_boolop_conditional_chain
original_cond = analyzer._detect_boolop_conditional_chain
def patched_cond(start_block, claimed, skip_claimed_check=False):
    result = original_cond(start_block, claimed, skip_claimed_check=skip_claimed_check)
    print(f"[INTERCEPT] _detect_boolop_conditional_chain(start={start_block.start_offset}, skip_claimed={skip_claimed_check}) -> {[(b.start_offset, op) for b, op in result] if result else None}")
    return result
analyzer._detect_boolop_conditional_chain = patched_cond

analyzer.analyze()

print(f"\n=== Final BoolOpRegions ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print(f"  entry={r.entry.start_offset} chain={[(b.start_offset, op) for b, op in r.op_chain]} merge={r.merge_block.start_offset if r.merge_block else None}")
