#!/usr/bin/env python
"""R36 fix: Skip value-context chained compare IfRegions in _try_collect_c3."""

import sys

filepath = 'core/cfg/region_ast_generator.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    "            def _try_collect_c3(child):\n"
    "                if not hasattr(child, 'entry') or child.entry is None:\n"
    "                    return False\n"
    "                if child.entry in self.generated_blocks:\n"
    "                    return False\n"
    "                if child.entry in _claimed_blocks_c3:\n"
    "                    return False\n"
)

new = (
    "            def _try_collect_c3(child):\n"
    "                if not hasattr(child, 'entry') or child.entry is None:\n"
    "                    return False\n"
    "                if child.entry in self.generated_blocks:\n"
    "                    return False\n"
    "                if child.entry in _claimed_blocks_c3:\n"
    "                    return False\n"
    "                # [R36 fix] Skip value-context chained compare IfRegions.\n"
    "                # These have chained_compare_ops, condition_block ending with\n"
    "                # SHORT_CIRCUIT_JUMP_OPS, and merge_block NOT ending with\n"
    "                # FORWARD_CONDITIONAL_JUMP_OPS. They are value expressions\n"
    "                # (BoolOp operands, return values), not if statements.\n"
    "                # Collecting them would cause the caller to mark their blocks\n"
    "                # as generated, preventing BoolOpRegion from processing them.\n"
    "                if (isinstance(child, IfRegion)\n"
    "                        and getattr(child, 'chained_compare_ops', None)\n"
    "                        and len(child.chained_compare_ops) >= 2\n"
    "                        and getattr(child, 'chained_compare_blocks', None)):\n"
    "                    _cb = getattr(child, 'condition_block', None)\n"
    "                    if _cb is not None:\n"
    "                        _cb_last = _cb.get_last_instruction()\n"
    "                        if _cb_last and _cb_last.opname in SHORT_CIRCUIT_JUMP_OPS:\n"
    "                            _mb = getattr(child, 'merge_block', None)\n"
    "                            if _mb is not None:\n"
    "                                _mb_last = _mb.get_last_instruction()\n"
    "                                if (_mb_last and _mb_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS):\n"
    "                                    return False\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
