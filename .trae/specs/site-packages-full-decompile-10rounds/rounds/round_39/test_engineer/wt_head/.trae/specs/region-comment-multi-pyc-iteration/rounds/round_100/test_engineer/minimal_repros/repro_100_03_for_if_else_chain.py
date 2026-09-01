"""R100 最小复现实例 03: for-else 中嵌套 if-else"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k < 3:
        result.extend(v)
    else:
        result.append('skip')
else:
    result.append('done')
