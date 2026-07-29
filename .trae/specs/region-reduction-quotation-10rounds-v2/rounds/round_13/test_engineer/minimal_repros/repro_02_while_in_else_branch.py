"""R13 repro_02: while loop in else-branch of if/elif chain.

Region type: LoopRegion + IfRegion
Violated principle: 2 (unique ownership)
Corresponding function: get_date_and_count (candle_period==8, block 1222)

Defect: The elif condition block's POP_JUMP_FORWARD_IF_FALSE targets the
while loop's condition_block. The backward walk sees p_target == _cb and
absorbs the elif block into the LoopRegion, causing IfRegion to vanish.
"""
def func(x, n):
    if x == 1:
        result = 1
    elif x == 2:
        result = 2
    else:
        n -= 1
        while n > 0:
            if n % 2 == 0:
                n = n // 2
            else:
                n = n - 1
        if n in (0, 1):
            result = 'a'
        else:
            result = 'b'
    return result
