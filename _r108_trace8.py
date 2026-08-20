"""Check what generate() returns for the function"""
import sys, marshal, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast = gen.generate()

# Check if orelse is in the Try node
for node in ast.get('body', []):
    if isinstance(node, dict) and node.get('type') == 'Try':
        print(f"Try node has orelse: {'orelse' in node}")
        print(f"Try node keys: {list(node.keys())}")
        if 'orelse' in node:
            print(f"orelse: {json.dumps(node['orelse'], default=str)}")
        else:
            print("NO orelse!")
            # Check trailing_returns
            print(f"trailing_returns: {json.dumps(gen._trailing_returns, default=str)}")
