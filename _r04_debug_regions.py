#!/usr/bin/env python3
"""Debug: dump region structure for repro_01 (Pattern A: or cond + elif + try -> full collapse)."""
import sys, types, os, py_compile, tempfile
sys.path.insert(0, os.path.abspath('.'))
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TryExceptRegion

REPRO = sys.argv[1] if len(sys.argv) > 1 else r'f:\Downloads\pythoncdc-main\.trae\specs\region-comment-multi-pyc-iteration\rounds\round_04\test_engineer\minimal_repros\repro_01_pattern_a_or_cond_try_elif_collapse.py'

# compile to pyc
tmpdir = tempfile.mkdtemp(prefix='r04_dbg_')
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
print(f"=== found code object: {f.co_name} ===")

cfg = build_cfg(f)
print(f"=== CFG blocks (by start_offset) ===")
_all_blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for blk in sorted(_all_blocks, key=lambda b: b.start_offset):
    last = blk.get_last_instruction() if hasattr(blk, 'get_last_instruction') else None
    last_str = f"{last.opname}->{last.argval}" if last else "None"
    first_meaningful = None
    for ins in blk.instructions:
        if ins.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
            first_meaningful = ins
            break
    fm_str = f"{first_meaningful.offset}:{first_meaningful.opname}({first_meaningful.argval})" if first_meaningful else "?"
    print(f"  blk@{blk.start_offset:5d} .. end={last_str:40s} first={fm_str}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\n=== {len(regions)} regions ===")
for r in regions:
    entry_off = r.entry.start_offset if getattr(r, 'entry', None) else None
    cond_off = r.condition_block.start_offset if getattr(r, 'condition_block', None) else None
    rtype = type(r).__name__
    rt_name = getattr(getattr(r, 'region_type', None), 'name', '')
    then_offs = [b.start_offset for b in (getattr(r, 'then_blocks', None) or [])]
    else_offs = [b.start_offset for b in (getattr(r, 'else_blocks', None) or [])]
    blocks_offs = [b.start_offset for b in (getattr(r, 'blocks', None) or [])]
    merge_off = getattr(r, 'merge_block', None)
    merge_off = merge_off.start_offset if merge_off else None
    print(f"  {rtype}({rt_name}) entry={entry_off} cond={cond_off} merge={merge_off}")
    print(f"     blocks={blocks_offs}")
    if then_offs:
        print(f"     then_blocks={then_offs}")
    if else_offs:
        print(f"     else_blocks={else_offs}")
    if hasattr(r, 'elif_conditions'):
        elc = [b.start_offset for b in (getattr(r, 'elif_conditions', None) or [])]
        elb = [[b.start_offset for b in body] for body in (getattr(r, 'elif_bodies', None) or [])]
        elf = [b.start_offset for b in (getattr(r, 'elif_final_else', None) or [])]
        if elc:
            print(f"     elif_conditions={elc}")
        if elb:
            print(f"     elif_bodies={elb}")
        if elf:
            print(f"     elif_final_else={elf}")
    if isinstance(r, TryExceptRegion):
        try_body = [b.start_offset for b in (getattr(r, 'try_blocks', None) or [])]
        handlers = getattr(r, 'handlers', None) or getattr(r, 'except_handlers', None) or []
        print(f"     try_blocks={try_body}")
        for hi, h in enumerate(handlers):
            if isinstance(h, tuple):
                hblocks = [b.start_offset for b in (h[2] if len(h) > 2 else [])]
            else:
                hblocks = [b.start_offset for b in (getattr(h, 'handler_blocks', None) or [])]
            print(f"     handler[{hi}] blocks={hblocks}")

print(f"\n=== block_to_region ownership ===")
b2r = getattr(analyzer, 'block_to_region', {})
for blk in sorted(_all_blocks, key=lambda b: b.start_offset):
    owner = b2r.get(blk)
    owner_str = type(owner).__name__ + f"@{owner.entry.start_offset}" if (owner and getattr(owner, 'entry', None)) else (type(owner).__name__ if owner else "None")
    print(f"  blk@{blk.start_offset:5d}: owner={owner_str}")

print(f"\n=== TryExceptRegion check ===")
try_regions = [r for r in regions if isinstance(r, TryExceptRegion)]
print(f"  TryExceptRegion count: {len(try_regions)}")
if_regions = [r for r in regions if isinstance(r, IfRegion)]
print(f"  IfRegion count: {len(if_regions)}")
boolop_regions = [r for r in regions if isinstance(r, BoolOpRegion)]
print(f"  BoolOpRegion count: {len(boolop_regions)}")
