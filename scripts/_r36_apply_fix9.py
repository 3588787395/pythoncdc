with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """            # Check for fall-through block with additional operands (for ALL chain blocks, not just last)
            # 当 chain_block 自身是嵌套 ternary 的 cond_block 时
            # （nested_ternary is not None），其 true/false 分支已纳入 IfExp，
            # 不应再作为「fall-through 块附加操作数」重复求值。否则
            # `x or (a if c else b)` 会误把 ternary 的 true_block (LOAD_NAME a)
            # 当作 `and a` 的额外操作数，输出 `x or ((a if c else b) and a)`。
            # 依「每块唯一归属」：ternary 的 true/false 块归属 TernaryRegion
            # （此处由 nested_ternary 表达），不归属 BoolOpRegion 的操作数链。
            next_chain_block = op_chain[chain_idx + 1][0] if chain_idx + 1 < len(op_chain) else None
            if (nested_ternary is None"""

new = """            # Check for fall-through block with additional operands (for ALL chain blocks, not just last)
            # 当 chain_block 自身是嵌套 ternary 的 cond_block 时
            # （nested_ternary is not None），其 true/false 分支已纳入 IfExp，
            # 不应再作为「fall-through 块附加操作数」重复求值。否则
            # `x or (a if c else b)` 会误把 ternary 的 true_block (LOAD_NAME a)
            # 当作 `and a` 的额外操作数，输出 `x or ((a if c else b) and a)`。
            # 依「每块唯一归属」：ternary 的 true/false 块归属 TernaryRegion
            # （此处由 nested_ternary 表达），不归属 BoolOpRegion 的操作数链。
            # [R36] Also skip when chained_compare_expr was found — the
            # fall-through block is the chained compare's continuation
            # (e.g. the second COMPARE_OP in `a < b < c`), not a separate
            # BoolOp operand. Without this, `return A < x < B or C < x < D`
            # produces `... or C < x < D and D` (extra D from ft block).
            next_chain_block = op_chain[chain_idx + 1][0] if chain_idx + 1 < len(op_chain) else None
            if (nested_ternary is None
                    and chained_compare_expr is None"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix9 applied")
else:
    print("FAIL: old_string not found")
