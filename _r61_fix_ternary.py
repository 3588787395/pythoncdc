#!/usr/bin/env python3
"""R61: Add STORE_SUBSCR/STORE_ATTR handling in _generate_ternary condition block"""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add STORE_SUBSCR/STORE_ATTR handling after the STORE_FAST/STORE_NAME/etc handler
# and before the load_instrs backward scan
old = """                    load_instrs = []
                    j = i - 1
                    while j >= cond_start_idx:
                        if cond_instrs[j].opname.startswith('LOAD_'):
                            load_instrs.insert(0, cond_instrs[j])
                            j -= 1
                        else:
                            break

                    if load_instrs:
                        val_expr = self.expr_reconstructor.reconstruct(load_instrs)
                        if val_expr:
                            pre_stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': instr.argval, 'ctx': 'Store'}],
                                'value': val_expr,
                            })
                        cond_start_idx = i + 1
                    else:"""

new = """                    # [R61 fix] Handle STORE_SUBSCR/STORE_ATTR in condition block
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

                    load_instrs = []
                    j = i - 1
                    while j >= cond_start_idx:
                        if cond_instrs[j].opname.startswith('LOAD_'):
                            load_instrs.insert(0, cond_instrs[j])
                            j -= 1
                        else:
                            break

                    if load_instrs:
                        val_expr = self.expr_reconstructor.reconstruct(load_instrs)
                        if val_expr:
                            pre_stmts.append({
                                'type': 'Assign',
                                'targets': [{'type': 'Name', 'id': instr.argval, 'ctx': 'Store'}],
                                'value': val_expr,
                            })
                        cond_start_idx = i + 1
                    else:"""

if old not in content:
    print("ERROR: old text not found!")
    # Try to find a smaller unique substring
    idx = content.find("load_instrs = []\n                    j = i - 1\n                    while j >= cond_start_idx:")
    if idx >= 0:
        print(f"Found at index {idx}")
        print(f"Context: {repr(content[idx-50:idx+100])}")
    exit(1)

content = content.replace(old, new, 1)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! STORE_SUBSCR/STORE_ATTR handling added to _generate_ternary.")
