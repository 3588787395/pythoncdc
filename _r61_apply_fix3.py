#!/usr/bin/env python3
"""R61: Apply chained assignment fix to region_ast_generator.py"""
import re

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Insert chained assignment detection before _full_rhs = boolop_expr
# The exact text to find (with indentation):
old1 = """                    _full_rhs = boolop_expr
                    if region.merge_block:
                        _mnn = [i for i in region.merge_block.instructions
                                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _si = None
                        for _ki, _instr in enumerate(_mnn):
                            if _instr.opname in ('STORE_FAST', 'STORE_NAME',
                                                 'STORE_GLOBAL', 'STORE_DEREF'):
                                _si = _ki
                                break
                        # Expression continuation = instructions before STORE"""

new1 = """                    # [R61 fix] Chained assignment detection: COPY + multiple
                    # STORE_* in merge_block. Pattern: `base_price = price = expr`
                    # generates `COPY 1; STORE_FAST price; STORE_FAST base_price`.
                    # The COPY duplicates the boolop result for the second store
                    # target. Collect all STORE targets and create a multi-target
                    # Assign, skipping expression continuation splicing (COPY is
                    # not an expression op) and post-store processing.
                    _chained_targets_r61 = None
                    if region.merge_block:
                        _mnn_r61 = [i for i in region.merge_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _STORE_TYPES_R61 = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                        if (len(_mnn_r61) >= 3
                                and _mnn_r61[0].opname == 'COPY'
                                and _mnn_r61[1].opname in _STORE_TYPES_R61
                                and _mnn_r61[2].opname in _STORE_TYPES_R61):
                            _chained_targets_r61 = []
                            for _ci in _mnn_r61[1:]:
                                if _ci.opname in _STORE_TYPES_R61:
                                    _chained_targets_r61.append(
                                        {'type': 'Name', 'id': _ci.argval, 'ctx': 'Store'})
                                else:
                                    break
                    _full_rhs = boolop_expr
                    if region.merge_block and not _chained_targets_r61:
                        _mnn = [i for i in region.merge_block.instructions
                                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _si = None
                        for _ki, _instr in enumerate(_mnn):
                            if _instr.opname in ('STORE_FAST', 'STORE_NAME',
                                                 'STORE_GLOBAL', 'STORE_DEREF'):
                                _si = _ki
                                break
                        # Expression continuation = instructions before STORE"""

if old1 not in content:
    print("ERROR: old1 not found!")
    # Try to find what's there
    idx = content.find("_full_rhs = boolop_expr")
    if idx >= 0:
        print(f"Found _full_rhs at index {idx}")
        print(f"Context: {repr(content[idx-20:idx+100])}")
    exit(1)

content = content.replace(old1, new1, 1)
print("Step 1: Inserted chained assignment detection")

# 2. Modify the Assign creation to use chained targets when available
old2 = """                    results.append({
                        'type': 'Assign',
                        'targets': [{'type': 'Name', 'id': region.value_target, 'ctx': 'Store'}],
                        'value': _full_rhs,
                    })
                if region.merge_block:"""

new2 = """                    if _chained_targets_r61:
                        results.append({
                            'type': 'Assign',
                            'targets': _chained_targets_r61,
                            'value': boolop_expr,
                        })
                    else:
                        results.append({
                            'type': 'Assign',
                            'targets': [{'type': 'Name', 'id': region.value_target, 'ctx': 'Store'}],
                            'value': _full_rhs,
                        })
                if region.merge_block and not _chained_targets_r61:"""

if old2 not in content:
    print("ERROR: old2 not found!")
    idx = content.find("'type': 'Assign',\n                        'targets': [{'type': 'Name', 'id': region.value_target")
    if idx >= 0:
        print(f"Found Assign at index {idx}")
        print(f"Context: {repr(content[idx-20:idx+200])}")
    exit(1)

content = content.replace(old2, new2, 1)
print("Step 2: Modified Assign creation for chained targets")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! File saved.")
