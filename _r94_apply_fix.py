#!/usr/bin/env python3
"""R94: Apply fix - add POP_TOP handling in _generate_ternary"""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The exact old text to find
old = """                        continue
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                   'STORE_SUBSCR', 'STORE_ATTR'):
                    # Check if the predecessor range contains
                    # MAKE_FUNCTION."""

# Check if it exists
if old in content:
    print("Found target text, applying edit...")
    new = """                        continue
                # [R94 fix] Handle POP_TOP as expression statement terminator
                # in condition_block. When condition_block contains multiple
                # user statements before the ternary condition (e.g. in an
                # except handler: `error_info = get_traceback_message();
                # system_log.error(...); <ternary condition>`), the
                # `system_log.error(...)` call is terminated by POP_TOP.
                # Without this, the call instructions are not extracted as
                # pre_stmts and are silently dropped.
                # 依「每块唯一归属」: POP_TOP-terminated expression belongs
                # to its own Expr statement node, not the TernaryRegion's
                # condition. Per "bottom-up reduction": predecessor Expr is
                # reduced as independent AST node, ternary only owns cond +
                # value + merge blocks.
                # 普遍性: covers any Expr statement (function call, method
                # call, etc.) that appears before the ternary condition in
                # the same basic block.
                if instr.opname == 'POP_TOP' and i > cond_start_idx:
                    _pop_instrs = list(cond_instrs[cond_start_idx:i])
                    if _pop_instrs:
                        _pop_expr = self.expr_reconstructor.reconstruct(_pop_instrs)
                        if _pop_expr is not None:
                            pre_stmts.append({
                                'type': 'Expr',
                                'value': _pop_expr,
                            })
                        else:
                            _pop_stmts = self._build_statements_from_instructions(
                                _pop_instrs)
                            if _pop_stmts:
                                pre_stmts.extend(_pop_stmts)
                    cond_start_idx = i + 1
                    i += 1
                    continue
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                   'STORE_SUBSCR', 'STORE_ATTR'):
                    # Check if the predecessor range contains
                    # MAKE_FUNCTION."""
    
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Edit applied successfully!")
else:
    print("ERROR: Old text not found!")
    # Try to find a shorter match
    short_old = "                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',\n                                   'STORE_SUBSCR', 'STORE_ATTR'):"
    if short_old in content:
        print("Short match found at position:", content.index(short_old))
    else:
        print("Short match not found either")
