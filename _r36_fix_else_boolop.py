#!/usr/bin/env python3
"""Apply R36 fix-2: claim blocks and collect BoolOpRegion in else branch."""

import re

FILE = r"f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: In _try_collect_c3, when skipping value-context chained compare,
# claim the blocks so they are not processed as sequential blocks.
old1 = "                                if (_mb_last and _mb_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS):\n                                    return False\n                # [R36 fix] child.entry may be directly in else_blocks"

new1 = "                                if (_mb_last and _mb_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS):\n                                    for b in child.blocks:\n                                        _child_block_set_c3.add(b)\n                                        _claimed_blocks_c3.add(b)\n                                    return False\n                # [R36 fix] child.entry may be directly in else_blocks"

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix 1 applied: claim blocks when skipping value-context chained compare")
else:
    print("ERROR: Fix 1 old string not found!")
    # Try to find it
    idx = content.find("_mb_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS")
    if idx >= 0:
        print(f"  Found at offset {idx}, context:")
        print(f"  ...{content[idx-100:idx+100]}...")

# Fix 2: Add third phase to collect BoolOpRegion/TernaryRegion children in else branch
old2 = "                _try_collect_c3(child)\n            _entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}"

new2 = "                _try_collect_c3(child)\n            # [R36 fix-2] Third phase: BoolOpRegion / TernaryRegion children.\n            # Value-expression regions in the else branch (e.g. `return\n            # (a < b < c) or (d < e < f)`) are not collected by phases 1/2.\n            # Without this, their blocks are processed as sequential blocks,\n            # producing garbage statements. Collecting them allows\n            # _generate_region -> _generate_boolop to properly rebuild the\n            # expression (including _try_build_chained_compare_in_boolop).\n            for child in (region.children or []):\n                if not isinstance(child, (BoolOpRegion, TernaryRegion)):\n                    continue\n                _try_collect_c3(child)\n            _entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}"

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix 2 applied: collect BoolOpRegion/TernaryRegion in else branch")
else:
    print("ERROR: Fix 2 old string not found!")
    # Try to find similar patterns
    count = content.count("_try_collect_c3(child)\n            _entry_to_child_c3")
    print(f"  Pattern count: {count}")
    idx = content.find("_entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}")
    if idx >= 0:
        print(f"  Found _entry_to_child_c3 at offset {idx}")
        print(f"  Context before:")
        start = max(0, idx - 200)
        print(f"  ...{content[start:idx]}...")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone.")
