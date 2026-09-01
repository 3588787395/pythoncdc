"""R13 repro_05: while loop without break, post-loop code as else_blocks.

Region type: LoopRegion (while without break)
Violated principle: 1 (self-bottom-up reduction) — else_blocks identification
is ambiguous when no breaks exist
Corresponding function: get_date_and_count (LoopRegion@1222 else_blocks=[1314])

Defect: _find_loop_else identifies post-loop code as else_blocks even when
no breaks exist. In Python 3.11+ (no SETUP_LOOP/POP_BLOCK), while-else
without breaks is indistinguishable from while + regular fall-through code.
"""
def func(n):
    while n > 0:
        if n % 2 == 0:
            n = n // 2
        else:
            n = n - 1
    if n == 0:
        return 'done'
    else:
        return 'unknown'
