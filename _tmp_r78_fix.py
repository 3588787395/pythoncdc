"""R78 fix: process remaining merge_block instructions after STORE_ATTR
by temporarily replacing block instructions and calling _generate_block_statements."""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the R77 fix code and replace it with R78 approach
old = """                        self._generated_regions.add(id(region))
                        # [R77] Unmark merge_block so remaining instructions
                        # (after STORE_ATTR) can be processed by the caller.
                        # This handles functions like trade.create_trade where
                        # the merge_block has multiple sequential assignments.
                        self.generated_blocks.discard(region.merge_block)
                        if hasattr(region.merge_block, 'start_offset') and region.merge_block.start_offset in self.generated_offsets:
                            self.generated_offsets.discard(region.merge_block.start_offset)
                        return pre_stmts + results if pre_stmts else results"""

new = """                        self._generated_regions.add(id(region))
                        # [R78] Process remaining instructions after STORE_ATTR
                        # by temporarily replacing merge_block instructions
                        # and calling _generate_block_statements.
                        _orig_instrs_r78 = region.merge_block.instructions
                        _store_instr_r78 = _mb_r67[_sa_r67]
                        _store_idx_r78 = _orig_instrs_r78.index(_store_instr_r78)
                        _remaining_r78 = _orig_instrs_r78[_store_idx_r78 + 1:]
                        if _remaining_r78:
                            # Temporarily replace instructions with remaining ones
                            region.merge_block.instructions = _remaining_r78
                            self.generated_blocks.discard(region.merge_block)
                            if hasattr(region.merge_block, 'start_offset') and region.merge_block.start_offset in self.generated_offsets:
                                self.generated_offsets.discard(region.merge_block.start_offset)
                            _remaining_stmts_r78 = self._generate_block_statements(region.merge_block)
                            if _remaining_stmts_r78:
                                results.extend(_remaining_stmts_r78)
                            # Restore and re-mark
                            region.merge_block.instructions = _orig_instrs_r78
                            self.generated_blocks.add(region.merge_block)
                        return pre_stmts + results if pre_stmts else results"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R78 fix inserted")
else:
    print("FAILED: Could not find R77 target text")
    # Try partial match
    idx = content.find("[R77] Unmark merge_block")
    if idx >= 0:
        print(f"Found R77 text at index {idx}")
        print(f"Context: ...{content[idx-50:idx+300]}...")
