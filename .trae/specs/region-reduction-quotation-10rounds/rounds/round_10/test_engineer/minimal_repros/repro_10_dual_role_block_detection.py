"""R10 repro_10: 双角色块检测（R10 修复点 2 模式）。
缺陷: 前驱 BoolOp 的 merge_block 同时是当前 BoolOp 的 entry 时，未允许继续处理导致 source_end 赋值丢失。
区域类型: BoolOp  违反原则: 1(自底向上归约) + 4(入口引用语义)
"""
def f(a, b):
    x = a[:8] + (a[8:] if len(a[8:]) == 4 else '0000')
    y = b[:8] + (b[8:] if len(b[8:]) == 4 else '1530')
    result = {}
    if x and y:
        result['x'] = x
        result['y'] = y
    return result
