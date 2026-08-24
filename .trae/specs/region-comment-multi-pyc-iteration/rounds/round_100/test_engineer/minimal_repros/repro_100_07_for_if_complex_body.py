"""R100 最小复现实例 07: for-else 中 if 条件后跟复杂 body"""
import re
d = {'a': 'x', 'b': 'y'}
result = []
for k, v in d.items():
    if k == 'a':
        pattern = '(?<![.\\w])\\s*' + re.escape(v) + '\\('
        matches = re.findall(pattern, 'test')
        if len(matches) > 0:
            result.append(v)
else:
    result.append('done')
