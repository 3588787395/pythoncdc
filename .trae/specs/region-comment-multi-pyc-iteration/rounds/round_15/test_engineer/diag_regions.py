"""R15 diagnostic: dump regions for get_trading_schedule to understand the inner-loop-in-then-block pattern."""
import sys
import os
import marshal
import types
from pathlib import Path

ROOT = Path(__file__).resolve()
while ROOT.name and not (ROOT / 'pycdc.py').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from pycdc import decompile_pyc
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = str(ROOT / 'site-packages/IQCommon/trade_schedule.pyc')


def load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract(code, out=None):
    if out is None:
        out = {}
    out[code.co_name or '<module>'] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            extract(c, out)
    return out


def main():
    code = load_pyc_code(PYC)
    cmap = extract(code)
    fn = cmap['get_trading_schedule']
    print(f'=== get_trading_schedule co_code bytes={len(fn.co_code)} ===')

    builder = CFGBuilder()
    cfg = builder.build(fn)
    print(f'CFG blocks: {len(cfg.blocks)}')
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        succ_offs = sorted([s.start_offset for s in b.successors])
        pred_offs = sorted([p.start_offset for p in b.predecessors])
        print(f'  block@{b.start_offset} end={b.end_offset} succ={succ_offs} '
              f'pred={pred_offs} instrs={len(b.instructions)}')
        for ins in b.instructions:
            print(f'    {ins.offset:4d} {ins.opname:30s} {ins.argval if ins.argval is not None else ""}')

    print()
    print('=== Regions ===')
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    for r in analyzer.regions:
        blocks_list = [b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else []
        then_bl = [b.start_offset for b in r.then_blocks] if hasattr(r, 'then_blocks') and r.then_blocks else []
        else_bl = [b.start_offset for b in r.else_blocks] if hasattr(r, 'else_blocks') and r.else_blocks else []
        entry = r.entry.start_offset if hasattr(r, 'entry') and r.entry else None
        merge = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
        print(f'  {r.region_type} entry={entry} merge={merge} '
              f'then={then_bl} else={else_bl} blocks={blocks_list}')


if __name__ == '__main__':
    main()
