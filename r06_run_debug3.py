#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from core.cfg import region_ast_generator_debug3 as rag
from core.cfg.cfg_builder import CFGBuilder
import marshal, types

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
codes = {}
for c in code.co_consts:
    if isinstance(c, types.CodeType):
        codes[c.co_name] = c
codes[code.co_name] = code
vc = codes['DataProcessor']
for c in vc.co_consts:
    if isinstance(c, types.CodeType):
        codes[f'DataProcessor.{c.co_name}'] = c
target = codes['DataProcessor.validate_data']
cfg = CFGBuilder().build(target)
gen = rag.RegionASTGenerator(cfg, recursive=True, parent_code=target)
result = gen.generate()
print(f'448: {448 in gen.generated_offsets}, 488: {488 in gen.generated_offsets}')