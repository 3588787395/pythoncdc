#!/usr/bin/env python3
"""R92 trace: generate IfRegion@0 and check post-if generation"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find IfRegion@0
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        result = ast_gen._generate_if(r)
        
        # Check if result is a list (with post-if statements)
        if isinstance(result, list):
            print(f"Result: list of {len(result)} items")
            for i, item in enumerate(result):
                t = item.get('type') if isinstance(item, dict) else type(item).__name__
                print(f"  [{i}] type={t}")
        elif isinstance(result, dict):
            t = result.get('type')
            print(f"Result: single {t}")
            if t == 'If':
                body = result.get('body', [])
                orelse = result.get('orelse', [])
                print(f"  body: {len(body)} stmts, last={body[-1].get('type') if body else '?'}")
                if body and body[-1].get('type') == 'Return':
                    val = body[-1].get('value', {})
                    print(f"    return value={val.get('type') if val else None}")
                print(f"  orelse: {len(orelse)} stmts")
        
        # Check if merge_block (2710) was generated
        print(f"\nGenerated blocks: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
        print(f"merge_block 2710 in generated: {2710 in [b.start_offset for b in ast_gen.generated_blocks]}")
        print(f"block 2758 in generated: {2758 in [b.start_offset for b in ast_gen.generated_blocks]}")
        break
