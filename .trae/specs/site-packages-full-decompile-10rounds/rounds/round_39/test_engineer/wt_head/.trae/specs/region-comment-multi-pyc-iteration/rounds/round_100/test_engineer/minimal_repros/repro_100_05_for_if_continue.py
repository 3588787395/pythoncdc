"""R100 最小复现实例 05: for 中 if+continue 模式"""
d = {1: [1], 2: [2], 3: [3]}
result = []
for k, v in d.items():
    if k >= 3:
        continue
    result.extend(v)
