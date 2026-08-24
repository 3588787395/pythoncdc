"""R100 最小复现实例 08: for-else 中 if 条件后跟 continue"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k < 3:
        result.extend(v)
        continue
    result.append('big')
else:
    result.append('done')
