"""R82 fix: add return-context chained compare support in _generate_value_context_chain_compare_assign."""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        if store_instr is None:
            return None
        target_name = store_instr.argval if store_instr.argval else f'var_{store_instr.arg}'
        # 用与 AssertRegion _build_assert_chained_compare 相同的算法重建链式 Compare
        chained_cond = self._build_assert_chained_compare(
            cond_block,
            list(region.chained_compare_blocks),
            list(region.chained_compare_ops),
        )"""

new = """        if store_instr is None:
            # [R82] Return-context chained compare (e.g. `return a <= b <= c`).
            # The merge_block has SWAP + POP_TOP + RETURN_VALUE instead of STORE_*.
            # Check if merge_block ends with RETURN_VALUE (no STORE_* means the
            # chained compare result is returned directly).
            _mb_instrs_r82 = [i for i in merge_block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _has_return_r82 = any(i.opname == 'RETURN_VALUE' for i in _mb_instrs_r82)
            _has_swap_r82 = any(i.opname == 'SWAP' for i in _mb_instrs_r82)
            if _has_return_r82 and _has_swap_r82:
                _chained_cond_r82 = self._build_assert_chained_compare(
                    cond_block,
                    list(region.chained_compare_blocks),
                    list(region.chained_compare_ops),
                )
                if _chained_cond_r82 is not None:
                    for block in region.blocks:
                        self.generated_blocks.add(block)
                    self.generated_blocks.add(merge_block)
                    self._generated_regions.add(id(region))
                    return {
                        'type': 'Return',
                        'value': _chained_cond_r82,
                    }
            return None
        target_name = store_instr.argval if store_instr.argval else f'var_{store_instr.arg}'
        # 用与 AssertRegion _build_assert_chained_compare 相同的算法重建链式 Compare
        chained_cond = self._build_assert_chained_compare(
            cond_block,
            list(region.chained_compare_blocks),
            list(region.chained_compare_ops),
        )"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R82 fix inserted")
else:
    print("FAILED: Could not find target text")
