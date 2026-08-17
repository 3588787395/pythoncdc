"""Insert R68 STORE_SUBSCR fix into region_ast_generator.py."""
filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the R67 fix code and add STORE_SUBSCR handling after it
target = """                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
            if region.value_target or"""

new_code = """                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
            # [R68] BoolOp with STORE_SUBSCR target (e.g. `d['k'] = a or b`).
            # When value_target is None but merge_block contains STORE_SUBSCR,
            # the BoolOp expression is the rhs of a subscript assignment.
            if (not region.value_target
                    and not getattr(region, 'is_augassign', False)
                    and region.merge_block is not None):
                _ss_r68 = None
                for _ii_r68, _mi_r68 in enumerate(_mb_r67):
                    if _mi_r68.opname == 'STORE_SUBSCR':
                        _ss_r68 = _ii_r68
                        break
                if _ss_r68 is not None and _ss_r68 >= 2:
                    _key_instrs_r68 = [_mb_r67[_ss_r68 - 1]]
                    _obj_instrs_r68 = _mb_r67[:_ss_r68 - 1]
                    _obj_expr_r68 = self.expr_reconstructor.reconstruct(_obj_instrs_r68)
                    _key_expr_r68 = self.expr_reconstructor.reconstruct(_key_instrs_r68)
                    if _obj_expr_r68 is not None and _key_expr_r68 is not None:
                        results.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Subscript',
                                'value': _obj_expr_r68,
                                'slice': _key_expr_r68,
                                'ctx': 'Store',
                            }],
                            'value': boolop_expr,
                        })
                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
            if region.value_target or"""

if target in content:
    content = content.replace(target, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R68 STORE_SUBSCR fix inserted")
else:
    print("FAILED: Could not find target text")
    # Try partial match
    idx = content.find("self._generated_regions.add(id(region))\n                        return pre_stmts + results if pre_stmts else results\n            if region.value_target or")
    if idx >= 0:
        content = content[:idx] + new_code.split("                        self._generated_regions.add(id(region))\n                        return pre_stmts + results if pre_stmts else results\n")[0] + new_code + content[idx+len("                        self._generated_regions.add(id(region))\n                        return pre_stmts + results if pre_stmts else results\n            if region.value_target or"):]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS (partial match): R68 fix inserted")
    else:
        print("Could not find target")
