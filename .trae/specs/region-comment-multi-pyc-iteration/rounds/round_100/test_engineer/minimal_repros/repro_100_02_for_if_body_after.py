"""R100 最小复现实例 02: for-else 中 if 条件取反（无 continue）

原始代码模式:
    for k, v in d.items():
        if cond:
            body1
        body2
    else:
        after
"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k < 3:
        result.extend(v)
    result.append(k)
else:
    result.append('done')
