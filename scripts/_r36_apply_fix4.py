with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        _is_outer_condition = False
        _enclosing = region.find_enclosing_parent((LoopRegion, IfRegion))
        if _enclosing and hasattr(_enclosing, 'condition_block') and _enclosing.condition_block:
            if region.prefix_block and region.prefix_block == _enclosing.condition_block:
                _is_outer_condition = True
            if not _is_outer_condition:
                for chain_block, _ in region.op_chain:
                    if chain_block == _enclosing.condition_block:
                        _is_outer_condition = True
                        break"""

new = """        _is_outer_condition = False
        _enclosing = region.find_enclosing_parent((LoopRegion, IfRegion))
        if _enclosing and hasattr(_enclosing, 'condition_block') and _enclosing.condition_block:
            if region.prefix_block and region.prefix_block == _enclosing.condition_block:
                _is_outer_condition = True
            if not _is_outer_condition:
                for chain_block, _ in region.op_chain:
                    if chain_block == _enclosing.condition_block:
                        _is_outer_condition = True
                        break
            # [R36] If the BoolOp's merge_block (or its successor) ends with
            # RETURN_VALUE, the BoolOp is a standalone return expression,
            # not an outer condition. This happens when a value-context
            # chained compare is an operand of `or`/`and` in a return statement
            # (e.g. `return A < x < B or C < x < D`). The enclosing IfRegion
            # is a spurious artifact of the chained compare detection whose
            # blocks overlap with the BoolOpRegion.
            if _is_outer_condition and region.merge_block:
                _mb_last = region.merge_block.get_last_instruction()
                _mb_is_return = (_mb_last and _mb_last.opname in ('RETURN_VALUE', 'RETURN_CONST'))
                if not _mb_is_return:
                    for _ms in region.merge_block.successors:
                        _ms_last = _ms.get_last_instruction()
                        if _ms_last and _ms_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            _mb_is_return = True
                            break
                if _mb_is_return:
                    _is_outer_condition = False"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix4 applied")
else:
    print("FAIL: old_string not found")
