# -*- coding: utf-8 -*-
"""R8 probe: step through _parse_exception_table stages."""
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

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

entries = list(cfg.exception_table)
result = []
seen = set()
for entry in entries:
    entry_start = entry.get('start', 0)
    entry_end = entry.get('end', 0)
    entry_target = entry.get('target', 0)
    entry_depth = entry.get('depth', 0)
    handler_block = cfg.get_block_by_offset(entry_target)
    if handler_block is None or not handler_block.instructions:
        print('SKIP no block for target', entry_target)
        continue
    handler_type = analyzer._classify_handler_type(handler_block, entry_target, entry_depth)
    if handler_type is None:
        handler_type = analyzer._classify_handler_with_cleanup(handler_block, entry_target, entry_depth)
    if handler_type is None:
        print('SKIP unclassified target', entry_target)
        continue
    actual = analyzer._find_actual_handler_start(handler_block, entry_target, handler_type, entry_depth)
    is_cleanup_only = (
        handler_block.instructions[0].opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
        and any(i.opname == 'COPY' for i in handler_block.instructions)
        and any(i.opname == 'POP_EXCEPT' for i in handler_block.instructions)
        and any(i.opname == 'RERAISE' for i in handler_block.instructions)
    )
    key = (entry_start, entry_end, actual)
    dup = key in seen
    seen.add(key)
    print('RAW [%s,%s) tgt=%s d=%s -> actual=%s type=%s cleanup_only=%s dup=%s' % (
        entry_start, entry_end, entry_target, entry_depth, actual, handler_type, is_cleanup_only, dup))
    if dup:
        continue
    result.append({'try_start': entry_start, 'try_end': entry_end, 'handler_start': actual,
                   'handler_type': handler_type, 'depth': entry_depth})

print('--- after stage1 ---')
for r in result:
    print('   ', r)

merged = {}
for entry in result:
    key = (entry['handler_start'], entry['handler_type'])
    if key in merged:
        existing = merged[key]
        if entry['try_start'] >= existing['handler_start']:
            handler_block = cfg.get_block_by_offset(existing['handler_start'])
            if handler_block:
                handler_already_in_range = any(
                    existing['try_start'] <= i.offset < existing['try_end']
                    for i in handler_block.instructions)
                if not handler_already_in_range:
                    print('MERGE-SKIP', existing, entry)
                    continue
            else:
                continue
        existing['try_start'] = min(existing['try_start'], entry['try_start'])
        existing['try_end'] = max(existing['try_end'], entry['try_end'])
        existing['depth'] = min(existing['depth'], entry['depth'])
    else:
        merged[key] = entry.copy()
result = list(merged.values())
print('--- after merge ---')
for r in result:
    print('   ', r)

all_raw_entries = cfg.exception_table
changed = True
while changed:
    changed = False
    for entry in result:
        handler_start = entry['handler_start']
        for raw_entry in all_raw_entries:
            raw_target = raw_entry.get('target', 0)
            raw_start = raw_entry.get('start', 0)
            raw_end = raw_entry.get('end', 0)
            if entry['try_start'] <= raw_target < handler_start:
                if raw_start < entry['try_start']:
                    entry['try_start'] = raw_start
                    changed = True
                if raw_end > entry['try_end'] and raw_end <= handler_start:
                    if raw_start < entry['try_end']:
                        entry['try_end'] = raw_end
                        changed = True
print('--- after expansion ---')
for r in result:
    print('   ', r)
