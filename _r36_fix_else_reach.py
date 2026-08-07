#!/usr/bin/env python
"""R36 fix: _try_collect_c3 should also check if child.entry is directly in blocks."""

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
    "                if not self._is_child_reachable_from_blocks(child, region.else_blocks):\n"
    "                    return False\n"
    "                _reachable_children_c3.append(child)\n"
)

new = (
    "            def _try_collect_c3(child):\n"
    "                if not hasattr(child, 'entry') or child.entry is None:\n"
    "                    return False\n"
    "                if child.entry in self.generated_blocks:\n"
    "                    return False\n"
    "                if child.entry in _claimed_blocks_c3:\n"
    "                    return False\n"
    "                # [R36 fix] child.entry may be directly in else_blocks\n"
    "                # (not just reachable via successors). This happens when\n"
    "                # the else branch starts with a for-loop (GET_ITER block).\n"
    "                # The for-loop's entry block has no predecessor in else_blocks\n"
    "                # (it's reached from the if condition's false branch), so\n"
    "                # _is_child_reachable_from_blocks returns False.\n"
    "                _entry_in_else = child.entry in set(region.else_blocks)\n"
    "                if not _entry_in_else and not self._is_child_reachable_from_blocks(child, region.else_blocks):\n"
    "                    return False\n"
    "                _reachable_children_c3.append(child)\n"
)

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: replaced successfully')
else:
    print('ERROR: old string not found')
    sys.exit(1)
