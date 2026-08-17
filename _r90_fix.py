#!/usr/bin/env python3
"""Fix: Add UNPACK_SEQUENCE handling to generate() entry block inline loop."""
import re

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add _entry_unpack_info variable initialization
old1 = '                    _import_pending_store = False\n\n                    for _instr in entry_block.instructions:'
new1 = '                    _import_pending_store = False\n                    _entry_unpack_info = None\n\n                    for _instr in entry_block.instructions:'

count1 = content.count(old1)
print(f'Step 1: Found {count1} occurrences of target text')
if count1 == 1:
    content = content.replace(old1, new1)
    print('Step 1: Applied')
elif count1 == 0:
    print('Step 1: Already applied or not found, checking...')
    if '_entry_unpack_info' in content:
        print('Step 1: _entry_unpack_info already exists')
    else:
        print('Step 1: ERROR - text not found')
else:
    print(f'Step 1: ERROR - {count1} occurrences, expected 1')

# Step 2: Add UNPACK_SEQUENCE handling before the STORE_FAST handling in the entry block loop
# We need to find the right location: after IMPORT_FROM handling and before STORE_FAST handling
# in the entry block inline loop (not in _if_extract_cond_instructions)

# The entry block loop has this pattern:
#                        if _instr.opname == 'IMPORT_FROM':
#                            _import_pending_store = True
#                            continue
#                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
#                            if _import_pending_store:

# We need to add UNPACK_SEQUENCE handling between IMPORT_FROM and STORE_FAST

old2 = """                        if _instr.opname == 'IMPORT_FROM':
                            _import_pending_store = True
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if _import_pending_store:
                                _stmt_instrs = []
                                _import_pending_store = False
                                continue
                            _stmt_instrs.append(_instr)"""

new2 = """                        if _instr.opname == 'IMPORT_FROM':
                            _import_pending_store = True
                            continue
                        if _instr.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
                            _val_instrs = [i for i in _stmt_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                            _val = self.expr_reconstructor.reconstruct(_val_instrs) if _val_instrs else None
                            if _instr.opname == 'UNPACK_SEQUENCE':
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _instr.arg}
                            else:
                                _arg = _instr.argval
                                _before, _after = _arg & 0xFF, (_arg >> 8) & 0xFF
                                _entry_unpack_info = {'value': _val, 'targets': [], 'count': _before + 1 + after, 'is_starred': True, 'starred_idx': _before}
                            _stmt_instrs = []
                            continue
                        if _instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if _import_pending_store:
                                _stmt_instrs = []
                                _import_pending_store = False
                                continue
                            if _entry_unpack_info is not None:
                                _entry_unpack_info['targets'].append({'type': 'Name', 'id': _instr.argval if _instr.argval else f'var_{_instr.arg}', 'ctx': 'Store'})
                                if len(_entry_unpack_info['targets']) == _entry_unpack_info['count']:
                                    _target = {'type': 'Tuple', 'elts': _entry_unpack_info['targets'], 'ctx': 'Store'}
                                    if _entry_unpack_info['value']:
                                        _pre_stmts.append({'type': 'Assign', 'targets': [_target], 'value': _entry_unpack_info['value']})
                                    _entry_unpack_info = None
                                _stmt_instrs = []
                                continue
                            _stmt_instrs.append(_instr)"""

count2 = content.count(old2)
print(f'Step 2: Found {count2} occurrences of target text')
if count2 == 1:
    content = content.replace(old2, new2)
    print('Step 2: Applied')
elif count2 == 0:
    print('Step 2: Not found, trying alternate search...')
    # Check if it's already been modified
    if '_entry_unpack_info' in content and 'UNPACK_SEQUENCE' in content[content.find('_entry_unpack_info'):content.find('_entry_unpack_info')+500]:
        print('Step 2: Already applied')
    else:
        print('Step 2: ERROR - text not found')
else:
    print(f'Step 2: ERROR - {count2} occurrences, expected 1')

with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
