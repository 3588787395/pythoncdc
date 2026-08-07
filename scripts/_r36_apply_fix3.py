with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        _vc_assign = self._generate_value_context_chain_compare_assign(region)
        if _vc_assign is not None:
            return _vc_assign"""

new = """        _vc_assign = self._generate_value_context_chain_compare_assign(region)
        if _vc_assign is not None:
            return _vc_assign
        # [R36] Value-context chained compare as BoolOp operand (e.g.
        # `return A < x < B or C < x < D`). The IfRegion has
        # chained_compare_ops, condition_block ends with SHORT_CIRCUIT_JUMP_OPS,
        # but merge_block has no STORE_* (instead it has JUMP_IF_TRUE_OR_POP
        # or JUMP_IF_FALSE_OR_POP — the BoolOp short-circuit). Without this
        # check, _if_generate_normal creates `if A < x < B: pass`, consuming
        # blocks that belong to the BoolOpRegion. Fix: detect this pattern,
        # cache the chained compare expression for the BoolOp generator, mark
        # blocks as generated, and return [] to skip IfRegion generation.
        if (getattr(region, 'chained_compare_ops', None)
                and len(region.chained_compare_ops) >= 2
                and getattr(region, 'chained_compare_blocks', None)):
            _cond_block = region.condition_block
            if _cond_block is not None:
                _cb_last = _cond_block.get_last_instruction()
                if _cb_last and _cb_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                    _merge = getattr(region, 'merge_block', None)
                    if _merge is not None:
                        _merge_last = _merge.get_last_instruction()
                        if (_merge_last and _merge_last.opname in SHORT_CIRCUIT_JUMP_OPS
                                and _merge_last.opname not in ('JUMP_FORWARD',)):
                            # merge_block is a BoolOp short-circuit jump block
                            _cc_expr = self._build_chained_compare_from_region_data(region)
                            if _cc_expr is not None:
                                if not hasattr(self, '_chain_compare_expr_cache'):
                                    self._chain_compare_expr_cache = {}
                                self._chain_compare_expr_cache[id(_merge)] = _cc_expr
                                for b in region.blocks:
                                    self.generated_blocks.add(b)
                                self._generated_regions.add(id(region))
                                return []"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix3 applied")
else:
    print("FAIL: old_string not found")
