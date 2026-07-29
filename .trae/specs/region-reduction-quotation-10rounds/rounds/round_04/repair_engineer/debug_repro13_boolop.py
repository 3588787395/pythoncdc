"""Debug BoolOp detection for repro_13 pattern."""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

# Compile repro_13
import py_compile
import os

REPRO = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_04/test_engineer/minimal_repros/repro_13_one_prod_elif_3_branches.py'

# Compile to pyc
pyc_path = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_04/repair_engineer/repro13.pyc'
py_compile.compile(REPRO, pyc_path, doraise=True)

# Load the code object
import marshal
with open(pyc_path, 'rb') as f:
    f.read(16)  # skip header
    code = marshal.load(f)

# Find the function
def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_func(const, name)
            if result:
                return result
    return None

func_code = find_func(code, 'one_prod_minimal')
if not func_code:
    print("ERROR: could not find one_prod_minimal")
    sys.exit(1)

print(f"Found function: {func_code.co_name}")
print(f"\n=== Disassembly ===")
dis.dis(func_code)

# Build CFG and analyze
cfg = build_cfg(func_code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== REGIONS ===")
for i, region in enumerate(analyzer.regions):
    rtype = region.region_type
    entry = region.entry.start_offset if region.entry else None
    blocks = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    print(f"  [{i}] {rtype} entry={entry} blocks={blocks}")

print(f"\n=== block_to_region ===")
for blk, reg in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    rentry = reg.entry.start_offset if reg.entry else None
    print(f"  blk@{blk.start_offset} -> {reg.region_type} (entry={rentry})")

# Check BoolOp detection for each block
print(f"\n=== BoolOp chain detection (with empty claimed) ===")
all_blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for blk in sorted(all_blocks, key=lambda b: b.start_offset):
    last = blk.get_last_instruction()
    if not last:
        continue
    if last.opname not in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                           'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
                           'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
        continue
    # Try detecting a boolop chain
    try:
        chain = analyzer._detect_boolop_conditional_chain(blk, set())
    except Exception as e:
        chain = None
        print(f"  blk@{blk.start_offset}: EXCEPTION {e}")
    if chain:
        print(f"  blk@{blk.start_offset}: chain={[(b.start_offset, op) for b, op in chain]}")
    else:
        # Check if it has body stmts
        has_body = any(
            i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                        'STORE_ATTR', 'STORE_SUBSCR', 'BINARY_OP', 'CALL')
            for i in blk.instructions
            if i.offset < last.offset and i.opname not in ('CACHE', 'EXTENDED_ARG', 'NOP', 'RESUME')
        )
        print(f"  blk@{blk.start_offset}: no chain (has_body={has_body}, last={last.opname} {last.argval})")
