"""R100 最小复现实例 01: for-else 中 if 条件取反 + for-else 误识别

原始代码模式:
    for k, v in d.items():
        if cond:
            body
    else:
        after

反编译输出:
    for k, v in d.items():
        if not cond:
            body
        continue
    else:
        after

字节码差异: POP_JUMP_FORWARD_IF_FALSE (orig) vs POP_JUMP_FORWARD_IF_TRUE (decomp)
"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k < 3:
        result.extend(v)
else:
    result.append('done')
