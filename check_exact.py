#!/usr/bin/env python3
with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(7589, 7596):
    print(f'{i+1}: {repr(lines[i])}')