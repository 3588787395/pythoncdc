import sys, types, marshal, traceback
sys.path.insert(0, '.')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import ast

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc'

# Load pyc
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find load_from_kwargs
target_code = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'LiveFuturePosition':
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType) and cc.co_name == 'load_from_kwargs':
                target_code = cc
                break

if not target_code:
    print("load_from_kwargs not found")
    sys.exit(1)

print(f"Found load_from_kwargs: {len(target_code.co_code)} bytes")

# Build CFG
try:
    cfg_builder = CFGBuilder()
    func_cfg = cfg_builder.build(target_code)
    print(f"CFG built: {len(func_cfg.blocks)} blocks")
    blocks = func_cfg.blocks if isinstance(func_cfg.blocks, list) else list(func_cfg.blocks.values()) if isinstance(func_cfg.blocks, dict) else []
    for b in blocks:
        if hasattr(b, 'get_last_instruction'):
            last = b.get_last_instruction()
            print(f"  Block @{b.start_offset}: {len(b.instructions)} instrs, last={last.opname if last else 'None'}")
        else:
            print(f"  Block: {b} (type={type(b).__name__})")
except Exception as e:
    print(f"CFG build failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Analyze regions
try:
    analyzer = RegionAnalyzer(func_cfg)
    func_region_list = analyzer.analyze()
    print(f"\nRegion analysis: {len(func_region_list)} regions")
    for r in func_region_list:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}, blocks={len(r.blocks)}")
except Exception as e:
    print(f"Region analysis failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Generate AST
try:
    gen = RegionASTGenerator(func_cfg, analyzer)
    func_ast_result = gen.generate()
    if func_ast_result:
        func_ast = func_ast_result.get('ast') if isinstance(func_ast_result, dict) else func_ast_result
        if func_ast and hasattr(func_ast, 'body'):
            print(f"\nAST generated: {len(func_ast.body)} statements")
            for stmt in func_ast.body:
                print(f"  {type(stmt).__name__}: {ast.dump(stmt)[:100]}")
        else:
            print(f"\nAST result: {type(func_ast_result)} keys={list(func_ast_result.keys()) if isinstance(func_ast_result, dict) else 'N/A'}")
    else:
        print("\nAST generation returned None!")
except Exception as e:
    print(f"AST generation failed: {e}")
    traceback.print_exc()
