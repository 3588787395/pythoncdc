"""R100 最小复现实例 04: for-else 中链式比较条件"""
d = {1: [1], 2: [2], 3: [3], 4: [4]}
low = 2
high = 4
result = []
for k, v in d.items():
    if low < k <= high:
        result.extend(v)
else:
    result.append('done')
