#!/usr/bin/env python3
"""Fix: Add Starred target support for UNPACK_EX in entry block processing."""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "                                _entry_unpack_info['targets'].append({'type': 'Name', 'id': _instr.argval if _instr.argval else f'var_{_instr.arg}', 'ctx': 'Store'})"

new = """                                _tgt_name = _instr.argval if _instr.argval else f'var_{_instr.arg}'
                                _is_starred = _entry_unpack_info.get('is_starred', False)
                                _starred_idx = _entry_unpack_info.get('starred_idx', -1)
                                if _is_starred and len(_entry_unpack_info['targets']) == _starred_idx:
                                    _entry_unpack_info['targets'].append({'type': 'Starred', 'value': {'type': 'Name', 'id': _tgt_name, 'ctx': 'Store'}})
                                else:
                                    _entry_unpack_info['targets'].append({'type': 'Name', 'id': _tgt_name, 'ctx': 'Store'})"""

count = content.count(old)
print(f'Found {count} occurrences')
if count == 1:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Applied successfully')
elif count == 0:
    print('Not found or already applied')
else:
    print(f'ERROR: {count} occurrences')
