#!/usr/bin/env python
"""R36 fix: unify BoolOpRegion sorting with other regions by entry offset."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    '        sorted_other = sorted(other_regions, key=lambda r: r.entry.start_offset if r.entry else 0)\r\n'
    '        top_level_regions = boolop_regions + sorted_other\r\n'
)
new = (
    '        # [R36 fix] BoolOpRegion sorted by entry offset with other regions,\r\n'
    '        # instead of being hardcoded at the front, to avoid return statements\r\n'
        '        # appearing before preceding assignment statements.\r\n'
    '        all_regions = boolop_regions + other_regions\r\n'
    '        top_level_regions = sorted(all_regions, key=lambda r: r.entry.start_offset if r.entry else 0)\r\n'
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    # Try without \r\n
    old2 = old.replace('\r\n', '\n')
    new2 = new.replace('\r\n', '\n')
    if old2 in content:
        content = content.replace(old2, new2)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print('OK: replaced (LF mode)')
    else:
        print('ERROR: old string not found')
        sys.exit(1)
