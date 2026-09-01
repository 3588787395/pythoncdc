"""R100 最小复现实例 09: for-else 中 if 条件后跟多个语句"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k < 3:
        result.extend(v)
        result.append(k)
else:
    result.append('done')
