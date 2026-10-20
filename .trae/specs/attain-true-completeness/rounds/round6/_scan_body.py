# -*- coding: utf-8 -*-
import io
import re

p = 'core/cfg/region_ast_generator.py'
lines = io.open(p, encoding='utf-8').read().split('\n')
start = 61620
end = len(lines)
for i in range(start + 1, len(lines)):
    if re.match(r'^    def [a-zA-Z_]', lines[i]):
        end = i
        break
print('body method', start + 1, 'to', end + 1)
for n in range(start, end):
    l = lines[n]
    if "'Assign'" in l or "'Expr'" in l:
        print(n + 1, l.strip()[:170])
