#!/usr/bin/env python
"""Remove debug print from _generate_if."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "        if region.entry is not None:\n"
    "            _entry_owner = self.region_analyzer.block_to_region.get(region.entry)\n"
    "            import os as _os_dbg2\n"
    "            if _os_dbg2.environ.get('R36_DEBUG_STT'):\n"
    "                import sys as _sys_dbg2\n"
    "                _e_off = region.entry.start_offset\n"
    "                _o_type = type(_entry_owner).__name__ if _entry_owner else None\n"
    "                _o_entry = _entry_owner.entry.start_offset if _entry_owner and hasattr(_entry_owner, 'entry') and _entry_owner.entry else None\n"
    "                _is_boolop = isinstance(_entry_owner, BoolOpRegion)\n"
    "                _is_self = _entry_owner is region\n"
    "                print(f' [R36_DEBUG] IfRegion@{_e_off}: owner={_o_type}@{_o_entry} is_boolop={_is_boolop} is_self={_is_self}', file=_sys_dbg2.stderr)\n"
    "            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:\n"
)

new = (
    "        if region.entry is not None:\n"
    "            _entry_owner = self.region_analyzer.block_to_region.get(region.entry)\n"
    "            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: debug removed')
else:
    print('ERROR: old string not found')
    sys.exit(1)
