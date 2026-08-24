"""R100 最小复现实例 10: 嵌套 for-else 中 if 条件"""
d = {1: [1, 2], 2: [3, 4]}
result = []
for k, v in d.items():
    for item in v:
        if item > 2:
            result.append(item)
else:
    result.append('done')
