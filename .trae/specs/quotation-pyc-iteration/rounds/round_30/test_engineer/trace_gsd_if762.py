"""Trace IfRegion creation for get_str_data block 762."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg import region_analyzer as ra_mod

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'get_str_data':
            return c
    return None


# Monkey-patch to trace
_orig_build_basic = ra_mod.RegionAnalyzer._build_basic_if_region
_orig_identify = ra_mod.RegionAnalyzer._identify_conditional_regions
_orig_ncpd = ra_mod.RegionAnalyzer._find_nearest_common_post_dominator
_orig_collect = ra_mod.RegionAnalyzer._collect_branch_blocks
_orig_jt_merge = ra_mod.RegionAnalyzer._compute_merge_from_jump_targets
_orig_role = ra_mod.RegionAnalyzer.get_block_role


def _traced_ncpd(self, a, b):
    result = _orig_ncpd(self, a, b)
    if a is not None and b is not None:
        ao = a.start_offset if hasattr(a, 'start_offset') else a
        bo = b.start_offset if hasattr(b, 'start_offset') else b
        if ao in (762, 788, 832, 836, 838, 844) or bo in (762, 788, 832, 836, 838, 844):
            print(f"[NCPD] ({ao}, {bo}) = {result.start_offset if result is not None else None}")
    return result


def _traced_jt_merge(self, block, then_succ, else_succ):
    result = _orig_jt_merge(self, block, then_succ, else_succ)
    bo = block.start_offset
    if bo == 762:
        print(f"[JT_MERGE] block={bo} then={then_succ.start_offset} else={else_succ.start_offset} = {result.start_offset if result is not None else None}")
    return result


def _traced_role(self, block):
    result = _orig_role(self, block)
    if block.start_offset in (788, 832, 836, 838, 844):
        print(f"[ROLE] block={block.start_offset} = {result}")
    return result


def _traced_collect(self, start, merge, stop_blocks=None):
    result = _orig_collect(self, start, merge, stop_blocks)
    if hasattr(start, 'start_offset') and start.start_offset in (788, 838):
        so = start.start_offset
        mo = merge.start_offset if merge is not None and hasattr(merge, 'start_offset') else merge
        sto = sorted([s.start_offset for s in stop_blocks]) if stop_blocks else []
        print(f"[COLLECT] start={so} merge={mo} stop={sto} = {[b.start_offset for b in result]}")
    return result


def _traced_build_basic(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boolop_regions=None, ternary_regions=None):
    bo = block.start_offset
    if bo == 762:
        print(f"[BUILD_BASIC] block={bo}")
        print(f"  then_blocks={[b.start_offset for b in then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in else_blocks]}")
        print(f"  merge={merge.start_offset if merge is not None else None}")
    return _orig_build_basic(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boolop_regions, ternary_regions)


ra_mod.RegionAnalyzer._find_nearest_common_post_dominator = _traced_ncpd
ra_mod.RegionAnalyzer._compute_merge_from_jump_targets = _traced_jt_merge
ra_mod.RegionAnalyzer.get_block_role = _traced_role
ra_mod.RegionAnalyzer._collect_branch_blocks = _traced_collect
ra_mod.RegionAnalyzer._build_basic_if_region = _traced_build_basic


def main():
    co = load_code(PYC)
    cfg = build_cfg(co)
    ra = ra_mod.RegionAnalyzer(cfg)
    ra.analyze()
    print()
    print("=== Final regions (loop + if-related) ===")
    for r in ra.regions:
        if hasattr(r, 'entry_block') or hasattr(r, 'condition_block'):
            entry = getattr(r, 'entry_block', None) or getattr(r, 'condition_block', None) or getattr(r, 'header_block', None)
            eo = entry.start_offset if entry is not None else None
            if eo in (762, 788, 832, 836, 838, 844, 760, 610):
                rtype = getattr(r, 'region_type', type(r).__name__)
                then_blks = [b.start_offset for b in getattr(r, 'then_blocks', [])]
                else_blks = [b.start_offset for b in getattr(r, 'else_blocks', [])]
                merge_blk = getattr(r, 'merge_block', None)
                merge_off = merge_blk.start_offset if merge_blk is not None else None
                body_blks = [b.start_offset for b in getattr(r, 'body_blocks', [])]
                break_blks = [b.start_offset for b in getattr(r, 'break_blocks', [])]
                all_blks = [b.start_offset for b in getattr(r, 'blocks', [])]
                print(f"  region type={rtype} entry={eo}")
                print(f"    body={body_blks}")
                print(f"    blocks={all_blks}")
                print(f"    then={then_blks} else={else_blks} merge={merge_off}")
                print(f"    break_blocks={break_blks}")


if __name__ == '__main__':
    main()
