"""Dump CFG blocks for handle_backtest_build to find where the f-string
gets split. The BUILD_STRING 25 chain spans bytes 1334-1456. We want to
see which basic block(s) those bytes fall into.
"""
import sys, marshal
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from core.cfg import build_cfg
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtest.pyc'
with open(PYC, 'rb') as f:
    f.read(16)
    top = marshal.load(f)
hb = next(c for c in top.co_consts if hasattr(c, 'co_code') and c.co_name == 'handle_backtest_build')

cfg = build_cfg(hb)
print(f'CFG name: {cfg.name}')
print(f'Total blocks: {len(cfg.blocks)}')
print(f'blocks type: {type(cfg.blocks)}')
# Inspect structure
if isinstance(cfg.blocks, dict):
    print('blocks keys (first 10):', list(cfg.blocks.keys())[:10])
    # values?
    sample_v = next(iter(cfg.blocks.values()))
    print('sample value type:', type(sample_v), 'attrs:', [a for a in dir(sample_v) if not a.startswith('_')][:20])
else:
    sample_v = cfg.blocks[0]
    print('sample block type:', type(sample_v), 'attrs:', [a for a in dir(sample_v) if not a.startswith('_')][:20])

# Find block(s) covering the f-string range 1334-1456
def covers(blk):
    if not hasattr(blk, 'instructions'):
        return False
    instrs = blk.instructions
    if not instrs:
        return False
    start = blk.start_offset
    end = instrs[-1].offset if hasattr(instrs[-1], 'offset') else start
    return start <= 1456 and end >= 1334

blocks_iter = cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks
for blk in blocks_iter:
    if not covers(blk):
        continue
    instrs = blk.instructions
    start = blk.start_offset
    end = instrs[-1].offset if hasattr(instrs[-1], 'offset') else start
    print(f'\n=== Block @ {start} (end~{end}, {len(instrs)} instrs) ===')
    for ins in instrs:
        if 1300 <= ins.offset <= 1470:
            argval = repr(ins.argval)[:50] if ins.argval is not None else ''
            print(f'  {ins.offset:5d} {ins.opname:30s} {ins.arg!s:5s} {argval}')
    preds = [p.start_offset for p in blk.predecessors] if hasattr(blk, 'predecessors') else []
    print(f'  predecessors: {preds}')
    succs = [s.start_offset for s in blk.successors] if hasattr(blk, 'successors') else []
    print(f'  successors: {succs}')
