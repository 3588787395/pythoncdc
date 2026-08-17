"""Insert R67 fix into region_ast_generator.py."""
import re

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The target line to insert before
target = "            if region.value_target or (getattr(region, 'is_augassign', False)\n                                       and getattr(region, 'augassign_target_kind', None) in ('attr', 'subscr')):\n                # AugAssign with BoolOp rhs"

# The new code to insert
new_code = """            # [R67] BoolOp with STORE_ATTR target (e.g. `obj.attr = a or b`).
            # When value_target is None but merge_block contains STORE_ATTR,
            # the BoolOp expression is the rhs of an attribute assignment.
            if (not region.value_target
                    and not getattr(region, 'is_augassign', False)
                    and region.merge_block is not None):
                _mb_r67 = [i for i in region.merge_block.instructions
                           if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _sa_r67 = None
                for _ii_r67, _mi_r67 in enumerate(_mb_r67):
                    if _mi_r67.opname == 'STORE_ATTR':
                        _sa_r67 = _ii_r67
                        break
                if _sa_r67 is not None and _sa_r67 > 0:
                    _obj_r67 = self.expr_reconstructor.reconstruct(_mb_r67[:_sa_r67])
                    _attr_r67 = _mb_r67[_sa_r67].argval
                    if _obj_r67 is not None and _attr_r67:
                        results.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Attribute',
                                'value': _obj_r67,
                                'attr': _attr_r67,
                                'ctx': 'Store',
                            }],
                            'value': boolop_expr,
                        })
                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
"""

# Check if target exists
if target in content:
    content = content.replace(target, new_code + target, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R67 fix inserted")
else:
    # Try to find a partial match
    idx = content.find("if region.value_target or (getattr(region, 'is_augassign', False)")
    if idx >= 0:
        # Find the start of the line (go back to the beginning of the line)
        line_start = content.rfind('\n', 0, idx) + 1
        # Insert before this line
        content = content[:line_start] + new_code + content[line_start:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS: R67 fix inserted at position {line_start}")
    else:
        print("FAILED: Could not find target text")
        # Show some context around where we expect it
        idx2 = content.find("AugAssign with BoolOp rhs")
        if idx2 >= 0:
            print(f"Found 'AugAssign with BoolOp rhs' at position {idx2}")
            print(f"Context: {content[idx2-200:idx2+200]}")
