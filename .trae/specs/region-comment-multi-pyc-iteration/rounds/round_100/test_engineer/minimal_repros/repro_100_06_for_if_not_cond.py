"""R100 最小复现实例 06: for-else 中 if not 条件"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if not k < 3:
        result.append('big')
    else:
        result.extend(v)
else:
    result.append('done')
