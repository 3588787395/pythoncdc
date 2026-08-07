with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The entry-match check should also verify condition_block == chain_block
# to avoid matching spurious IfRegions whose entry is a BoolOp jump block
# but whose condition_block is a different block.
old = """        for r in self.regions:
            if (isinstance(r, IfRegion)
                    and r.entry is chain_block
                    and getattr(r, 'chained_compare_ops', None)
                    and len(r.chained_compare_ops) >= 2
                    and getattr(r, 'chained_compare_blocks', None)):
                cc_expr = self._build_chained_compare_from_region_data(r)"""

new = """        for r in self.regions:
            if (isinstance(r, IfRegion)
                    and r.entry is chain_block
                    and getattr(r, 'chained_compare_ops', None)
                    and len(r.chained_compare_ops) >= 2
                    and getattr(r, 'chained_compare_blocks', None)
                    # [R36] Ensure condition_block matches chain_block to avoid
                    # matching spurious IfRegions whose entry is a BoolOp jump
                    # block but whose condition_block is a different block.
                    and r.condition_block is chain_block):
                cc_expr = self._build_chained_compare_from_region_data(r)"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix8 applied")
else:
    print("FAIL: old_string not found")
