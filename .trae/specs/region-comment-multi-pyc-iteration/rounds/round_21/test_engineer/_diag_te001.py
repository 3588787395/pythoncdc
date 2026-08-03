"""R21 diag: trace region analysis + decompile for te001 (try-else continue)."""
import marshal, sys, types, os
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from pycdc import decompile_pyc

PYC = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros/__pycache__/te001_loop_continue.cpython-311.pyc'

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def main():
    code = load_pyc(PYC)
    # Find function f
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == 'f':
            func_code = c
            break
    else:
        print('No function f found')
        return

    print(f'== f varnames={func_code.co_varnames} ==')
    cfg = build_cfg(func_code)
    blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    print(f'--- blocks ({len(blocks)}) ---')
    for b in sorted(blocks, key=lambda x: x.start_offset):
        ops = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        succs = sorted(s.start_offset for s in b.successors)
        print(f'block@{b.start_offset:4d} end={b.end_offset:4d} succs={succs}: {ops}')

    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()
    print(f'\n--- regions ({len(regions)}) ---')
    for r in regions:
        rtype = type(r).__name__
        entry_off = getattr(r, 'entry', None) and getattr(r.entry, 'start_offset', None)
        blocks_off = [getattr(b, 'start_offset', None) for b in getattr(r, 'blocks', [])]
        print(f'{rtype} entry@{entry_off} blocks={blocks_off}')
        if hasattr(r, 'except_handlers'):
            for exc, name, hb in r.except_handlers:
                print(f'  handler exc={exc} name={name} blocks={[b.start_offset for b in hb]}')
            print(f'  try_offset_end={getattr(r, "try_offset_end", None)}')
            print(f'  has_else={getattr(r, "has_else", None)}')
            print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')

    # Decompile
    print(f'\n--- decompiled ---')
    dec = decompile_pyc(PYC)
    print(dec)


if __name__ == '__main__':
    main()
