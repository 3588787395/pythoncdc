import re

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "                    return cc_expr\n                return None\n        return None\n\n    def _try_build_nested_ternary_in_boolop(self, chain_block, region):"

new = """                    return cc_expr
                return None
        # [R36] When chain_block has no value load (just a short-circuit jump
        # like JUMP_IF_TRUE_OR_POP), it may be the merge_block of a preceding
        # chained compare IfRegion. This happens in patterns like:
        #   return A < x < B or C < x < D
        # where the first chained compare has merge_block = the `or` jump block.
        # The BoolOp chain starts at the `or` block because the chained compare
        # entry is skipped by value_chain_cmp_if_entries guard. Without this
        # check, the first operand of `or` is lost.
        for r in self.regions:
            if (isinstance(r, IfRegion)
                    and getattr(r, 'merge_block', None) is chain_block
                    and getattr(r, 'chained_compare_ops', None)
                    and len(r.chained_compare_ops) >= 2
                    and getattr(r, 'chained_compare_blocks', None)):
                cc_expr = self._build_chained_compare_from_region_data(r)
                if cc_expr is not None:
                    for b in r.blocks:
                        self.generated_blocks.add(b)
                    return cc_expr
                return None
        return None

    def _try_build_nested_ternary_in_boolop(self, chain_block, region):"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Edit applied")
else:
    print("FAIL: old_string not found")
    # Try to find what's actually there
    idx = content.find("return cc_expr\n                return None\n        return None\n\n    def _try_build_nested_ternary_in_boolop")
    if idx >= 0:
        print(f"Found at index {idx}")
        print(repr(content[idx:idx+200]))
    else:
        print("Pattern not found at all")
        # Search for the function definition
        idx2 = content.find("def _try_build_nested_ternary_in_boolop")
        if idx2 >= 0:
            print(f"Found function at index {idx2}")
            print(repr(content[idx2-100:idx2+50]))
