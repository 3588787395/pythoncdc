# round-2 r2v3 specimen (synthetic, minimal) [R2-B106 修复·处理器尾回边按循环入口归属]
# positive arm: except handler tail = POP_EXCEPT + JUMP_BACKWARD -> loop head,
# and the loop body still has pending statements after the try  => explicit continue
def f(items, w):
    for x in items:
        try:
            v = w(x)
        except ValueError:
            continue
        w(v)
