"""R13 repro_04: elif condition jumps to while loop condition_block.

Region type: IfRegion + LoopRegion
Violated principle: 2 (unique ownership) — elif block claimed by both
IfRegion and LoopRegion
Corresponding function: get_date_and_count (block 1202 → 1222)

Defect: Block 1202 (elif condition) has POP_JUMP_FORWARD_IF_FALSE -> 1222
(while loop condition_block). The backward walk absorbs 1202 because
p_target == _cb, but 1202's fall-through is 1214 (elif body), not 1222.
True condition-chain predecessors have fall-through == _cb.
"""
def func(a, b, c):
    if a == 0:
        result = 0
    elif b == 1 and c > 0:
        result = 1
    else:
        c -= 1
        while c > 0:
            if c > 10:
                c -= 5
            else:
                c -= 1
        result = c
    return result
