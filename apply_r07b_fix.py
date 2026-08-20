#!/usr/bin/env python3
"""Round 7b fix: Don't mark RETURN blocks as break targets when inside try-except.

Root cause: In _detect_break_continue, block@406 (return False) is marked as
a break target because:
1. It contains RETURN_VALUE
2. Source block@366 doesn't end with JUMP_FORWARD
3. Block@406 has no meaningful instructions (only LOAD_CONST + RETURN_VALUE)
4. There IS an exception handler (block@610), but loop header@72 dominates block@406

The fix: When _has_exc_handler is True, the block is inside a try-except,
so return is a real return statement, not a break. Don't mark it as break.
"""

import shutil

file_path = "core/cfg/region_analyzer.py"
shutil.copy2(file_path, file_path + ".r07b_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                                if not s_meaningful:
                                    if not _has_exc_handler or self.dom_analyzer.is_dominator(header, s):
                                        break_blocks_set.add(s)
                                else:
                                    if not _has_exc_handler:
                                        break_blocks_set.add(s)"""

new_code = """                                if not s_meaningful:
                                    # [Round 7b fix] When _has_exc_handler is True,
                                    # the block is inside a try-except. A return
                                    # statement inside try-except is a real return,
                                    # not a break. Don't mark it as break target.
                                    if not _has_exc_handler:
                                        break_blocks_set.add(s)
                                else:
                                    if not _has_exc_handler:
                                        break_blocks_set.add(s)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Round 7b fix applied!")
else:
    print("ERROR: Target not found!")