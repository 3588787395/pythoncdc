#!/usr/bin/env python3
"""R61: Revert ternary changes that caused regressions"""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert change 3: Remove STORE_SUBSCR/STORE_ATTR from condition check
old3 = """                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                   'STORE_SUBSCR', 'STORE_ATTR'):"""
new3 = """                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):"""

if old3 not in content:
    print("ERROR: old3 not found!")
else:
    content = content.replace(old3, new3, 1)
    print("Step 1: Reverted STORE_SUBSCR/STORE_ATTR from condition check")

# Revert change 4: Remove the STORE_SUBSCR/STORE_ATTR handler block
old4 = """                    # [R61 fix] Handle STORE_SUBSCR/STORE_ATTR in condition block
                    # as pre-statements (e.g. `new_kwargs[key] = [price, amount]`
                    # before a ternary condition). The backward LOAD_* scan below
                    # only works for simple Name targets; Subscript/Attribute
                    # targets need full instruction reconstruction.
                    if instr.opname in ('STORE_SUBSCR', 'STORE_ATTR'):
                        _pred_instrs = list(cond_instrs[cond_start_idx:i + 1])
                        _pred_stmts = self._build_statements_from_instructions(
                            _pred_instrs)
                        if _pred_stmts:
                            pre_stmts.extend(_pred_stmts)
                        cond_start_idx = i + 1
                        i += 1
                        continue

                    load_instrs = []"""
new4 = """                    load_instrs = []"""

if old4 not in content:
    print("ERROR: old4 not found!")
else:
    content = content.replace(old4, new4, 1)
    print("Step 2: Reverted STORE_SUBSCR/STORE_ATTR handler block")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Ternary changes reverted.")
