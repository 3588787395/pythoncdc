#!/usr/bin/env python3
"""Debug: monkeypatch to log boundary_stop and _collect_branch_blocks for repro_01."""
import sys, types, os, py_compile, tempfile
sys.path.insert(0, os.path.abspath('.'))
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TryExceptRegion

REPRO = sys.argv[1] if len(sys.argv) > 1 else r'f:\Downloads\pythoncdc-main\.trae\specs\region-comment-multi-pyc-iteration\rounds\round_04\test_engineer\minimal_repros\repro_01_pattern_a_or_cond_try_elif_collapse.py'

tmpdir = tempfile.mkdtemp(prefix='r04_dbg2_')
pyc = os.path.join(tmpdir, 'r01_c.pyc')
py_compile.compile(REPRO, pyc, doraise=True, quiet=2)

m = load_pyc_file_v2(pyc)
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

def find(co, n):
    if co.co_name == n:
        return co
    for k in co.co_consts:
        if isinstance(k, types.CodeType):
            r = find(k, n)
            if r:
                return r
    return None

f = find(c, 'f')
cfg = build_cfg(f)

# Monkeypatch _collect_branch_blocks to log calls involving blocks 38/76
_orig_collect = RegionAnalyzer._collect_branch_blocks
_log = []
def _patched_collect(self, entry, merge, stop_set=None):
    entry_off = entry.start_offset if hasattr(entry, 'start_offset') else entry
    merge_off = merge.start_offset if hasattr(merge, 'start_offset') else merge
    stop_offs = sorted([s.start_offset for s in (stop_set or ()) if hasattr(s, 'start_offset')])
    result = _orig_collect(self, entry, merge, stop_set)
    result_offs = [b.start_offset for b in result]
    # only log if involves blocks 38 or 76
    relevant = {38, 76}
    if entry_off in relevant or merge_off in relevant or any(s in relevant for s in stop_offs) or any(r in relevant for r in result_offs):
        _log.append(f"  _collect_branch_blocks(entry={entry_off}, merge={merge_off}, stop={stop_offs}) -> {result_offs}")
    return result
RegionAnalyzer._collect_branch_blocks = _patched_collect

# Monkeypatch get_if_branch_boundary_stop on TryExceptRegion
_orig_get_boundary = TryExceptRegion.get_if_branch_boundary_stop
def _patched_get_boundary(self, block):
    block_off = block.start_offset if hasattr(block, 'start_offset') else block
    result = _orig_get_boundary(self, block)
    result_offs = sorted([s.start_offset for s in result])
    try_offs = sorted([b.start_offset for b in self.try_blocks])
    else_offs = sorted([b.start_offset for b in self.else_blocks])
    print(f"  TryExceptRegion@{self.entry.start_offset}.get_if_branch_boundary_stop(block={block_off}): try_blocks={try_offs} else_blocks={else_offs} -> boundary={result_offs}")
    return result
TryExceptRegion.get_if_branch_boundary_stop = _patched_get_boundary

# Monkeypatch _build_elif_region to log boundary_stop
_orig_build_elif = RegionAnalyzer._build_elif_region
def _patched_build_elif(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boundary_stop=None, ternary_regions=None, main_inline_boolop_chain=None):
    block_off = block.start_offset
    bs_offs = sorted([s.start_offset for s in (boundary_stop or ())])
    merge_off = merge.start_offset if merge else None
    cond_off = condition_block.start_offset if condition_block else None
    br = self.block_to_region.get(block)
    br_str = type(br).__name__ + f"@{br.entry.start_offset}" if (br and getattr(br, 'entry', None)) else (type(br).__name__ if br else "None")
    print(f"  _build_elif_region(block={block_off}, cond={cond_off}, merge={merge_off}, boundary_stop={bs_offs}, block_region={br_str})")
    return _orig_build_elif(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boundary_stop, ternary_regions, main_inline_boolop_chain)
RegionAnalyzer._build_elif_region = _patched_build_elif

analyzer = RegionAnalyzer(cfg)
print("=== Running analyze() with monkeypatches ===")
regions = analyzer.analyze()

print(f"\n=== _collect_branch_blocks calls involving 38/76 ===")
for line in _log:
    print(line)

print(f"\n=== Final IfRegion elif_final_else ===")
for r in regions:
    if isinstance(r, IfRegion):
        print(f"  IfRegion@{r.entry.start_offset} elif_final_else={[b.start_offset for b in r.elif_final_else]}")
