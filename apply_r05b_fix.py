#!/usr/bin/env python3
"""Fix 5b: prevent condition negation in elif chain handling for POP_JUMP_IF_FALSE"""

import shutil

file_path = "core/cfg/region_ast_generator.py"
shutil.copy2(file_path, file_path + ".r05b_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The problem: at line 6951, _negate is True when 'IF_TRUE' is in opname
# But for POP_JUMP_IF_FALSE, _negate should be False (condition is already correct)
# When POP_JUMP_IF_FALSE jumps to else, the fall-through is the then branch
# No negation needed.

old_code = """        _negate = 'IF_TRUE' in _jt_last.opname or 'IF_NONE' in _jt_last.opname
        _elif_cond = _negate_expr(_elif_expr) if _negate else _elif_expr"""

new_code = """        _is_elif_if_false = 'IF_FALSE' in _jt_last.opname
        if _is_elif_if_false:
            _negate = False
        else:
            _negate = 'IF_TRUE' in _jt_last.opname or 'IF_NONE' in _jt_last.opname
        _elif_cond = _negate_expr(_elif_expr) if _negate else _elif_expr"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix 5b applied: elif condition negation for IF_FALSE")
else:
    print("ERROR: Fix 5b target not found!")
    # Search for similar patterns
    import re
    matches = [(m.start(), m.group()) for m in re.finditer(r"_negate.*IF_TRUE.*opname", content)]
    for pos, match in matches[:5]:
        print(f"  Found at pos {pos}: {match[:80]}")