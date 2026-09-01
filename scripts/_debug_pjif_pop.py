import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

builder = CFGBuilder()
cfg = builder.build(code)
ra = RegionAnalyzer(cfg)
ra.analyze()
gen = RegionASTGenerator(cfg, ra, code)
result = gen.generate()

def find_func(ast_node, name):
    if isinstance(ast_node, dict):
        if ast_node.get('type') in ('FunctionDef', 'AsyncFunctionDef') and ast_node.get('name') == name:
            return ast_node
        for key in ('body', 'orelse', 'handlers', 'finalbody'):
            body = ast_node.get(key, [])
            if isinstance(body, list):
                for item in body:
                    r = find_func(item, name)
                    if r: return r
    return None

func = find_func(result, 'get_daily_summary')
if func:
    body = func.get('body', [])
    # Search for benchmark_portfolio
    def search_ast(node, target, path=""):
        if isinstance(node, dict):
            if target in str(node):
                print(f"  FOUND at {path}: type={node.get('type','?')}")
                if node.get('type') == 'Expr':
                    print(f"    value: {node.get('value', {}).get('type', '?')}")
                    if node.get('value', {}).get('type') == 'Attribute':
                        print(f"    attr: {node['value'].get('attr', '?')}")
            for key, val in node.items():
                if isinstance(val, list):
                    for i, item in enumerate(val):
                        search_ast(item, target, f"{path}.{key}[{i}]")
                elif isinstance(val, dict):
                    search_ast(val, target, f"{path}.{key}")
    
    search_ast(func, 'benchmark_portfolio')
else:
    print("Function not found!")
