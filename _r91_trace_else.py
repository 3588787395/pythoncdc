#!/usr/bin/env python3
"""R91 trace else branch generation"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator, generate_ast_from_regions

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

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find the outer IfRegion (entry=108)
outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 108:
        outer_if = r
        break

if outer_if:
    # Generate the entire if region
    print("=== Generating outer IfRegion ===")
    result = ast_gen._generate_if(outer_if)
    if isinstance(result, list):
        print(f"Result: {len(result)} items")
        for i, item in enumerate(result):
            print(f"  [{i}] type={item.get('type') if isinstance(item, dict) else type(item).__name__}")
            if isinstance(item, dict) and item.get('type') == 'If':
                body = item.get('body', [])
                orelse = item.get('orelse', [])
                print(f"    body ({len(body)} stmts):")
                for j, s in enumerate(body):
                    print(f"      [{j}] type={s.get('type')}")
                print(f"    orelse ({len(orelse)} stmts):")
                for j, s in enumerate(orelse):
                    print(f"      [{j}] type={s.get('type')}")
                    if s.get('type') == 'If':
                        sub_body = s.get('body', [])
                        sub_orelse = s.get('orelse', [])
                        print(f"        sub-body ({len(sub_body)} stmts):")
                        for k, ss in enumerate(sub_body):
                            print(f"          [{k}] type={ss.get('type')}")
                        print(f"        sub-orelse ({len(sub_orelse)} stmts):")
                        for k, ss in enumerate(sub_orelse):
                            print(f"          [{k}] type={ss.get('type')}")
    elif isinstance(result, dict):
        print(f"Result type={result.get('type')}")
        if result.get('type') == 'If':
            body = result.get('body', [])
            orelse = result.get('orelse', [])
            print(f"  body ({len(body)} stmts):")
            for j, s in enumerate(body):
                print(f"    [{j}] type={s.get('type')}")
            print(f"  orelse ({len(orelse)} stmts):")
            for j, s in enumerate(orelse):
                print(f"    [{j}] type={s.get('type')}")
                if s.get('type') == 'If':
                    sub_body = s.get('body', [])
                    sub_orelse = s.get('orelse', [])
                    print(f"      sub-body ({len(sub_body)} stmts):")
                    for k, ss in enumerate(sub_body):
                        print(f"        [{k}] type={ss.get('type')}")
                    print(f"      sub-orelse ({len(sub_orelse)} stmts):")
                    for k, ss in enumerate(sub_orelse):
                        print(f"        [{k}] type={ss.get('type')}")
