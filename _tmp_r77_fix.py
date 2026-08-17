"""R77 fix: modify R67 STORE_ATTR fix to not mark merge_block as generated,
allowing the caller to process remaining instructions after STORE_ATTR."""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the R67 fix return statement and replace it with unmark + no return
old = """                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
            # [R68] BoolOp with STORE_SUBSCR target"""

new = """                        self._generated_regions.add(id(region))
                        # [R77] Don't return immediately - unmark merge_block
                        # so the caller can process remaining instructions
                        # (e.g. subsequent STORE_ATTR assignments in the same
                        # merge_block like trade._trading_dt = ...).
                        # The merge_block was marked at line ~23259; unmark it
                        # to allow _generate_block_statements to process the
                        # remaining instructions after STORE_ATTR.
                        self.generated_blocks.discard(region.merge_block)
                        if region.merge_block.start_offset in self.generated_offsets:
                            self.generated_offsets.discard(region.merge_block.start_offset)
                        # Skip the R68 STORE_SUBSCR check since we already
                        # handled this as a STORE_ATTR assignment.
                        _r67_handled = True
                    else:
                        _r67_handled = False
                else:
                    _r67_handled = False
            else:
                _r67_handled = False
            if not _r67_handled and False:  # R68 placeholder - always skip if R67 handled
                pass  # R68 check below will handle if R67 didn't
            # [R68] BoolOp with STORE_SUBSCR target"""

# Actually, let me use a simpler approach - just unmark and return
old_simple = """                        self._generated_regions.add(id(region))
                        return pre_stmts + results if pre_stmts else results
            # [R68] BoolOp with STORE_SUBSCR target"""

new_simple = """                        self._generated_regions.add(id(region))
                        # [R77] Unmark merge_block so remaining instructions
                        # (after STORE_ATTR) can be processed by the caller.
                        # This handles functions like trade.create_trade where
                        # the merge_block has multiple sequential assignments.
                        self.generated_blocks.discard(region.merge_block)
                        if hasattr(region.merge_block, 'start_offset') and region.merge_block.start_offset in self.generated_offsets:
                            self.generated_offsets.discard(region.merge_block.start_offset)
                        return pre_stmts + results if pre_stmts else results
            # [R68] BoolOp with STORE_SUBSCR target"""

if old_simple in content:
    content = content.replace(old_simple, new_simple, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R77 fix inserted")
else:
    print("FAILED: Could not find target text")
    # Try partial match
    idx = content.find("self._generated_regions.add(id(region))\n                        return pre_stmts + results if pre_stmts else results\n            # [R68]")
    if idx >= 0:
        print(f"Found at index {idx}")
    else:
        # Try another pattern
        idx2 = content.find("return pre_stmts + results if pre_stmts else results")
        if idx2 >= 0:
            print(f"Found 'return pre_stmts' at index {idx2}")
            print(f"Context: ...{content[idx2-100:idx2+100]}...")
