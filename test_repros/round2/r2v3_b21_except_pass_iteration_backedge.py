# round-2 r2v3 specimen (synthetic, minimal) [R2-B106 修复·处理器尾回边按循环入口归属]
# near-miss arm: the try/except IS the last statement of the loop body and the handler
# is empty => its POP_EXCEPT + JUMP_BACKWARD -> loop head is the loop's implicit
# iteration edge and must NOT be emitted as `continue` (source keeps `pass`).
def f(items, w):
    for x in items:
        try:
            w(x)
        except ValueError:
            pass
