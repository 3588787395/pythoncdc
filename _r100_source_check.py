#!/usr/bin/env python3
"""R100: Check if Region 82's then_blocks are correctly generated"""
import sys, types, marshal, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion
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

def extract(co):
    r = {co.co_name: co}
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

om = extract(orig_code)
co = om['get_history_df']

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(co)

ast_result = generate_ast_from_regions(cfg, top_level_code=co)
code_gen = CodeGenerator()
source = code_gen.generate(ast_result)

# Find the if block around the problematic area
lines = source.split('\n')
in_func = False
func_lines = []
for i, line in enumerate(lines):
    if 'def get_history_df' in line:
        in_func = True
    if in_func:
        func_lines.append((i+1, line))
        if len(func_lines) > 200:
            break

# Find lines with 'if ' or 'elif ' or 'pm_open_market'
print("Lines with if/elif/pm_open in get_history_df:")
for lineno, line in func_lines:
    if 'if ' in line.lower() and ('pm_open' in line or 'now_date' in line or 'frequency' in line or 'real' in line.lower() or 'elif' in line.lower()):
        print(f"  {lineno:4d}: {line.strip()[:80]}")

# Show a window around the first match
first_match = None
for lineno, line in func_lines:
    if 'pm_open' in line:
        first_match = lineno
        break

if first_match:
    start = max(0, first_match - 3)
    end = min(len(func_lines), first_match + 30)
    print(f"\nContext around line {first_match}:")
    for i in range(start, end):
        print(f"  {func_lines[i][0]:4d}: {func_lines[i][1].strip()[:80]}")
