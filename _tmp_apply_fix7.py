#!/usr/bin/env python3
"""Fix _find_loop_else: don't advance post_else past a break target that has real statements.
Only advance if the break target is a trivial jump block (single JUMP_FORWARD)."""

filepath = 'core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                if post_else and post_else in break_targets and len(break_targets) == 1:
                    for succ in post_else.successors:
                        if succ not in body_set:
                            post_else = succ
                            break"""

new = """                if post_else and post_else in break_targets and len(break_targets) == 1:
                    # Only advance post_else past the break target if it's a trivial
                    # jump block (single JUMP_FORWARD/JUMP_ABSOLUTE). If the break
                    # target has real statements (e.g., `counter = 0`), it is the
                    # first block AFTER the for-else, not part of the else block.
                    _bt_meaningful = [i for i in post_else.instructions
                                      if i.opname not in ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME')]
                    if (len(_bt_meaningful) == 1
                            and _bt_meaningful[0].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')):
                        for succ in post_else.successors:
                            if succ not in body_set:
                                post_else = succ
                                break"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
