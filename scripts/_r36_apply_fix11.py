with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        if len(op_chain) >= 1 and not last_has_nested_ternary:
            last_chain_block = op_chain[-1][0]
            last_instr = last_chain_block.get_last_instruction()
            last_chain_op = op_chain[-1][1]
            if last_instr and last_instr.opname in STRIP_JUMP_OPS:"""

new = """        if len(op_chain) >= 1 and not last_has_nested_ternary:
            last_chain_block = op_chain[-1][0]
            last_instr = last_chain_block.get_last_instruction()
            last_chain_op = op_chain[-1][1]
            # [R36] Skip end-of-loop fall-through when the last chain block was
            # already processed as a chained compare operand. The fall-through
            # block is the chained compare's continuation, not a separate operand.
            _last_cc_expr = self._try_build_chained_compare_in_boolop(last_chain_block, region)
            if _last_cc_expr is not None:
                last_instr = None  # Skip fall-through processing
            if last_instr and last_instr.opname in STRIP_JUMP_OPS:"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix11 applied")
else:
    print("FAIL: old_string not found")
