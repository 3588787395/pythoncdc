#!/usr/bin/env python3
"""R100: Show decompiled source around the problematic area"""
import sys, types, marshal, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.code_generator import CodeGenerator

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if 'api_base' in entry['path'] and entry['path'].endswith('.pyc') and 'IQData' in entry['path']:
        pyc_path = entry['path']
        break

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(orig_code)
ast_result = generate_ast_from_regions(cfg, top_level_code=orig_code)
code_gen = CodeGenerator()
source = code_gen.generate(ast_result)

lines = source.split('\n')
# Find the area around line 21-33 (def get_history_df)
in_func = False
func_start = 0
for i, line in enumerate(lines):
    if 'def get_history_df' in line:
        in_func = True
        func_start = i
        break

if in_func:
    for i in range(func_start + 10, min(func_start + 50, len(lines))):
        print(f"  {i+1:4d}: {lines[i]}")
