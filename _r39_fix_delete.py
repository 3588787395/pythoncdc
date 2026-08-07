import os

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 31242 (0-indexed: 31241) is:
# "                        _eff_expr_instrs.append(_instr)\n"
# We need to insert DELETE_SUBSCR/DELETE_ATTR handling BEFORE this line
# and AFTER the STORE handling block (which ends at line 31241 with "continue\n")

# Verify we're at the right position
assert '_eff_expr_instrs.append(_instr)' in lines[31241], f"Line mismatch: {repr(lines[31241])}"
assert 'continue' in lines[31240], f"Line mismatch: {repr(lines[31240])}"

# Insert the DELETE_SUBSCR/DELETE_ATTR handling before _eff_expr_instrs.append(_instr)
delete_handling = (
    "                        # [R39 fix] DELETE_SUBSCR/DELETE_ATTR -> Delete stmt.\n"
    "                        # del obj.attr / del container[key] in CONTINUE blocks\n"
    "                        # had DELETE_* dropped and LOAD preds emitted as Expr.\n"
    "                        if _instr.opname in ('DELETE_SUBSCR', 'DELETE_ATTR') and _eff_expr_instrs:\n"
    "                            _del_stmt = self._build_delete_stmt(_instr, _eff_expr_instrs + [_instr])\n"
    "                            if _del_stmt:\n"
    "                                if isinstance(_del_stmt, list):\n"
    "                                    _eff_stmts.extend(_del_stmt)\n"
    "                                else:\n"
    "                                    _eff_stmts.append(_del_stmt)\n"
    "                            _eff_expr_instrs = []\n"
    "                            continue\n"
)

lines.insert(31241, delete_handling)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done! Inserted DELETE_SUBSCR/DELETE_ATTR handling at line 31242")
