# -*- coding: utf-8 -*-
"""R8 probe: dump TryExceptRegion structure after analyze()."""
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2] if len(sys.argv) > 2 else None

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = code
if fname:
    found = None
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == fname:
            found = c
            break
    if found is None:
        print('NOT FOUND')
        sys.exit(1)
    target = found

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()


def offs(blocks):
    if blocks is None:
        return None
    if isinstance(blocks, dict):
        return sorted(blocks.keys())
    out = []
    for b in blocks:
        out.append(b.start_offset if hasattr(b, 'start_offset') else b)
    return sorted(out)


print('=== TryExceptRegions ===')
for r in analyzer.regions:
    if not isinstance(r, TryExceptRegion):
        continue
    print('REG entry=%s try=[%s,%s) has_finally=%s has_else=%s' % (
        r.entry.start_offset if r.entry else None,
        getattr(r, 'try_offset_start', None), getattr(r, 'try_offset_end', None),
        getattr(r, 'has_finally', None), getattr(r, 'has_else', None)))
    print('   blocks=%s' % offs(r.blocks))
    print('   try_blocks=%s' % offs(getattr(r, 'try_blocks', None)))
    print('   handler_entry_blocks=%s' % offs(getattr(r, 'handler_entry_blocks', None)))
    print('   finally_blocks=%s' % offs(getattr(r, 'finally_blocks', None)))
    print('   else_blocks=%s' % offs(getattr(r, 'else_blocks', None)))
    print('   cleanup_blocks=%s' % offs(getattr(r, 'cleanup_blocks', None)))
    print('   finally_copy_blocks=%s' % offs(getattr(r, 'finally_copy_blocks', None)))
    for eh in (getattr(r, 'except_handlers', None) or []):
        print('   handler: type=%r body=%s' % (eh[0], offs(eh[2] if len(eh) > 2 else None)))
    print('   parent=%s children=%s enclosing=%s' % (
        type(r.parent).__name__ if r.parent else None,
        [c.entry.start_offset if c.entry else None for c in (getattr(r, 'children', None) or [])],
        type(getattr(r, 'enclosing_try', None)).__name__ if getattr(r, 'enclosing_try', None) else None))
